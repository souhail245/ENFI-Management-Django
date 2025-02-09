from email import errors
import json
import requests
from django.contrib import messages
from django.core.files.storage import FileSystemStorage, default_storage
import os
from django.http import HttpResponse, JsonResponse
from django.shortcuts import (HttpResponse, HttpResponseRedirect,
                              get_object_or_404, redirect, render)
from django.templatetags.static import static
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import UpdateView
from django.conf import settings
from django.http import HttpResponse
import xlsxwriter
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle

from .forms import *
from .models import *

# Ajouter ces imports en haut du fichier
from django.db.models import F, Sum, ExpressionWrapper, DurationField
from datetime import datetime, timedelta

# manager abscence

from django.http import JsonResponse

def add_absence(request):
    if request.method == 'POST':
        form = AbsenceForm(request.POST)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'errors': form.errors})
    else:
        form = AbsenceForm()
    return render(request, 'hod_template/add_absence_template.html', {'form': form})

# Vue pour récupérer les détails de l'étudiant par matricule
def get_student_details(request):
    matricule = request.GET.get('matricule', None)
    if matricule:
        try:
            student = Student.objects.get(matricule=matricule)
            return JsonResponse({
                'success': True,
                'student_id': student.id,
                'first_name': student.admin.first_name,
                'last_name': student.admin.last_name,
                'niveau': student.niveau,
            })
        except Student.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Étudiant introuvable.'})
    return JsonResponse({'success': False, 'error': 'Matricule non fourni.'})


# voir l'absence + le filtrage

def view_absences(request):
    # Query de base avec select_related pour optimiser les performances
    absences = Absence.objects.select_related('student', 'subject')

    # Récupération des paramètres de filtrage
    matricule = request.GET.get('matricule')
    date_debut = request.GET.get('date_debut')
    date_fin = request.GET.get('date_fin')
    niveau = request.GET.get('niveau')

    # Application des filtres
    if (matricule):
        absences = absences.filter(student__matricule__icontains=matricule)
    
    if (date_debut):
        absences = absences.filter(date__gte=date_debut)
    
        absences = absences.filter(date__lte=date_fin)
    
    if (niveau):
        absences = absences.filter(student__niveau=niveau)

    # Récupération de la liste des niveaux pour le formulaire
    niveaux = Absence.objects.select_related('student').values_list(
        'student__niveau', flat=True).distinct()

    context = {
        'absences': absences,
        'niveaux': niveaux,
        'page_title': 'Liste des Absences'
    }

    print("Absences filtrées :", absences)  # Garde le print pour debug

    return render(request, 'hod_template/view_absences.html', context)

# export resultats des absences :


def export_absences_excel(request):
    # Récupérer les absences filtrées
    absences = Absence.objects.select_related('student', 'subject')
    
    # Appliquer les mêmes filtres que dans la vue principale
    matricule = request.GET.get('matricule')
    date_debut = request.GET.get('date_debut')
    date_fin = request.GET.get('date_fin')
    niveau = request.GET.get('niveau')

    if (matricule):
        absences = absences.filter(student__matricule__icontains=matricule)
    if (date_debut):
        absences = absences.filter(date__gte=date_debut)
    if (date_fin):
        absences = absences.filter(date__lte=date_fin)
    if (niveau):
        absences = absences.filter(student__niveau=niveau)

    # Créer le fichier Excel en mémoire
    output = BytesIO()
    workbook = xlsxwriter.Workbook(output)
    worksheet = workbook.add_worksheet()

    # Entêtes
    headers = ['#', 'Matricule', "Nom de l'Étudiant", 'Niveau', 'Matière', 
              'Date', 'Heure début', 'Heure fin', 'Raison']
    for col, header in enumerate(headers):
        worksheet.write(0, col, header)

    # Données
    for row, absence in enumerate(absences, 1):
        worksheet.write(row, 0, row)
        worksheet.write(row, 1, absence.student.matricule)
        worksheet.write(row, 2, f"{absence.student.admin.last_name}, {absence.student.admin.first_name}")
        worksheet.write(row, 3, absence.student.niveau)
        worksheet.write(row, 4, absence.subject.name)
        worksheet.write(row, 5, absence.date.strftime('%Y-%m-%d'))
        worksheet.write(row, 6, absence.time_from.strftime('%H:%M'))
        worksheet.write(row, 7, absence.time_to.strftime('%H:%M'))
        worksheet.write(row, 8, absence.reason)

    workbook.close()
    output.seek(0)

    response = HttpResponse(output.read(),
                          content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=absences.xlsx'
    return response

def export_absences_pdf(request):
    # Récupérer les absences filtrées avec les mêmes filtres
    absences = Absence.objects.select_related('student', 'subject')
    
    # Appliquer les filtres
    matricule = request.GET.get('matricule')
    date_debut = request.GET.get('date_debut')
    date_fin = request.GET.get('date_fin')
    niveau = request.GET.get('niveau')

    if (matricule):
        absences = absences.filter(student__matricule__icontains=matricule)
    if (date_debut):
        absences = absences.filter(date__gte=date_debut)
    if (date_fin):
        absences = absences.filter(date__lte=date_fin)
    if (niveau):
        absences = absences.filter(student__niveau=niveau)

    # Créer le PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []

    # Préparer les données
    data = [['#', 'Matricule', "Nom de l'Étudiant", 'Niveau', 'Matière', 
             'Date', 'Heure début', 'Heure fin', 'Raison']]
    
    for i, absence in enumerate(absences, 1):
        data.append([
            i,
            absence.student.matricule,
            f"{absence.student.admin.last_name}, {absence.student.admin.first_name}",
            absence.student.niveau,
            absence.subject.name,
            absence.date.strftime('%Y-%m-%d'),
            absence.time_from.strftime('%H:%M'),
            absence.time_to.strftime('%H:%M'),
            absence.reason
        ])

    # Créer le tableau
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0,  1), (-1, -1), colors.white),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    elements.append(table)
    doc.build(elements)
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=absences.pdf'
    response.write(buffer.getvalue())
    return response







# export pdf excel
import xlwt
from django.http import HttpResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib.units import inch

def export_students_excel(request):
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename="students_list.xls"'

    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet('Students')
    
    # Styles
    header_style = xlwt.easyxf('font: bold on; pattern: pattern solid, fore_colour gray25;')
    
    # En-têtes
    row_num = 0
    columns = [
        '#',
        'Full Name',
        'Niveau',
        'Matricule',
        'Gender',
        'Numéro de téléphone'
    ]
    
    for col_num, column_title in enumerate(columns):
        ws.write(row_num, col_num, column_title, header_style)

    # Récupérer le niveau sélectionné
    selected_niveau = request.GET.get('niveau')
    
    # Query de base
    students = CustomUser.objects.filter(user_type=3).select_related('student')
    
    # Appliquer le filtre si un niveau est sélectionné
    if (selected_niveau):
        students = students.filter(student__niveau=selected_niveau)

    for idx, student in enumerate(students, 1):
        row_num += 1
        row = [
            idx,
            f"{student.last_name}, {student.first_name}",
            student.student.niveau if hasattr(student, 'student') else "",
            student.student.matricule if hasattr(student, 'student') else "",
            student.gender,
            student.student.phone_number if hasattr(student, 'student') else "Not provided"
        ]
        
        for col_num, cell_value in enumerate(row):
            ws.write(row_num, col_num, str(cell_value))

    wb.save(response)
    return response


def export_students_pdf(request):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="students_list.pdf"'

    doc = SimpleDocTemplate(response, pagesize=landscape(letter))
    elements = []

    headers = [
        '#',
        'Full Name',
        'Niveau',
        'Matricule',
        'Gender',
        'Numéro de téléphone'
    ]
    
    data = [headers]
    
    # Récupérer le niveau sélectionné
    selected_niveau = request.GET.get('niveau')
    
    # Query de base
    students = CustomUser.objects.filter(user_type=3).select_related('student')
    
    # Appliquer le filtre si un niveau est sélectionné
    if (selected_niveau):
        students = students.filter(student__niveau=selected_niveau)

    for idx, student in enumerate(students, 1):
        data.append([
            idx,
            f"{student.last_name}, {student.first_name}",
            student.student.niveau if hasattr(student, 'student') else "",
            student.student.matricule if hasattr(student, 'student') else "",
            student.gender,
            student.student.phone_number if hasattr(student, 'student') else "Not provided"
        ])

    col_widths = [0.5*inch, 2*inch, 1*inch, 1.5*inch, 1*inch, 1.5*inch]
    table = Table(data, colWidths=col_widths)
    
    # Le reste du style de la table reste inchangé
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    elements.append(table)
    doc.build(elements)
    return response
    
    # home graphes 

