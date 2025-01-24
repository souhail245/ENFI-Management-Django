from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import UserManager
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.db import models  # Correction ici : importer models directement de django.db
from django.contrib.auth.models import AbstractUser




class CustomUserManager(UserManager):
    def _create_user(self, email, password, **extra_fields):
        email = self.normalize_email(email)
        user = CustomUser(email=email, **extra_fields)
        user.password = make_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        assert extra_fields["is_staff"]
        assert extra_fields["is_superuser"]
        return self._create_user(email, password, **extra_fields)


class Session(models.Model):
    start_year = models.DateField()
    end_year = models.DateField()

    def __str__(self):
        return "From " + str(self.start_year) + " to " + str(self.end_year)


class CustomUser(AbstractUser):
    USER_TYPE = ((1, "HOD"), (2, "Staff"), (3, "Student"))
    GENDER = [("M", "Male"), ("F", "Female")]
    
    
    username = None  # Removed username, using email instead
    email = models.EmailField(unique=True)
    user_type = models.CharField(default=1, choices=USER_TYPE, max_length=1)
    gender = models.CharField(max_length=1, choices=GENDER)
    profile_pic = models.ImageField()
    address = models.TextField()
    fcm_token = models.TextField(max_length=255, blank=True, null=True, default="")  # For firebase notifications
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []
    objects = CustomUserManager()

    def __str__(self):
        return self.last_name + ", " + self.first_name

    def update_fcm_token(self, token):
        self.fcm_token = token
        self.save()


class Admin(models.Model):
    admin = models.OneToOneField(CustomUser, on_delete=models.CASCADE)



from django.db import models

class Course(models.Model):
    LEVEL_CHOICES = [
        ('3ème année', '3ème année'),
        ('4ème année', '4ème année'),
        ('5ème année', '5ème année'),
    ]

    name = models.CharField(max_length=120, unique=True)  # Le nom du cours, unique pour éviter les doublons
    niveau = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='3ème année')  # Champ pour le niveau avec valeur par défaut
    created_at = models.DateTimeField(auto_now_add=True)  # Date de création
    updated_at = models.DateTimeField(auto_now=True)  # Date de mise à jour

    def __str__(self):
        return f"{self.name} ({self.niveau})"  # Affiche le nom du cours avec le niveau

class Student(models.Model):
    admin = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.DO_NOTHING, null=True, blank=False)
    session = models.ForeignKey(Session, on_delete=models.DO_NOTHING, null=True)
    phone_number = models.CharField(max_length=20,  default="06000007")  # Nouveau champ
    matricule = models.CharField(max_length=14, unique=False, default="5001")  # Nouveau champ
    # Champ Niveau avec des choix
    NIVEAU_CHOICES = [
        ('3eme année', '3ème année'),
        ('4eme année', '4ème année'),
        ('5eme année', '5ème année'),
        ('6eme année', '6ème année'),
                  ]
    niveau = models.CharField(max_length=20, choices=NIVEAU_CHOICES, default='3eme année')
    lieu = models.CharField(max_length=100, null=True, blank=True)  # Lieu de naissance
    dateN = models.DateField(null=True, blank=True)  # Date de naissance

    def __str__(self):
        return self.admin.last_name + ", " + self.admin.first_name


class Staff(models.Model):
    admin = models.OneToOneField(CustomUser, on_delete=models.CASCADE)

    def __str__(self):
        return self.admin.last_name + " " + self.admin.first_name


