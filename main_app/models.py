from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import UserManager
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.db import models
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
    course = models.ForeignKey(Course, on_delete=models.DO_NOTHING, null=True, blank=False)
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
        ],
        default='3ème année'
    )
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


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
    updated_at = models.DateTimeField(auto_now=True)

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
<<<<<<< HEAD
    JOUR_CHOICES = [
        ('Lundi', 'Lundi'),
        ('Mardi', 'Mardi'),
        ('Mercredi', 'Mercredi'),
        ('Jeudi', 'Jeudi'),
        ('Vendredi', 'Vendredi'),
        ('Samedi', 'Samedi'),
    ]
    jour = models.CharField(max_length=10, choices=JOUR_CHOICES, default='Lundi')
    # Remplacez `niveau` pour qu'il fasse référence à l'objet `Student`
    niveau = models.ForeignKey(Student, on_delete=models.CASCADE)  # Référence au modèle Student
    date = models.DateField(default=date.today) 
    horaire = models.CharField(max_length=20, choices=HORAIRES_CHOICES, default='08:00-10:00')
=======

    niveau = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='emplois_temps')
    jour = models.CharField(max_length=10, choices=JOUR_CHOICES, default='Lundi')  # Ajout d'une valeur par défaut
    horaire = models.CharField(max_length=20, choices=HORAIRES_CHOICES, default='08:00-10:00')  # Ajout d'une valeur par défaut
>>>>>>> cbf02f3ea2a3b2416add0db9201ae1083c676d05
    matiere = models.ForeignKey(Subject, on_delete=models.CASCADE)
    professeur = models.ForeignKey(Staff, on_delete=models.CASCADE)
    progression = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Décrivez la progression, par exemple '50% terminé' ou 'Chapitre 3 terminé'."
    )

    def __str__(self):
        return f"{self.niveau} - {self.date} - {self.horaire} : {self.matiere}"