def admin_home(request):
    total_staff = Staff.objects.all().count()
    total_students = Student.objects.all().count()
    subjects = Subject.objects.all()  # Récupérer toutes les matières
    total_subject = subjects.count()
    total_course = Course.objects.all().count()
    attendance_list = Attendance.objects.filter(subject__in=subjects)
    total_attendance = attendance_list.count()
      # Récupérer le niveau/promotion sélectionné (par défaut 3ème année)
    selected_niveau = request.GET.get('niveau', '3ème année')
    today = datetime.now().date()

    subject_list = []
    course_progress = []

    for subject in subjects:
        subject_list.append(subject.name[:15])  # Raccourcir les noms de matières
        
        # Calculer uniquement les séances qui ont déjà eu lieu
        seances_realisees = EmploiTemps.objects.filter(
            matiere=subject,
            type_evenement='COURS',
            date__lte=today
        ).count()
        
        # Calculer la progression
        if subject.volume_horaire_total > 0:
            heures_realisees = seances_realisees * 2
            progression = min(int((heures_realisees / subject.volume_horaire_total) * 100), 100)
        else:
            progression = 0
            
        course_progress.append(progression)

    # Récupérer tous les niveaux disponibles
    niveaux_disponibles = Subject.objects.values_list('niveau', flat=True).distinct()
    subject_list = []
    attendance_list = []

    # Liste pour stocker la progression des cours
    course_progress = []

    for subject in subjects:
        attendance_count = Attendance.objects.filter(subject=subject).count()  # Nombre de présences pour chaque matière
        subject_list.append(subject.name[:7])  # Prendre les 7 premiers caractères du nom de la matière
        attendance_list.append(attendance_count)  # Ajouter le nombre de présences à la liste
        
        # Récupérer la progression du cours pour chaque matière
        progression = subject.progression_cours if subject.progression_cours is not None else 0
        course_progress.append(progression)  # Ajouter la progression à la liste

    # Total des matières et des étudiants dans chaque cours
    course_all = Course.objects.all()
    course_name_list = []
    subject_count_list = []
    student_count_list_in_course = []

    for course in course_all:
        subjects_count = Subject.objects.filter(course_id=course.id).count()  # Nombre de matières pour chaque cours
        students_count = Student.objects.filter(course_id=course.id).count()  # Nombre d'étudiants dans chaque cours
        course_name_list.append(course.name)
        subject_count_list.append(subjects_count)
        student_count_list_in_course.append(students_count)

    # Pour les étudiants (présence et absence)
    student_attendance_present_list = []
    student_attendance_leave_list = []
    student_name_list = []

    students = Student.objects.all()
    for student in students:
        attendance = AttendanceReport.objects.filter(student_id=student.id, status=True).count()  # Présences de l'étudiant
        absent = AttendanceReport.objects.filter(student_id=student.id, status=False).count()  # Absences
        leave = LeaveReportStudent.objects.filter(student_id=student.id, status=1).count()  # Congés
        student_attendance_present_list.append(attendance)
        student_attendance_leave_list.append(leave + absent)
        student_name_list.append(student.admin.first_name)  # Prénom de l'étudiant

    # Combinez les listes de matières et de progression des cours
    course_progress = list(zip(subject_list, course_progress))

    # Passer les données au template
    context = {
        'page_title': "Administrative Dashboard",
        'total_students': total_students,
        'total_staff': total_staff,
        'total_course': total_course,
        'total_subject': total_subject,
        'subject_list': subject_list,
        'attendance_list': attendance_list,
        'student_attendance_present_list': student_attendance_present_list,
        'student_attendance_leave_list': student_attendance_leave_list,
        "student_name_list": student_name_list,
        "student_count_list_in_course": student_count_list_in_course,
        "course_name_list": course_name_list,
        "course_progress": course_progress,  # Nouvelle clé ajoutée
        'niveaux_disponibles': list(niveaux_disponibles),
        'selected_niveau': selected_niveau,
    
    }

    return render(request, 'hod_template/home_content.html', context)

def get_progression_data(request):
    niveau = request.GET.get('niveau', '3ème année')
    today = datetime.now().date()
    
    # Récupérer toutes les matières du niveau sélectionné
    subjects = Subject.objects.filter(niveau=niveau)
    
    subject_list = []
    course_progress = []
    
    for subject in subjects:
        subject_list.append(subject.name[:15])
        
        # Calculer uniquement les séances qui ont déjà eu lieu
        seances_realisees = EmploiTemps.objects.filter(
            matiere=subject,
            type_evenement='COURS',
            date__lte=today  # Seulement les séances jusqu'à aujourd'hui
        ).count()
        
        # Calculer la progression
        if subject.volume_horaire_total > 0:
            heures_realisees = seances_realisees * 2  # 2 heures par séance
            progression = min(int((heures_realisees / subject.volume_horaire_total) * 100), 100)
        else:
            progression = 0
            
        course_progress.append(progression)
    
    return JsonResponse({
        'subject_list': subject_list,
        'course_progress': course_progress,
        'total_subjects': len(subject_list)
    })

def add_staff(request):
    form = StaffForm(request.POST or None, request.FILES or None)
    context = {'form': form, 'page_title': 'Add Staff'}
    if request.method == 'POST':
        if form.is_valid():
            first_name = form.cleaned_data.get('first_name')
            last_name = form.cleaned_data.get('last_name')
            address = form.cleaned_data.get('address')
            email = form.cleaned_data.get('email')
            gender = form.cleaned_data.get('gender')
            password = form.cleaned_data.get('password')
            course = form.cleaned_data.get('course')
            passport = request.FILES.get('profile_pic')
            fs = FileSystemStorage()
            filename = fs.save(passport.name, passport)
            passport_url = fs.url(filename)
            try:
                user = CustomUser.objects.create_user(
                    email=email, password=password, user_type=2, first_name=first_name, last_name=last_name, profile_pic=passport_url)
                user.gender = gender
                user.address = address
                user.staff.course = course
                user.save()
                messages.success(request, "Successfully Added")
                return redirect(reverse('add_staff'))

            except Exception as e:
                messages.error(request, "Could Not Add " + str(e))
        else:
            messages.error(request, "Please fulfil all requirements")

    return render(request, 'hod_template/add_staff_template.html', context)


def add_student(request):
    student_form = StudentForm(request.POST or None, request.FILES or None)
    context = {'form': student_form, 'page_title': 'Add Student'}
    if request.method == 'POST':
        if student_form.is_valid():
            first_name = student_form.cleaned_data.get('first_name')
            last_name = student_form.cleaned_data.get('last_name')
            address = student_form.cleaned_data.get('address')
            email = student_form.cleaned_data.get('email') 
            gender = student_form.cleaned_data.get('gender')
            phone_number = student_form.cleaned_data.get('phone_number')
            password = student_form.cleaned_data.get('password')
            lieu = student_form.cleaned_data.get('lieu')
            dateN = student_form.cleaned_data.get('dateN')
            niveau = student_form.cleaned_data.get('niveau')
            matricule = student_form.cleaned_data.get('matricule')
            passport = request.FILES['profile_pic']
            fs = FileSystemStorage()
            filename = fs.save(passport.name, passport)
            passport_url = fs.url(filename)
            try:
                user = CustomUser.objects.create_user(
                    email=email, password=password, user_type=3, first_name=first_name, last_name=last_name, profile_pic=passport_url)
                user.gender = gender
                user.address = address   
                user.student.matricule = matricule
                user.student.phone_number = phone_number
                user.student.niveau = niveau
                user.student.lieu = lieu
                user.student.dateN = dateN
                user.save()
                
                messages.success(request, "Successfully Added")
                return redirect(reverse('add_student'))
            except Exception as e:
                messages.error(request, "Could Not Add: " + str(e))
        else:
            messages.error(request, "baa3 Else")
    return render(request, 'hod_template/add_student_template.html', context)


def add_course(request):
    form = CourseForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            try:
                form.save()  # Sauvegarde l'objet Course directement
                messages.success(request, "Cours ajouté avec succès.")
                return redirect('manage_course')  # Redirige vers la page de gestion des cours
            except Exception as e:
                messages.error(request, f"Erreur lors de l'ajout du cours : {str(e)}")
        else:
            messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
    
    context = {
        'form': form,
        'page_title': 'Ajouter un Cours'
    }
    return render(request, 'hod_template/add_course_template.html', context)

def add_subject(request):
    form = SubjectForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            try:
                # Utiliser directement form.save() au lieu de créer manuellement
                subject = form.save()
                messages.success(request, "Matière ajoutée avec succès")
                return redirect('add_subject')
            except Exception as e:
                messages.error(request, f"Erreur lors de l'ajout : {str(e)}")
    context = {'form': form, 'page_title': 'Add Subject'}
    return render(request, 'hod_template/add_subject_template.html', context)


from django.db.models import Q

def manage_staff(request):
    search_query = request.GET.get('search', '')
    allStaff = CustomUser.objects.filter(user_type=2)

    if search_query:
        allStaff = allStaff.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(staff__subject__name__icontains=search_query)
        ).distinct()

    context = {
        'allStaff': allStaff,
        'page_title': 'Manage Staff',
        'search_query': search_query
    }
    return render(request, "hod_template/manage_staff.html", context)


import csv
from django.shortcuts import render
from .models import Student, CustomUser, Course, Session
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.db import transaction
from django.core.exceptions import ValidationError