class Subject(models.Model):
    name = models.CharField(max_length=120)
    staff = models.ForeignKey(Staff,on_delete=models.CASCADE,)
    niveau = models.CharField(
        max_length=20,
        choices=[
            ('3ème année', '3ème année'),
            ('4ème année', '4ème année'),
            ('5ème année', '5ème année'),
             ('6ème année', '6ème année'),
        ],
        default='3ème année'
    )
    volume_horaire_total = models.IntegerField(default=40)  # 30-40 heures
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    heures_ajoutees = models.IntegerField(default=0, null=True, blank=True)
    progression_cours = models.IntegerField(default=0)  # Progression en %
    volume_horaire_restant = models.IntegerField(default=40, null=True, blank=True)  # Initialisé avec le total

    def __str__(self):
        return self.name
    
    
    def save(self, *args, **kwargs):
        # Si c'est un nouveau sujet ou si heures_ajoutees n'est pas défini
        if not self.pk or self.heures_ajoutees is None:
            self.heures_ajoutees = 0
        
        # Si volume_horaire_restant n'est pas défini
        if self.volume_horaire_restant is None:
            self.volume_horaire_restant = self.volume_horaire_total
        
        # Calculer la progression avant de sauvegarder
        if self.volume_horaire_total > 0:
            self.progression_cours = int((self.heures_ajoutees / self.volume_horaire_total) * 100)
        
        # Sauvegarder sans rappeler mettre_a_jour_progression
        super().save(*args, **kwargs)

    def mettre_a_jour_progression(self):
        """Met à jour la progression en fonction du volume horaire total"""
        if self.volume_horaire_total > 0:
            # Compter toutes les séances pour cette matière
            nb_seances = EmploiTemps.objects.filter(
                matiere=self,
                type_evenement='COURS'
            ).count()
            
            # Calculer les heures totales (2h par séance)
            self.heures_ajoutees = nb_seances * 2
            
            # Calculer la progression en pourcentage
            self.progression_cours = min(
                int((self.heures_ajoutees / self.volume_horaire_total) * 100),
                100
            )
            
            # Mettre à jour le volume horaire restant
            self.volume_horaire_restant = max(
                self.volume_horaire_total - self.heures_ajoutees,
                0
            )
            
            # Mise à jour en base sans déclencher de nouvelle sauvegarde
            Subject.objects.filter(pk=self.pk).update(
                heures_ajoutees=self.heures_ajoutees,
                progression_cours=self.progression_cours,
                volume_horaire_restant=self.volume_horaire_restant
            )


class Attendance(models.Model):
    session = models.ForeignKey(Session, on_delete=models.DO_NOTHING)
    subject = models.ForeignKey(Subject, on_delete=models.DO_NOTHING)
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class AttendanceReport(models.Model):
    student = models.ForeignKey(Student, on_delete=models.DO_NOTHING)
    attendance = models.ForeignKey(Attendance, on_delete=models.CASCADE)
    status = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class LeaveReportStudent(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    date = models.CharField(max_length=60)
    message = models.TextField()
    status = models.SmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class LeaveReportStaff(models.Model):
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE)
    date = models.CharField(max_length=60)
    message = models.TextField()
    status = models.SmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)


class FeedbackStudent(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    feedback = models.TextField()
    reply = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)


class FeedbackStaff(models.Model):
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE)
    feedback = models.TextField()
    reply = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)


class NotificationStaff(models.Model):
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE)
    message = models.TextField()
    # Modifier le chemin d'upload pour éviter le doublon de 'media'
    file = models.FileField(upload_to='staff_notifications', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification pour {self.staff.admin.email}"


class NotificationStudent(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    message = models.TextField()
    file = models.FileField(upload_to='notifications/', null=True, blank=True)
    status = models.CharField(
        max_length=20, 
        default='pending',
        choices=[
            ('pending', 'En attente'),
            ('success', 'Envoyée'),
            ('failed', 'Échouée')
        ]
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification pour {self.student.admin.email} - {self.status}"


class StudentResult(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    test = models.FloatField(default=0)
    exam = models.FloatField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)

class Absence(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="absences")
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="absences")
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name="absences")
    date = models.DateField()
    time_from = models.TimeField()
    time_to = models.TimeField()
    reason = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.student.matricule} - {self.subject.name} - {self.date}"


@receiver(post_save, sender=CustomUser)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        if instance.user_type == 1:
            Admin.objects.create(admin=instance)
        if instance.user_type == 2:
            Staff.objects.create(admin=instance)
        if instance.user_type == 3:
            Student.objects.create(admin=instance)


@receiver(post_save, sender=CustomUser)
def save_user_profile(sender, instance, **kwargs):
    if instance.user_type == 1:
        instance.admin.save()
    if instance.user_type == 2:
        instance.staff.save()
    if instance.user_type == 3:
        instance.student.save()




class SuiviCours(models.Model):
    matiere = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='suivis')
    total_heures = models.IntegerField(default=0)  # Total d'heures prévues pour la matière
    heures_effectuees = models.IntegerField(default=0)  # Heures déjà effectuées

    def progression(self):
        if self.total_heures > 0:
            return round((self.heures_effectuees / self.total_heures) * 100, 2)
        return 0

    def __str__(self):
        return f"{self.matiere.name} : {self.heures_effectuees}/{self.total_heures} heures"