def manage_student(request):
    # Récupérer tous les niveaux uniques
    niveaux = CustomUser.objects.filter(user_type=3).select_related('student').values_list('student__niveau', flat=True).distinct()
    
    # Récupérer le niveau sélectionné
    selected_niveau = request.GET.get('niveau')
    
    # Query de base
    students = CustomUser.objects.filter(user_type=3).select_related('student')
    
    # Appliquer le filtre si un niveau est sélectionné
    if (selected_niveau):
        students = students.filter(student__niveau=selected_niveau)

    if request.method == 'POST' and request.FILES.get('csv_file'):
        csv_file = request.FILES['csv_file']

        if not csv_file.name.endswith('.csv'):
            messages.error(request, 'File is not a CSV file')
            return HttpResponseRedirect(request.path_info)

        try:
           
            decoded_file = csv_file.read().decode('iso-8859-1').splitlines() # spécifier l'encodage ici
            reader = csv.DictReader(decoded_file)
        
            with transaction.atomic():
                
                for row in reader:
                   # Récupérer ou créer l'utilisateur (CustomUser)
                    user = CustomUser.objects.create(
                                                first_name=row['first_name'].strip(),
                                                last_name=row['last_name'].strip(),
                                                email=row['email'].strip(),
                                                password=row['password'].strip(),
                                                user_type="3"
                    )
                    # Créer l'objet Student
                    try:
                        Student.objects.create(
                            admin=user,
                            phone_number=row['phone_number'],
                            matricule=row['matricule'],
                            niveau=row['niveau'],
                            lieu=row.get('lieu',None), #permettre d'avoir un champ lieu vide
                            dateN=row.get('dateN',None), #permettre d'avoir un champ dateN vide
                            course=None,  # Mettre course à None
                            session=None,   # Mettre session à None
                        )
                    except ValidationError as e:
                        messages.error(request, f"Erreur de validation lors de la création de l'étudiant {row['first_name']} {row['last_name']}: {e}")
                        raise # la transaction atomique annulera les changement de la DB si une erreur est levée
            messages.success(request, 'Students imported successfully')
        except UnicodeDecodeError as e: # capture de l'erreur d'encodage
           messages.error(request, f"UnicodeDecodeError lors de la lecture du fichier : {str(e)}. Veuillez vous assurer que l'encodage est correct.")
           return HttpResponseRedirect(request.path_info) # redirection avant la fin de la transaction en cas d'erreur
        
        except Exception as e:
           messages.error(request, f"Error importing students: {str(e)}")
           return HttpResponseRedirect(request.path_info)
        return HttpResponseRedirect(request.path_info)

    context = {
        'students': students,
        'page_title': 'Manage Students',
        'niveaux': niveaux,
        'selected_niveau': selected_niveau
    }
    return render(request, "hod_template/manage_student.html", context)
    

def manage_course(request):
    # Récupérer tous les cours
    courses = Course.objects.all()

    # Regrouper les cours par niveau
    niveaux = Course._meta.get_field('niveau').choices  # Récupérer les choix de niveau
    cours_par_niveau = {}

    for niveau in niveaux:
        cours = Course.objects.filter(niveau=niveau[0])  # Filtrer les cours par niveau
        cours_par_niveau[niveau[1]] = cours  # Stocker les cours dans un dictionnaire

    context = {
        'cours_par_niveau': cours_par_niveau,  # Passer les cours groupés par niveau
        'page_title': 'Gérer les Cours'
    }
    return render(request, "hod_template/manage_course.html", context)


def manage_subject(request):
    selected_niveau = request.GET.get('niveau')
    
    # Récupérer les choix de niveau pour le select
    niveaux = Subject._meta.get_field('niveau').choices
    
    # Récupérer les sujets
    subjects = Subject.objects.select_related('staff__admin')
    
    # Filtrer par niveau si sélectionné
    if selected_niveau:
        subjects = subjects.filter(niveau=selected_niveau)
    
    context = {
        'sujets': subjects,
        'niveaux': niveaux,
        'selected_niveau': selected_niveau,
        'page_title': 'Gérer les Matières'
    }
    
    return render(request, "hod_template/manage_subject.html", context)

def edit_staff(request, staff_id):
    staff = get_object_or_404(Staff, id=staff_id)
    form = StaffForm(request.POST or None, instance=staff)
    context = {
        'form': form,
        'staff_id': staff_id,
        'page_title': 'Edit Staff'
    }
    if request.method == 'POST':
        if form.is_valid():
            first_name = form.cleaned_data.get('first_name')
            last_name = form.cleaned_data.get('last_name')
            address = form.cleaned_data.get('address')
            username = form.cleaned_data.get('username')
            email = form.cleaned_data.get('email')
            gender = form.cleaned_data.get('gender')
            password = form.cleaned_data.get('password') or None
            course = form.cleaned_data.get('course')
            passport = request.FILES.get('profile_pic') or None
            try:
                user = CustomUser.objects.get(id=staff.admin.id)
                user.username = username
                user.email = email
                if password != None:
                    user.set_password(password)
                if passport != None:
                    fs = FileSystemStorage()
                    filename = fs.save(passport.name, passport)
                    passport_url = fs.url(filename)
                    user.profile_pic = passport_url
                user.first_name = first_name
                user.last_name = last_name
                user.gender = gender
                user.address = address
                staff.course = course
                user.save()
                staff.save()
                messages.success(request, "Successfully Updated")
                return redirect(reverse('edit_staff', args=[staff_id]))
            except Exception as e:
                messages.error(request, "Could Not Update " + str(e))
        else:
            messages.error(request, "Please fil form properly")
    else:
        user = CustomUser.objects.get(id=staff_id)
        staff = Staff.objects.get(id=user.id)
        return render(request, "hod_template/edit_staff_template.html", context)