from datetime import date 
class EmploiTemps(models.Model):

    HORAIRES_CHOICES = [
        ('08:00-10:00', '08:00-10:00'),
        ('10:00-12:00', '10:00-12:00'),
        ('14:00-16:00', '14:00-16:00'),
        ('16:00-18:00', '16:00-18:00'),
        ('08:00-12:00', '08:00-12:00'),
        ('14:00-18:00', '14:00-18:00'),
    ]

    JOUR_CHOICES = [
        ('Lundi', 'Lundi'),
        ('Mardi', 'Mardi'),
        ('Mercredi', 'Mercredi'),
        ('Jeudi', 'Jeudi'),
        ('Vendredi', 'Vendredi'),
        ('Samedi', 'Samedi'),
    ]
    jour = models.CharField(max_length=10, choices=JOUR_CHOICES, default='Lundi')
    # Supprimer l'ancien champ niveau qui référence Student
    # niveau = models.ForeignKey(Student, on_delete=models.CASCADE)
    
    niveau = models.CharField(
        max_length=20,
        choices=[
            ('3ème année', '3ème année'),
            ('4ème année', '4ème année'),
            ('5ème année', '5ème année'),
        ],
        default='3ème année'
    )
    date = models.DateField(default=date.today) 
    jour = models.CharField(max_length=10, choices=JOUR_CHOICES, default='Lundi')  # Ajout d'une valeur par défaut
    horaire = models.CharField(max_length=20, choices=HORAIRES_CHOICES, default='08:00-10:00')  # Ajout d'une valeur par défaut

    matiere = models.ForeignKey(
        Subject, 
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    professeur = models.ForeignKey(
        Staff, 
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    
    progression = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Décrivez la progression, par exemple '50% terminé' ou 'Chapitre 3 terminé'."
    )

    TYPE_CHOICES = [
        ('COURS', 'Cours'),
        ('EXAMEN_PARTIEL', 'Examen Partiel'),
        ('EXAMEN_FINAL', 'Examen Final'),
        ('JOUR_FERIE', 'Jour Férié'),
        ('VACANCES', 'Vacances'),
    ]
    
    type_evenement = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default='COURS'
    )
    
    titre_evenement = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Nom du jour férié ou type de vacances"
    )
    
    date_debut = models.DateField(null=True, blank=True)
    date_fin = models.DateField(null=True, blank=True)
    numero_seance = models.IntegerField(default=0)  # Ajouter ce champ
    
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        if is_new and self.type_evenement == 'COURS' and self.matiere:
            # Calculer le nombre de séances jusqu'à cette date et horaire
            seances_precedentes = EmploiTemps.objects.filter(
                matiere=self.matiere,
                type_evenement='COURS',
                date__lt=self.date
            ).count()
            
            seances_meme_jour = EmploiTemps.objects.filter(
                matiere=self.matiere,
                type_evenement='COURS',
                date=self.date,
                horaire__lt=self.horaire
            ).count()
            
            self.numero_seance = seances_precedentes + seances_meme_jour + 1
            
            # Calculer la progression
            progression = min(int((self.numero_seance * 2 / self.matiere.volume_horaire_total) * 100), 100)
            
            # Mettre à jour cette séance
            EmploiTemps.objects.filter(pk=self.pk).update(
                numero_seance=self.numero_seance,
                progression=str(progression)
            )
            
            # Mettre à jour la matière
            self.matiere.heures_ajoutees = self.numero_seance * 2
            self.matiere.volume_horaire_restant = max(
                self.matiere.volume_horaire_total - self.matiere.heures_ajoutees,
                0
            )
            self.matiere.progression_cours = progression
            
            Subject.objects.filter(pk=self.matiere.pk).update(
                heures_ajoutees=self.matiere.heures_ajoutees,
                progression_cours=self.matiere.progression_cours,
                volume_horaire_restant=self.matiere.volume_horaire_restant
            )

    def get_progression_percentage(self):
        """Retourne la progression en pourcentage"""
        try:
            return int(self.progression or 0)
        except ValueError:
            return 0

    def __str__(self):
        return f"{self.niveau} - {self.date} - {self.horaire} : {self.matiere}"