def edit_student(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    form = StudentForm(request.POST or None, instance=student)
    context = {
        'form': form,
        'student_id': student_id,
        'page_title': 'Edit Student'
    }
    if request.method == 'POST':
        if form.is_valid():
            first_name = form.cleaned_data.get('first_name')
            last_name = form.cleaned_data.get('last_name')
            address = form.cleaned_data.get('address')
            username = form.cleaned_data.get('username')
            niveau = form.cleaned_data.get('niveau')
            matricule = form.cleaned_data.get('matricule')
            email = form.cleaned_data.get('email')    
            gender = form.cleaned_data.get('gender')   
            phone_number = form.cleaned_data.get('phone_number')
            password = form.cleaned_data.get('password') or None
        
            passport = request.FILES.get('profile_pic') or None
            try:
                user = CustomUser.objects.get(id=student.admin.id)
                if passport != None:
                    fs = FileSystemStorage()
                    filename = fs.save(passport.name, passport)
                    passport_url = fs.url(filename)
                    user.profile_pic = passport_url
                user.username = username
                user.email = email
                if password != None:  
                    user.set_password(password)
                user.first_name = first_name
                user.last_name = last_name
                user.gender = gender
                user.address = address
                student.niveau = niveau
                student.matricule = matricule
                student.phone_number = phone_number
                user.save()
                student.save()
                messages.success(request, "Successfully Updated")
                return redirect(reverse('edit_student', args=[student_id]))
            except Exception as e:
                messages.error(request, "Could Not Update " + str(e))
        else:
            messages.error(request, "Please Fill Form Properly!")
    else:
        return render(request, "hod_template/edit_student_template.html", context)


def edit_course(request, course_id):
    instance = get_object_or_404(Course, id=course_id)
    form = CourseForm(request.POST or None, instance=instance)
    context = {
        'form': form,
        'course_id': course_id,
        'page_title': 'Edit Course'
    }
    if request.method == 'POST':
        if form.is_valid():
            name = form.cleaned_data.get('name')
            try:
                course = Course.objects.get(id=course_id)
                course.name = name
                course.save()
                messages.success(request, "Successfully Updated")
            except:
                messages.error(request, "Could Not Update")
        else:
            messages.error(request, "Could Not Update")

    return render(request, 'hod_template/edit_course_template.html', context)


def edit_subject(request, subject_id):
    instance = get_object_or_404(Subject, id=subject_id)
    form = SubjectForm(request.POST or None, instance=instance)
    context = {
        'form': form,
        'subject_id': subject_id,
        'page_title': 'Edit Subject'
    }
    if request.method == 'POST':
        if form.is_valid():
            try:
                # Utiliser form.save() au lieu de créer un nouvel objet
                subject = form.save()
                messages.success(request, "Successfully Updated")
                return redirect(reverse('edit_subject', args=[subject_id]))
            except Exception as e:
                messages.error(request, "Could Not Update " + str(e))
        else:
            messages.error(request, "Fill Form Properly")
    
    # Toujours retourner un render pour la méthode GET
    return render(request, 'hod_template/edit_subject_template.html', context)

def add_session(request):
    form = SessionForm(request.POST or None)
    context = {'form': form, 'page_title': 'Add Session'}
    if request.method == 'POST':
        if form.is_valid():
            try:
                form.save()
                messages.success(request, "Session Created")
                return redirect(reverse('add_session'))
            except Exception as e:
                messages.error(request, 'Could Not Add ' + str(e))
        else:
            messages.error(request, 'Fill Form Properly ')
    return render(request, "hod_template/add_session_template.html", context)


def manage_session(request):
    sessions = Session.objects.all()
    context = {'sessions': sessions, 'page_title': 'Manage Sessions'}
    return render(request, "hod_template/manage_session.html", context)


def edit_session(request, session_id):
    instance = get_object_or_404(Session, id=session_id)
    form = SessionForm(request.POST or None, instance=instance)
    context = {'form': form, 'session_id': session_id,
               'page_title': 'Edit Session'}
    if request.method == 'POST':
        if form.is_valid():
            try:
                form.save()
                messages.success(request, "Session Updated")
                return redirect(reverse('edit_session', args=[session_id]))
            except Exception as e:
                messages.error(
                    request, "Session Could Not Be Updated " + str(e))
                return render(request, "hod_template/edit_session_template.html", context)
        else:
            messages.error(request, "Invalid Form Submitted ")
            return render(request, "hod_template/edit_session_template.html", context)

    else:
        return render(request, "hod_template/edit_session_template.html", context)


@csrf_exempt
def check_email_availability(request):
    email = request.POST.get("email")
    try:
        user = CustomUser.objects.filter(email=email).exists()
        if (user):
            return HttpResponse(True)
        return HttpResponse(False)
    except Exception as e:
        return HttpResponse(False)


@csrf_exempt
def student_feedback_message(request):
    if request.method != 'POST':
        feedbacks = FeedbackStudent.objects.all()
        context = {
            'feedbacks': feedbacks,
            'page_title': 'Student Feedback Messages'
        }
        return render(request, 'hod_template/student_feedback_template.html', context)
    else:
        feedback_id = request.POST.get('id')
        try:
            feedback = get_object_or_404(FeedbackStudent, id=feedback_id)
            reply = request.POST.get('reply')
            feedback.reply = reply
            feedback.save()
            return HttpResponse(True)
        except Exception as e:
            return HttpResponse(False)


@csrf_exempt
def staff_feedback_message(request):
    if request.method != 'POST':
        feedbacks = FeedbackStaff.objects.all()
        context = {
            'feedbacks': feedbacks,
            'page_title': 'Staff Feedback Messages'
        }
        return render(request, 'hod_template/staff_feedback_template.html', context)
    else:
        feedback_id = request.POST.get('id')
        try:
            feedback = get_object_or_404(FeedbackStaff, id=feedback_id)
            reply = request.POST.get('reply')
            feedback.reply = reply
            feedback.save()
            return HttpResponse(True)
        except Exception as e:
            return HttpResponse(False)


@csrf_exempt
def view_staff_leave(request):
    if request.method != 'POST':
        allLeave = LeaveReportStaff.objects.all()
        context = {
            'allLeave': allLeave,
            'page_title': 'Leave Applications From Staff'
        }
        return render(request, "hod_template/staff_leave_view.html", context)
    else:
        id = request.POST.get('id')
        status = request.POST.get('status')
        if (status == '1'):
            status = 1
        else:
            status = -1
        try:
            leave = get_object_or_404(LeaveReportStaff, id=id)
            leave.status = status
            leave.save()
            return HttpResponse(True)
        except Exception as e:
            return False


@csrf_exempt
def view_student_leave(request):
    if request.method != 'POST':  # Suppression de la parenthèse en trop
        allLeave = LeaveReportStudent.objects.all()
        context = {
            'allLeave': allLeave,
            'page_title': 'Leave Applications From Students'
        }
        return render(request, "hod_template/student_leave_view.html", context)
    else:
        id = request.POST.get('id')
        status = request.POST.get('status')
        if (status == '1'):
            status = 1
        else:
            status = -1
        try:
            leave = get_object_or_404(LeaveReportStudent, id=id)
            leave.status = status
            leave.save()
            return HttpResponse(True)
        except Exception as e:
            return False


def admin_view_attendance(request):
    subjects = Subject.objects.all()
    sessions = Session.objects.all()
    context = {
        'subjects': subjects,
        'sessions': sessions,
        'page_title': 'View Attendance'
    }

    return render(request, "hod_template/admin_view_attendance.html", context)


@csrf_exempt
def get_admin_attendance(request):
    subject_id = request.POST.get('subject')
    session_id = request.POST.get('session')
    attendance_date_id = request.POST.get('attendance_date_id')
    try:
        subject = get_object_or_404(Subject, id=subject_id)
        session = get_object_or_404(Session, id=session_id)
        attendance = get_object_or_404(
            Attendance, id=attendance_date_id, session=session)
        attendance_reports = AttendanceReport.objects.filter(
            attendance=attendance)
        json_data = []
        for report in attendance_reports:
            data = {
                "status":  str(report.status),
                "name": str(report.student)
            }
            json_data.append(data)
        return JsonResponse(json.dumps(json_data), safe=False)
    except Exception as e:
        return None


def admin_view_profile(request):
    admin = get_object_or_404(Admin, admin=request.user)
    form = AdminForm(request.POST or None, request.FILES or None,
                     instance=admin)
    context = {'form': form,
               'page_title': 'View/Edit Profile'
               }
    if request.method == 'POST':
        try:
            if form.is_valid():
                first_name = form.cleaned_data.get('first_name')
                last_name = form.cleaned_data.get('last_name')
                password = form.cleaned_data.get('password') or None
                passport = request.FILES.get('profile_pic') or None
                custom_user = admin.admin
                if password != None:
                    custom_user.set_password(password)
                if passport != None:
                    fs = FileSystemStorage()
                    filename = fs.save(passport.name, passport)
                    passport_url = fs.url(filename)
                    custom_user.profile_pic = passport_url
                custom_user.first_name = first_name
                custom_user.last_name = last_name
                custom_user.save()
                messages.success(request, "Profile Updated!")
                return redirect(reverse('admin_view_profile'))
            else:
                messages.error(request, "Invalid Data Provided")
        except Exception as e:
            messages.error(
                request, "Error Occured While Updating Profile " + str(e))
    return render(request, "hod_template/admin_view_profile.html", context)


def admin_notify_staff(request):
    staff = CustomUser.objects.filter(user_type=2)
    context = {
        'page_title': "Send Notifications To Staff",
        'allStaff': staff
    }
    return render(request, "hod_template/staff_notification.html", context)


def admin_notify_student(request):
    # Récupérer tous les étudiants triés par niveau
    students = Student.objects.all().order_by('niveau')
    
    # Récupérer les promotions distinctes
    promotions = Student.objects.values_list('niveau', flat=True).distinct()
    
    # Initialiser le contexte
    context = {
        'page_title': "Send Notifications To Students",
        'promotions': promotions,
    }
    
    # Regrouper les étudiants par niveau
    students_by_niveau = {}
    for student in students:
        niveau = student.niveau
        if (niveau not in students_by_niveau):
            students_by_niveau[niveau] = []
        students_by_niveau[niveau].append(student)
    
    # Ajouter students_by_niveau au contexte existant
    context['students_by_niveau'] = students_by_niveau
    
    return render(request, "hod_template/student_notification.html", context)

@csrf_exempt
def send_student_notification(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Méthode non autorisée.'}, status=405)
    
    # Récupérer les données
    id = request.POST.get('id')
    message = request.POST.get('message')
    file = request.FILES.get('file')

    if not id or not message:
        return JsonResponse({'success': False, 'error': 'Données manquantes'})

    try:
        # Récupérer l'étudiant
        student = get_object_or_404(Student, admin_id=id)
        
        # Créer la notification dans la base de données
        notification = NotificationStudent.objects.create(
            student=student,
            message=message,
            file=file,
            status='pending'
        )

        # Vérifier le token FCM
        if not student.admin.fcm_token:
            notification.status = 'pending'
            notification.save()
            return JsonResponse({
                'success': True,
                'warning': "L'étudiant n'a pas de token FCM, la notification sera envoyée plus tard."
            })

        # Envoyer la notification FCM
        url = "https://fcm.googleapis.com/fcm/send"
        body = {
            'notification': {
                'title': "Student Management System",
                'body': message,
                'click_action': reverse('student_view_notification'),
                'icon': static('dist/img/AdminLTELogo.png')
            },
            'to': student.admin.fcm_token
        }
        
        headers = {
            'Authorization': 'key=AAAA3Bm8j_M:APA91bElZlOLetwV696SoEtgzpJr2qbxBfxVBfDWFiopBWzfCfzQp2nRyC7_A2mlukZEHV4g1AmyC6P_HonvSkY2YyliKt5tT3fe_1lrKod2Daigzhb2xnYQMxUWjCAIQcUexAMPZePB',
            'Content-Type': 'application/json'
        }

        response = requests.post(url, data=json.dumps(body), headers=headers)
        
        if response.status_code == 200:
            notification.status = 'success'
            notification.save()
            return JsonResponse({
                'success': True,
                'message': 'Notification envoyée avec succès'
            })
        else:
            notification.status = 'failed'
            notification.save()
            return JsonResponse({
                'success': False,
                'error': f'Échec de l\'envoi: {response.text}'
            })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@csrf_exempt
def send_promotion_notification(request):
    if request.method == 'POST':
        niveau = request.POST.get('niveau')
        message = request.POST.get('message')
        file = request.FILES.get('file')

        if not niveau:
            return JsonResponse({'success': False, 'error': 'Niveau non spécifié.'})

        # Récupérer les étudiants pour le niveau spécifié
        students = Student.objects.filter(niveau=niveau)

        if not students.exists():
            return JsonResponse({
                'success': False,
                'error': f'Aucun étudiant trouvé pour ce niveau.'
            })

        notifications_sent = 0
        errors = []
        warnings = []

        for student in students:
            try:
                # Vérifier si l'étudiant a un token FCM
                if not student.admin or not student.admin.fcm_token:
                    # Créer la notification en base avec statut 'pending'
                    NotificationStudent.objects.create(
                        student=student,
                        message=message,
                        file=file,
                        status='pending'
                    )
                    warnings.append(f"Pas de token FCM pour {student.admin.email if student.admin else 'étudiant'}")
                    continue

                # Préparer et envoyer la notification FCM
                url = "https://fcm.googleapis.com/fcm/send"
                body = {
                    'notification': {
                        'title': "Student Management System",
                        'body': message,
                        'click_action': reverse('student_view_notification'),
                        'icon': static('dist/img/AdminLTELogo.png')
                    },
                    'to': student.admin.fcm_token
                }

                headers = {
                    'Authorization': 'key=AAAA3Bm8j_M:APA91bElZlOLetwV696SoEtgzpJr2qbxBfxVBfDWFiopBWzfCfzQp2nRyC7_A2mlukZEHV4g1AmyC6P_HonvSkY2YyliKt5tT3fe_1lrKod2Daigzhb2xnYQMxUWjCAIQcUexAMPZePB',
                    'Content-Type': 'application/json'
                }

                response = requests.post(url, data=json.dumps(body), headers=headers)
                
                if response.status_code == 200:
                    NotificationStudent.objects.create(
                        student=student,
                        message=message,
                        file=file,
                        status='success'
                    )
                    notifications_sent += 1
                else:
                    errors.append(f"Échec pour {student.admin.email}: {response.text}")

            except Exception as e:
                errors.append(f"Erreur pour {student.admin.email if student.admin else 'étudiant'}: {str(e)}")

        # Préparer la réponse
        response_data = {
            'success': notifications_sent > 0 or len(warnings) > 0,
            'message': f"{notifications_sent} notification(s) envoyée(s) avec succès."
        }
        
        if warnings:
            response_data['warnings'] = warnings
        if errors:
            response_data['errors'] = errors

        return JsonResponse(response_data)

    return JsonResponse({'success': False, 'error': 'Méthode non autorisée.'})


  
@csrf_exempt
def send_staff_notification(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Méthode non autorisée'})

    try:
        id = request.POST.get('id')
        message = request.POST.get('message')
        file = request.FILES.get('file')
        
        staff = get_object_or_404(Staff, admin_id=id)
        
        # Créer la notification
        notification = NotificationStaff.objects.create(
            staff=staff,
            message=message
        )

        # Gestion du fichier
        if file:
            # Assurez-vous que le dossier existe
            upload_dir = os.path.join(settings.MEDIA_ROOT, 'staff_notifications')
            os.makedirs(upload_dir, exist_ok=True)
            
            # Sauvegarde du fichier
            notification.file = file
            notification.save()

        # Envoi de la notification FCM
        if staff.admin.fcm_token:
            # ... le reste du code FCM ...
            pass

        return JsonResponse({
            'success': True,
            'message': 'Notification envoyée avec succès'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


def delete_staff(request, staff_id):
    staff = get_object_or_404(CustomUser, staff__id=staff_id)
    staff.delete()
    messages.success(request, "Staff deleted successfully!")
    return redirect(reverse('manage_staff'))


def delete_student(request, student_id):
    student = get_object_or_404(CustomUser, student__id=student_id)
    student.delete()
    messages.success(request, "Student deleted successfully!")
    return redirect(reverse('manage_student'))


def delete_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    try:
        course.delete()
        messages.success(request, "Course deleted successfully!")
    except Exception:
        messages.error(
            request, "Sorry, some students are assigned to this course already. Kindly change the affected student course and try again")
    return redirect(reverse('manage_course'))


def delete_subject(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id)
    subject.delete()
    messages.success(request, "Subject deleted successfully!")
    return redirect(reverse('manage_subject'))


def delete_session(request, session_id):
    session = get_object_or_404(Session, id=session_id)
    try:
        session.delete()
        messages.success(request, "Session deleted successfully!")
    except Exception:
        messages.error(
            request, "There are students assigned to this session. Please move them to another session.")
    return redirect(reverse('manage_session'))




# fonction EMPLOI DU TEMPS

from django.shortcuts import get_object_or_404, render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime, timedelta
from collections import defaultdict
from .models import EmploiTemps, Subject, Staff, AcademicYear, Holiday, Vacation  # Assure-toi que tes modèles sont correctement importés
from django.contrib import messages
from django.urls import reverse
from django.db.models import Q

@csrf_exempt
def creer_emploi_temps(request):
    if request.method == "POST":
        promotion = request.POST.get("promotion")
        try:
            type_evenement = request.POST.get("type_evenement")
            date_debut = request.POST.get("date_debut")
            matiere_id = request.POST.get("matiere")
            
            # Récupérer le titre selon le type d'événement
            titre_evenement = None
            if type_evenement == 'CONFERENCE':
                # Pour une conférence, utiliser directement le champ titre_evenement
                titre_evenement = request.POST.get("titre_evenement")
            elif type_evenement == 'TOURNEE':
                titre_evenement = request.POST.get("titre_evenement_tournee")
            elif type_evenement == 'SORTIE':
                titre_evenement = request.POST.get("titre_evenement_sortie")
            elif type_evenement == 'PROJET':
                titre_evenement = request.POST.get("titre_evenement_projet")
            elif type_evenement == 'VISITE_MILITAIRE':
                titre_evenement = request.POST.get("titre_evenement")

            # Définir les types d'événements
            EVENEMENTS_AVEC_HORAIRE = ['COURS', 'EXAMEN_PARTIEL', 'EXAMEN_FINAL', 'RATTRAPAGE', 'FORMATION_MILITAIRE', 'CONFERENCE']
            EVENEMENTS_MULTI_JOURS = ['TOURNEE', 'SORTIE', 'PROJET', 'VISITE_MILITAIRE']

            if type_evenement in EVENEMENTS_MULTI_JOURS:
                date_fin = request.POST.get("date_fin")

                if not date_fin:
                    raise ValueError("La date de fin est requise pour ce type d'événement")
                if not titre_evenement:
                    raise ValueError(f"Le titre est requis pour un événement de type {type_evenement}")

                # Pour les sorties, on conserve la référence à la matière
                matiere_instance = None
                if type_evenement == 'SORTIE' and matiere_id:
                    matiere_instance = get_object_or_404(Subject, id=matiere_id)

                emploi_temps = EmploiTemps.objects.create(
                    niveau=promotion,
                    type_evenement=type_evenement,
                    date=date_debut,
                    date_debut=date_debut,
                    date_fin=date_fin,
                    titre_evenement=titre_evenement,
                    matiere=matiere_instance,  # Sera None pour les autres types d'événements
                    professeur=None,
                    heure_debut=None,
                    heure_fin=None
                )

            elif type_evenement in EVENEMENTS_AVEC_HORAIRE:
                heure_debut = request.POST.get("heure_debut")
                heure_fin = request.POST.get("heure_fin")
                
                if not (heure_debut and heure_fin):
                    raise ValueError("Les heures de début et de fin sont requises pour ce type d'événement")

                if matiere_id:
                    matiere = get_object_or_404(Subject, id=matiere_id)
                else:
                    matiere = None

                # Gestion spécifique pour FORMATION_MILITAIRE
                if type_evenement == 'FORMATION_MILITAIRE':
                    professeur = None # Pas de professeur pour la formation militaire
                    matiere = None  # Pas
                else:
                    # Récupérer le professeur associé à la matière
                    try:
                        professeur = matiere.professeur
                        # Afficher erreur si c'est un examen/rattrapage et qu'il n'y a pas de professeur
                        if type_evenement in ['EXAMEN_PARTIEL', 'EXAMEN_FINAL', 'RATTRAPAGE'] and professeur is None:
                            messages.error(request, "Aucun professeur n'est associé à cette matière. Veuillez contacter l'administrateur.")
                            return redirect(f"{reverse('creer_emploi_temps')}?promotion={promotion}")

                    except AttributeError:
                        #Gérer le cas où il n'y a pas de professeur associé (même pour les autres types)
                        professeur = None
                        
                emploi_temps = EmploiTemps.objects.create(
                    niveau=promotion,
                    type_evenement=type_evenement,
                    date=date_debut,
                    date_debut=date_debut,
                    matiere=matiere,
                    professeur=professeur,
                    titre_evenement=titre_evenement,  # Utilisation directe du titre
                    heure_debut=datetime.strptime(heure_debut, '%H:%M').time(),
                    heure_fin=datetime.strptime(heure_fin, '%H:%M').time()
                )

            # Retourner une réponse JSON pour les requêtes AJAX
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True})

            messages.success(request, "Événement programmé avec succès")
            return redirect(f"{reverse('creer_emploi_temps')}?promotion={promotion}")

        except Exception as e:
            print(f"Erreur: {str(e)}")  # Debug
            messages.error(request, f"Erreur lors de la programmation : {str(e)}")
            return redirect(f"{reverse('creer_emploi_temps')}?promotion={promotion}")

    else:
        # Le reste de votre code pour le cas GET reste inchangé
        promotion_selected = request.GET.get('promotion', '3ème année')
        promotions = ['3ème année', '4ème année', '5ème année', '6ème année']
        date_debut = request.GET.get('date_debut', datetime.now().date())
        if isinstance(date_debut, str):
            date_debut = datetime.strptime(date_debut, '%Y-%m-%d').date()
        date_fin = date_debut + timedelta(days=14)

        # Récupération de l'année académique courante
        try:
            current_year = AcademicYear.objects.filter(start_date__lte=date_debut, end_date__gte=date_debut).first()
        except AcademicYear.DoesNotExist:
            messages.error(request, "Aucune année académique n'a été définie pour cette date.")
            current_year = None

        # Création des événements 'JOUR_FERIE' et 'VACANCES'
        if current_year:
            # Récupérer les jours fériés de l'année courante
            holidays = Holiday.objects.filter(date__range=[current_year.start_date, current_year.end_date])
            for holiday in holidays:
                # Vérifier si l'événement n'existe pas déjà pour éviter les doublons
                if not EmploiTemps.objects.filter(date=holiday.date, type_evenement='JOUR_FERIE', niveau=promotion_selected).exists():
                    EmploiTemps.objects.create(
                        niveau=promotion_selected,
                        date=holiday.date,
                        type_evenement='JOUR_FERIE',
                        titre_evenement=holiday.description,
                    )

            # Récupérer les vacances de l'année courante
            vacations = Vacation.objects.filter(start_date__range=[current_year.start_date, current_year.end_date])
            for vacation in vacations:
                # Pour chaque jour de la période de vacances
                current_date = vacation.start_date
                while current_date <= vacation.end_date:
                    # Vérifier si la période n'existe pas déjà pour éviter les doublons
                    if not EmploiTemps.objects.filter(date=current_date, type_evenement='VACANCES', niveau=promotion_selected, titre_evenement=vacation.description).exists():
                        EmploiTemps.objects.create(
                            niveau=promotion_selected,
                             date = current_date,
                            type_evenement='VACANCES',
                            titre_evenement=vacation.description,
                        )
                    current_date += timedelta(days=1)
        sessions = EmploiTemps.objects.filter(
            Q(date__range=[date_debut, date_fin], niveau=promotion_selected) |
            Q(date_debut__lte=date_fin, date_fin__gte=date_debut, niveau=promotion_selected)
        ).select_related('matiere', 'professeur').order_by('heure_debut')  # Ajout du order_by

        sessions_by_date = defaultdict(dict)
        dates = []
        current_date = date_debut
        while (current_date <= date_fin):
            dates.append(current_date)
            current_date += timedelta(days=1)
        horaires = ['08:00-10:00', '10:00-12:00', '14:00-16:00', '16:00-18:00']

        # Organiser les sessions par date
        # Organiser les sessions par date
        sessions_by_date = defaultdict(lambda: defaultdict(dict))
        for session in sessions:
            if (session.type_evenement in ['TOURNEE', 'SORTIE', 'PROJET', 'VISITE_MILITAIRE', 'VACANCES', 'JOUR_FERIE']):
                # Pour les événements multi-jours
                if (session.date_debut and session.date_fin):
                    event_start = max(session.date_debut, date_debut)
                    event_end = min(session.date_fin, date_fin)
                    current = event_start
                    while (current <= event_end):
                        sessions_by_date[current]['full_day'] = session
                        current += timedelta(days=1)
                else:
                    # Pour les événements VACANCES et JOUR_FERIE
                    sessions_by_date[session.date]['full_day'] = session
            else:
                # Pour les événements standards, utiliser heure_debut comme clé
                time_key = session.heure_debut.strftime('%H:%M')
                sessions_by_date[session.date][time_key] = session

        context = {
            "promotions": promotions,
            "promotion_selected": promotion_selected,
            "subjects": Subject.objects.filter(niveau=promotion_selected).order_by('name'),
            #"professeurs": Staff.objects.all().order_by('admin__last_name'),  # Plus besoin de cette ligne
            "sessions_by_date": dict(sessions_by_date),
            "dates": dates,
            "horaires": horaires,
            "date_debut": date_debut,
            "date_fin": date_fin,
            'page_title': f'Emploi du temps - {promotion_selected}'
        }
        # Remplacer horaires fixes par plage horaire
        heures_possibles = [
            {'debut': '08:00', 'fin': '19:00'}  # Plage horaire de la journée
        ]

        context.update({
            'heures_possibles': heures_possibles,
            'intervalle_minutes': 30  # Pour l'affichage de la grille
        })

        sessions_by_date = defaultdict(list)  # Changé en list au lieu de dict
        for session in sessions:
            if session.type_evenement in ['TOURNEE', 'SORTIE', 'PROJET', 'VISITE_MILITAIRE', 'VACANCES', 'JOUR_FERIE']:
                # Pour les événements multi-jours
                if session.date_debut and session.date_fin:
                    event_start = max(session.date_debut, date_debut)
                    event_end = min(session.date_fin, date_fin)
                    current = event_start
                    while current <= event_end:
                        sessions_by_date[current].append(session)
                        current += timedelta(days=1)
            else:
                # Pour les événements standards avec horaire
                sessions_by_date[session.date].append(session)

        context.update({
            'sessions_by_date': dict(sessions_by_date)
        })

        return render(request, "hod_template/creer_emploi_temps.html", context)

def choisir_promotion(request):
    promotions = [
        '3ème année',
        '4ème année',
        '5ème année',
        '6ème année'
    ]
    context = {
        'promotions': promotions,
        'page_title': 'Choisir une promotion'
    }
    return render(request, 'hod_template/choisir_promotion.html', context)
def liste_emplois(request):
    promotion_selected = request.GET.get('promotion', '3ème année')
    date_debut = request.GET.get('date_debut')
    date_fin = request.GET.get('date_fin')

    promotions = ['3ème année', '4ème année', '5ème année', '6ème année']

    # Convertir les dates
    if date_debut:
        date_debut = datetime.strptime(date_debut, '%Y-%m-%d').date()
    else:
        date_debut = datetime.now().date()

    if date_fin:
        date_fin = datetime.strptime(date_fin, '%Y-%m-%d').date()
    else:
        date_fin = date_debut + timedelta(days=14)

    # Récupérer tous les événements (standard et multi-jours)
    sessions = EmploiTemps.objects.filter(
        Q(niveau=promotion_selected) &
        (
            (Q(date__range=[date_debut, date_fin])) |
            (
                (Q(date_debut__lte=date_fin) if date_debut else Q(pk__in=[])) &
                (Q(date_fin__gte=date_debut) if date_fin else Q(pk__in=[])) &
                Q(type_evenement__in=['TOURNEE', 'SORTIE', 'PROJET', 'VISITE_MILITAIRE', 'VACANCES', 'JOUR_FERIE'])
            )
        )
    ).select_related('matiere', 'professeur').order_by('date')

    # Calculer les heures effectuées et la progression pour chaque séance
    for session in sessions:
        if session.type_evenement == 'COURS' and session.heure_debut and session.heure_fin:
            # Convertir les heures de début et de fin en datetime pour le calcul
            debut = datetime.combine(session.date, session.heure_debut)
            fin = datetime.combine(session.date, session.heure_fin)
            
            # Calculer la durée de la séance en heures
            duree_seance = (fin - debut).total_seconds() / 3600  # Convertir en heures
            
            # Calculer les heures effectuées pour les séances précédentes
            seances_precedentes = EmploiTemps.objects.filter(
                matiere=session.matiere,
                type_evenement='COURS',
                date__lt=session.date  # Uniquement les séances avant la date actuelle
            )
            
            total_heures = duree_seance  # Commencer avec la durée de la séance actuelle
            
            # Ajouter les durées des séances précédentes
            for seance in seances_precedentes:
                debut_seance = datetime.combine(seance.date, seance.heure_debut)
                fin_seance = datetime.combine(seance.date, seance.heure_fin)
                duree = (fin_seance - debut_seance).total_seconds() / 3600
                total_heures += duree
            
            # Calculer la progression
            if session.matiere and session.matiere.volume_horaire_total > 0:
                progression = min(int((total_heures / session.matiere.volume_horaire_total) * 100), 100)
            else:
                progression = 0
                
            session.progression = progression
            session.numero_seance = len(seances_precedentes) + 1  # Numéro de séance basé sur le compte des séances précédentes

    # Générer les dates
    dates = []
    current_date = date_debut
    while current_date <= date_fin:
        dates.append(current_date)
        current_date += timedelta(days=1)

    # Organiser les sessions par date
    sessions_by_date = defaultdict(list)
    for session in sessions:
        sessions_by_date[session.date].append(session) # Organiser par date, et lister les sessions
    
    # Trier les sessions par heure pour chaque date
    for date in sessions_by_date:
        sessions_by_date[date] = sorted(
            sessions_by_date[date],
            key=lambda x: (
                # Les événements multi-jours en premier
                0 if x.type_evenement in ['TOURNEE', 'SORTIE', 'PROJET', 'VISITE_MILITAIRE', 'VACANCES', 'JOUR_FERIE'] else 1,
                # Puis par heure de début (si existe)
                x.heure_debut.strftime('%H:%M') if x.heure_debut else '23:59'
            )
        )

    # Calculer la progression pour chaque matière avec un calcul correct
    subjects = Subject.objects.filter(niveau=promotion_selected)
    today = datetime.now().date()

    for subject in subjects:
        # Récupérer toutes les séances de cours jusqu'à aujourd'hui
        seances = EmploiTemps.objects.filter(
            matiere=subject,
            type_evenement='COURS',
            date__lte=today,  # Seulement les séances passées
            niveau=promotion_selected
        )
        
        heures_realisees = 0
        for seance in seances:
            if seance.heure_debut and seance.heure_fin:
                debut = datetime.combine(seance.date, seance.heure_debut)
                fin = datetime.combine(seance.date, seance.heure_fin)
                duree = (fin - debut).total_seconds() / 3600  # Convertir en heures
                heures_realisees += duree

        # Arrondir les heures réalisées à 2 décimales
        subject.heures_realisees = round(heures_realisees, 2)
        
        # Calculer la progression en pourcentage
        if subject.volume_horaire_total > 0:
            subject.progression = min(
                round((subject.heures_realisees / subject.volume_horaire_total) * 100),
                100
            )
        else:
            subject.progression = 0

        # Calculer le nombre de séances restantes
        subject.nombre_seances = seances.count()
        subject.seances_totales = round(subject.volume_horaire_total / 2)  # 2h par séance
        subject.seances_restantes = max(0, subject.seances_totales - subject.nombre_seances)

    context = {
        'sessions_by_date': dict(sessions_by_date),
        'promotions': promotions,
        'promotion_selected': promotion_selected,
        'date_debut': date_debut,
        'date_fin': date_fin,
        'dates': dates,
        'page_title': f'Emploi du temps - {promotion_selected}',
        'subjects': subjects  # Passer les matières mises à jour au template
    }

    return render(request, "hod_template/liste_emplois.html", context)


@csrf_exempt
def get_matieres_by_niveau(request):
    niveau = request.GET.get('niveau')
    matieres = Subject.objects.filter(niveau=niveau).values('id', 'name')
    return JsonResponse({'matieres': list(matieres)})
    niveau = request.GET.get('niveau')
    matieres = Subject.objects.filter(niveau=niveau).values('id', 'name')
    return JsonResponse({'matieres': list(matieres)})

# Ajouter cette nouvelle fonction
def historique_emploi(request):
    promotion_selected = request.GET.get('promotion', '3ème année')
    date_debut = request.GET.get('date_debut')
    date_fin = request.GET.get('date_fin')
    
    promotions = ['3ème année', '4ème année', '5ème année', '6ème année']
    horaires = ['08:00-10:00', '10:00-12:00', '14:00-16:00', '16:00-18:00']

    # Convertir les dates
    if date_debut:
        date_debut = datetime.strptime(date_debut, '%Y-%m-%d').date()
    else:
        date_debut = datetime.now().date().replace(day=1)
    
    if date_fin:
        date_fin = datetime.strptime(date_fin, '%Y-%m-%d').date()
    else:
        date_fin = (date_debut + timedelta(days=32)).replace(day=1) - timedelta(days=1)

    # Récupérer TOUS les événements y compris multi-jours
    sessions = EmploiTemps.objects.filter(
        Q(niveau=promotion_selected) &
        (
            # Pour les événements standards
            (Q(date__range=[date_debut, date_fin])) |
            # Pour les événements multi-jours
            (
                (Q(date_debut__lte=date_fin) if date_debut else Q(pk__in=[])) &
                (Q(date_fin__gte=date_debut) if date_fin else Q(pk__in=[])) &
                Q(type_evenement__in=['TOURNEE', 'SORTIE', 'PROJET', 'VISITE_MILITAIRE', 'VACANCES', 'JOUR_FERIE'])
            )
        )
    ).select_related('matiere', 'professeur')

    dates = []
    current_date = date_debut
    while current_date <= date_fin:
        dates.append(current_date)
        current_date += timedelta(days=1)

    # Organiser les sessions par date
    sessions_by_date = defaultdict(dict)
    for session in sessions:
        if session.type_evenement in ['TOURNEE', 'SORTIE', 'PROJET', 'VISITE_MILITAIRE', 'VACANCES', 'JOUR_FERIE']:
            # Pour les événements multi-jours
            event_start = max(session.date_debut, date_debut) if session.date_debut else date_debut
            event_end = min(session.date_fin, date_fin) if session.date_fin else date_fin
            current = event_start
            while current <= event_end:
                sessions_by_date[current]['full_day'] = session
                current += timedelta(days=1)
        else:
            # Pour les événements standards
            sessions_by_date[session.date][session.horaire] = session

    context = {
        'sessions_by_date': dict(sessions_by_date),
        'promotions': promotions,
        'horaires': horaires,
        'promotion_selected': promotion_selected,
        'date_debut': date_debut,
        'date_fin': date_fin,
        'dates': dates,
        'page_title': 'Historique des emplois'
    }
    
    return render(request, 'hod_template/historique_emploi.html', context)
    
def supprimer_evenement(request, evenement_id):
    try:
        # Récupérer l'événement initial
        evenement = get_object_or_404(EmploiTemps, id=evenement_id)
        niveau = evenement.niveau
        
        # Pour les événements qui s'étendent sur plusieurs jours
        if evenement.type_evenement in ['VACANCES', 'PROJET', 'VISITE_MILITAIRE', 'TOURNEE', 'JOUR_FERIE']:  # Retrait de 'FORMATION_MILITAIRE'
            # Supprimer tous les événements correspondants dans la période
            evenements_periode = EmploiTemps.objects.filter(
                niveau=evenement.niveau,
                type_evenement=evenement.type_evenement,
                titre_evenement=evenement.titre_evenement,
                date_debut=evenement.date_debut,
                date_fin=evenement.date_fin
            )
            nombre_supprime = evenements_periode.count()
            evenements_periode.delete()
            messages.success(request, f"{nombre_supprime} événements supprimés avec succès")
        else:
            # Pour les événements sur un seul créneau (y compris FORMATION_MILITAIRE maintenant)
            evenement.delete()
            messages.success(request, "Événement supprimé avec succès")
            
    except Exception as e:
        messages.error(request, f"Erreur lors de la suppression : {str(e)}")
    
    # Rediriger vers la même page avec la même promotion sélectionnée
    return redirect(f"{reverse('creer_emploi_temps')}?promotion={niveau}")




# emploi des options :
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from .models import Option5eme, Subject, EmploiTempsOption, Holiday, Vacation, AcademicYear, Staff, MatiereOption5eme
from django.utils import timezone
from datetime import date, timedelta, datetime
from collections import defaultdict
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def gerer_emploi_temps_options(request):
    # Définir les options par défaut et les récupérer depuis la base de données
    options = Option5eme.objects.all()
    option_selected = request.GET.get('option', None)

    if not options.exists():
      #Création des options
        Option5eme.objects.create(nom='GRN')
        Option5eme.objects.create(nom='VALO')
        Option5eme.objects.create(nom='AF')
        Option5eme.objects.create(nom='ECO')
        Option5eme.objects.create(nom='EF')
        Option5eme.objects.create(nom='GAP')
        options = Option5eme.objects.all()
        #Redirection
        first_option = Option5eme.objects.first()
        if first_option:
             return redirect(f"{reverse('gerer_emploi_temps_options')}?option={first_option.nom}")
        else :
            messages.error(request, "Impossible de créer les options par defauts")

    if not option_selected:
        # Si aucune option n'est sélectionnée, prendre la première option par défaut
        first_option = Option5eme.objects.first()
        if first_option:
            option_selected = first_option.nom
        else:
            option_selected = None  # Ou gérer le cas où il n'y a pas d'options

    promotions = ['3ème année', '4ème année', '5ème année', '6ème année']

    # Récupère les matières de 5ème année pour l'option sélectionnée
    if option_selected:
        selected_option = Option5eme.objects.get(nom=option_selected)
        matiere_options = MatiereOption5eme.objects.filter(option=selected_option)
    else:
        matiere_options = []

    staffs = Staff.objects.all()

    date_debut = date.today()
    date_fin = date_debut + timedelta(days=14)

    # Définir les types d'événements (en dehors du bloc try)
    EVENEMENTS_AVEC_HORAIRE = ['COURS', 'EXAMEN_PARTIEL', 'EXAMEN_FINAL', 'RATTRAPAGE', 'FORMATION_MILITAIRE', 'CONFERENCE']
    EVENEMENTS_MULTI_JOURS = ['TOURNEE', 'SORTIE', 'PROJET', 'VISITE_MILITAIRE']
    EVENEMENTS_AVEC_TITRE_OBLIGATOIRE = ['TOURNEE', 'SORTIE', 'PROJET', 'VISITE_MILITAIRE', 'CONFERENCE']

    if request.method == 'POST':
        try:
            option_nom = request.POST.get('option')
            type_evenement = request.POST.get('type_evenement')
            date_debut_str = request.POST.get('date_debut')
            matiere_id = request.POST.get('matiere')  # ID de MatiereOption5eme
            heure_debut_str = request.POST.get('heure_debut')
            heure_fin_str = request.POST.get('heure_fin')
            titre_evenement = request.POST.get('titre_evenement')

            option = Option5eme.objects.get(nom=option_nom)

            if matiere_id:
                matiere_option = get_object_or_404(MatiereOption5eme, pk=matiere_id)  # Récupérer l'instance de MatiereOption5eme
                matiere = matiere_option #On récupere l'objet
                professeur = matiere_option.professeur
            else:
                matiere_option = None
                matiere = None
                professeur = None

            date_debut = date.fromisoformat(date_debut_str)

            # Vérifier si le titre est vide (seulement si c'est un événement avec titre obligatoire)
            if type_evenement in EVENEMENTS_AVEC_TITRE_OBLIGATOIRE and not titre_evenement:
                messages.error(request, "Le titre de l'événement est obligatoire pour ce type d'événement.")
                return redirect(f"{reverse('gerer_emploi_temps_options')}?option={option.nom}")

            if type_evenement in EVENEMENTS_MULTI_JOURS:
                date_fin = request.POST.get("date_fin")

                if not date_fin:
                    messages.error(request, "La date de fin est requise pour ce type d'événement")
                    return redirect(f"{reverse('gerer_emploi_temps_options')}?option={option.nom}")

                emploi_temps = EmploiTempsOption.objects.create(
                    option=option,
                    type_evenement=type_evenement,
                    date=date_debut,
                    date_debut=date_debut,
                    date_fin=date_fin,
                    titre_evenement=titre_evenement,
                    matiere=matiere_option,  # Instance de MatiereOption5eme
                    professeur=None,
                    heure_debut=None,
                    heure_fin=None
                )

            elif type_evenement in EVENEMENTS_AVEC_HORAIRE:
                heure_debut = request.POST.get("heure_debut")
                heure_fin = request.POST.get("heure_fin")

                if not (heure_debut and heure_fin):
                    messages.error(request, "Les heures de début et de fin sont requises pour ce type d'événement")
                    return redirect(f"{reverse('gerer_emploi_temps_options')}?option={option.nom}")

                # Gestion spécifique pour FORMATION_MILITAIRE
                if type_evenement == 'FORMATION_MILITAIRE':
                    professeur = None
                    matiere = None
                else:
                    #professeur=matiere.professeur
                    #if matiere:
                     professeur = matiere_option.professeur if matiere_option else None   #instance
                    #else:
                        #professeur=None

                emploi_temps = EmploiTempsOption.objects.create(
                    option=option,
                    type_evenement=type_evenement,
                    date=date_debut,
                    date_debut=date_debut,
                    matiere=matiere_option,  # Instance de MatiereOption5eme
                    professeur=professeur,
                    titre_evenement=titre_evenement,
                    heure_debut=datetime.strptime(heure_debut, '%H:%M').time(),
                    heure_fin=datetime.strptime(heure_fin, '%H:%M').time()
                )

            # Retourner une réponse JSON pour les requêtes AJAX
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True})

            messages.success(request, "Événement programmé avec succès")
            return redirect(f"{reverse('gerer_emploi_temps_options')}?option={option.nom}")

        except Exception as e:
            print(f"Erreur: {str(e)}")
            messages.error(request, f"Erreur lors de la programmation : {str(e)}")
            return redirect(f"{reverse('gerer_emploi_temps_options')}?option={option.nom}")

    else:
        # Le reste de votre code pour le cas GET reste inchangé
        date_debut = request.GET.get('date_debut', datetime.now().date())
        if isinstance(date_debut, str):
            date_debut = datetime.strptime(date_debut, '%Y-%m-%d').date()
        date_fin = date_debut + timedelta(days=14)

        # Récupération de l'année académique courante
        try:
            current_year = AcademicYear.objects.filter(start_date__lte=date_debut, end_date__gte=date_debut).first()
        except AcademicYear.DoesNotExist:
            messages.error(request, "Aucune année académique n'a été définie pour cette date.")
            current_year = None

        # Création des événements 'JOUR_FERIE' et 'VACANCES'
        if current_year:
            # Récupérer les jours fériés de l'année courante
            holidays = Holiday.objects.filter(date__range=[current_year.start_date, current_year.end_date])
            for holiday in holidays:
                # Vérifier si l'événement n'existe pas déjà pour éviter les doublons
                if not EmploiTempsOption.objects.filter(date=holiday.date, type_evenement='JOUR_FERIE', option__nom=option_selected).exists():
                    Option_choosed = Option5eme.objects.get(nom=option_selected)
                    emploi_temps = EmploiTempsOption(
                        option=Option_choosed,
                        date=holiday.date,
                        type_evenement='JOUR_FERIE',
                        titre_evenement=holiday.description,
                    )
                    emploi_temps.save()

            # Récupérer les vacances de l'année courante
            vacations = Vacation.objects.filter(start_date__range=[current_year.start_date, current_year.end_date])
            for vacation in vacations:
                # Pour chaque jour de la période de vacances
                current_date = vacation.start_date
                while current_date <= vacation.end_date:
                    # Vérifier si la période n'existe pas déjà pour éviter les doublons
                    if not EmploiTempsOption.objects.filter(date=current_date, type_evenement='VACANCES', option__nom=option_selected, titre_evenement=vacation.description).exists():
                        Option_choosed = Option5eme.objects.get(nom=option_selected)
                        EmploiTempsOption.objects.create(
                            option=Option_choosed,
                            date=current_date,
                            type_evenement='VACANCES',
                            titre_evenement=vacation.description,
                        )
                    current_date += timedelta(days=1)

        # Récupérer l'emploi du temps pour l'option sélectionnée et les 14 prochains jours
        if option_selected:
            selected_option = Option5eme.objects.get(nom=option_selected)
            sessions = EmploiTempsOption.objects.filter(
                Q(date__range=[date_debut, date_fin], option=selected_option) |
                Q(date_debut__lte=date_fin, date_fin__gte=date_debut, option=selected_option)
            ).select_related('matiere', 'professeur').order_by('heure_debut')
        else:
            sessions = []

        sessions_by_date = defaultdict(dict)
        dates = []
        current_date = date_debut
        while (current_date <= date_fin):
            dates.append(current_date)
            current_date += timedelta(days=1)
        horaires = ['08:00-10:00', '10:00-12:00', '14:00-16:00', '16:00-18:00']

        sessions_by_date = defaultdict(lambda: defaultdict(dict))
        for session in sessions:
            if (session.type_evenement in ['TOURNEE', 'SORTIE', 'PROJET', 'VISITE_MILITAIRE', 'VACANCES', 'JOUR_FERIE']):
                # Pour les événements multi-jours
                if (session.date_debut and session.date_fin):
                    event_start = max(session.date_debut, date_debut)
                    event_end = min(session.date_fin, date_fin)
                    current = event_start
                    while current <= event_end:
                        sessions_by_date[current]['full_day'] = session
                        current += timedelta(days=1)
                else:
                    # Pour les événements VACANCES et JOUR_FERIE
                    sessions_by_date[session.date]['full_day'] = session
            else:
                # Pour les événements standards, utiliser heure_debut comme clé
                time_key = session.heure_debut.strftime('%H:%M')
                sessions_by_date[session.date][time_key] = session

        context = {
            "promotions": promotions,
            "promotion_selected": '', #Pas besoin de cette variable
            "options": options,
            "option_selected": option_selected,
            "matieres_options": matiere_options,  # Les instances de MatiereOption5eme
            "sessions_by_date": dict(sessions_by_date),
            "dates": dates,
            "horaires": horaires,
            "date_debut": date_debut,
            "date_fin": date_fin,
            'page_title': f'Emploi du temps - {option_selected}'
        }

        # Remplacer horaires fixes par plage horaire
        heures_possibles = [
            {'debut': '08:00', 'fin': '19:00'}  # Plage horaire de la journée
        ]

        context.update({
            'heures_possibles': heures_possibles,
            'intervalle_minutes': 30  # Pour l'affichage de la grille
        })

        sessions_by_date = defaultdict(list)  # Changé en list au lieu de dict
        for session in sessions:
            if session.type_evenement in ['TOURNEE', 'SORTIE', 'PROJET', 'VISITE_MILITAIRE', 'VACANCES', 'JOUR_FERIE']:
                # Pour les événements multi-jours
                if session.date_debut and session.date_fin:
                    event_start = max(session.date_debut, date_debut)
                    event_end = min(session.date_fin, date_fin)
                    current = event_start
                    while current <= event_end:
                        sessions_by_date[current].append(session)
                        current += timedelta(days=1)
            else:
                # Pour les événements standards avec horaire
                sessions_by_date[session.date].append(session)

        context.update({
            'sessions_by_date': dict(sessions_by_date)
        })

        return render(request, "hod_template/options_5eme.html", context)
        
def supprimer_evenement_option(request, evenement_id):
    try:
        # Récupérer l'événement à supprimer
        evenement = get_object_or_404(EmploiTempsOption, id=evenement_id)

        #Récupere l'option du model.
        option = evenement.option.nom
        # Supprimer l'événement
        evenement.delete()
        messages.success(request, "Événement supprimé avec succès.")

    except EmploiTempsOption.DoesNotExist:
        messages.error(request, "L'événement n'existe pas.")
        option = "GRN"  # Valeur par défaut si l'événement n'existe pas

    except Exception as e:
        messages.error(request, f"Erreur lors de la suppression : {str(e)}")
        option = "GRN"

    # Rediriger vers la page de gestion des options
    return redirect(reverse('gerer_emploi_temps_options') + '?option=' + option)

def suivi_progression_options(request):
    option_selected = request.GET.get('option')
    date_debut = request.GET.get('date_debut')
    date_fin = request.GET.get('date_fin')
    options = Option5eme.objects.all()
    
    if not option_selected and options.exists():
        option_selected = options.first().nom
    
    # Gestion des dates
    today = datetime.now().date()
    if date_debut:
        date_debut = datetime.strptime(date_debut, '%Y-%m-%d').date()
    else:
        date_debut = today
    
    if date_fin:
        date_fin = datetime.strptime(date_fin, '%Y-%m-%d').date()
    else:
        date_fin = date_debut + timedelta(days=14)
    
    # Récupérer toutes les matières de l'option sélectionnée
    subjects = Subject.objects.filter(niveau='5ème année')
    
    # Tableau pour stocker les données de progression
    progression_data = []
    
    for subject in subjects:
        # Modifier la requête pour utiliser la plage de dates sélectionnée
        seances = EmploiTempsOption.objects.filter(
            option__nom=option_selected,
            matiere=subject,
            type_evenement='COURS',
            date__range=[date_debut, date_fin]  # Utiliser les dates du filtre au lieu de today
        )
        
        # Calculer le total des heures réalisées
        heures_realisees = 0
        for seance in seances:
            if seance.heure_debut and seance.heure_fin:
                debut = datetime.combine(seance.date, seance.heure_debut)
                fin = datetime.combine(seance.date, seance.heure_fin)
                duree = (fin - debut).total_seconds() / 3600
                heures_realisees += duree
        
        # Arrondir les heures réalisées à 2 décimales
        heures_realisees = round(heures_realisees, 2)
        
        # Calculer la progression en pourcentage
        if subject.volume_horaire_total > 0:
            progression = min(int((heures_realisees / subject.volume_horaire_total) * 100), 100)
        else:
            progression = 0
            
        progression_data.append({
            'matiere': subject.name,
            'volume_total': subject.volume_horaire_total,
            'heures_realisees': heures_realisees,
            'progression': progression
        })
    
    # Modifier la requête des sessions pour utiliser date__range
    sessions = EmploiTempsOption.objects.filter(
        Q(option__nom=option_selected) &
        (
            Q(date__range=[date_debut, date_fin]) |  # Pour les événements standards
            (
                Q(date_debut__lte=date_fin) &  # Pour les événements multi-jours
                Q(date_fin__gte=date_debut)
            )
        )
    ).select_related('matiere', 'professeur').order_by('date', 'heure_debut')
    
    # Ajouter ceci avant le context
    # Récupérer les sessions pour le planning
    sessions = EmploiTempsOption.objects.filter(
        option__nom=option_selected,
        date__range=[date_debut, date_fin]  # Afficher les 2 prochaines semaines
    ).order_by('date', 'heure_debut')
    
    # Organiser les sessions par date
    sessions_by_date = defaultdict(list)
    for session in sessions:
        sessions_by_date[session.date].append(session)
    
    context = {
        'options': options,
        'option_selected': option_selected,
        'progression_data': progression_data,
        'sessions_by_date': dict(sessions_by_date),  # Ajouter les sessions au contexte
        'page_title': f'Suivi de progression - {option_selected}',
        'date_debut': date_debut,
        'date_fin': date_fin
    }
    
    return render(request, 'hod_template/suivi_progression_options.html', context)



# matieres des options :

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from .models import MatiereOption5eme, Option5eme
from .forms import MatiereOption5emeForm

def ajouter_matiere_option(request):
    if request.method == 'POST':
        form = MatiereOption5emeForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Matière ajoutée avec succès à l'option.")
            return redirect(reverse('ajouter_matiere_option'))  # Rediriger vers la même page
        else:
            messages.error(request, "Erreur lors de l'ajout de la matière.")
    else:
        form = MatiereOption5emeForm()
    context = {
        'form': form,
        'page_title': 'Ajouter une matière à une option (5ème année)'
    }
    return render(request, 'hod_template/ajouter_matiere_option.html', context)


