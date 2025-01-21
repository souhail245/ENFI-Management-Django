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


from .forms import *
from .models import *

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
    if matricule:
        absences = absences.filter(student__matricule__icontains=matricule)
    
    if date_debut:
        absences = absences.filter(date__gte=date_debut)
    
    if date_fin:
        absences = absences.filter(date__lte=date_fin)
    
    if niveau:
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
from django.http import HttpResponse
import xlsxwriter
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle

def export_absences_excel(request):
    # Récupérer les absences filtrées
    absences = Absence.objects.select_related('student', 'subject')
    
    # Appliquer les mêmes filtres que dans la vue principale
    matricule = request.GET.get('matricule')
    date_debut = request.GET.get('date_debut')
    date_fin = request.GET.get('date_fin')
    niveau = request.GET.get('niveau')

    if matricule:
        absences = absences.filter(student__matricule__icontains=matricule)
    if date_debut:
        absences = absences.filter(date__gte=date_debut)
    if date_fin:
        absences = absences.filter(date__lte=date_fin)
    if niveau:
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

    if matricule:
        absences = absences.filter(student__matricule__icontains=matricule)
    if date_debut:
        absences = absences.filter(date__gte=date_debut)
    if date_fin:
        absences = absences.filter(date__lte=date_fin)
    if niveau:
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
    if selected_niveau:
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
    if selected_niveau:
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
    

def admin_home(request):
    total_staff = Staff.objects.all().count()
    total_students = Student.objects.all().count()
    subjects = Subject.objects.all()
    total_subject = subjects.count()
    total_course = Course.objects.all().count()
    attendance_list = Attendance.objects.filter(subject__in=subjects)
    total_attendance = attendance_list.count()
    attendance_list = []
    subject_list = []
    for subject in subjects:
        attendance_count = Attendance.objects.filter(subject=subject).count()
        subject_list.append(subject.name[:7])
        attendance_list.append(attendance_count)

    # Total Subjects and students in Each Course
    course_all = Course.objects.all()
    course_name_list = []
    subject_count_list = []
    student_count_list_in_course = []

    for course in course_all:
        subjects = Subject.objects.filter(course_id=course.id).count()
        students = Student.objects.filter(course_id=course.id).count()
        course_name_list.append(course.name)
        subject_count_list.append(subjects)
        student_count_list_in_course.append(students)
    
    subject_all = Subject.objects.all()
    subject_list = []
    student_count_list_in_subject = []
    
    for subject in subject_all:
        course = Course.objects.get(id=subject.course.id)
        student_count = Student.objects.filter(course_id=course.id).count()
        subject_list.append(subject.name)
        student_count_list_in_subject.append(student_count)


    # For Students
    student_attendance_present_list=[]
    student_attendance_leave_list=[]
    student_name_list=[]

    students = Student.objects.all()
    for student in students:
        
        attendance = AttendanceReport.objects.filter(student_id=student.id, status=True).count()
        absent = AttendanceReport.objects.filter(student_id=student.id, status=False).count()
        leave = LeaveReportStudent.objects.filter(student_id=student.id, status=1).count()
        student_attendance_present_list.append(attendance)
        student_attendance_leave_list.append(leave+absent)
        student_name_list.append(student.admin.first_name)

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
        "student_count_list_in_subject": student_count_list_in_subject,
        "student_count_list_in_course": student_count_list_in_course,
        "course_name_list": course_name_list,

    }
    return render(request, 'hod_template/home_content.html', context)


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
    context = {
        'form': form,
        'page_title': 'Add Subject'
    }
    if request.method == 'POST':
        if form.is_valid():
            name = form.cleaned_data.get('name')
            course = form.cleaned_data.get('course')
            staff = form.cleaned_data.get('staff')
            niveau = form.cleaned_data.get('niveau')  # Récupérer le niveau
            try:
                subject = Subject()
                subject.name = name
                subject.staff = staff
                subject.course = course
                subject.niveau = niveau  # Ajouter le niveau
                subject.save()
                messages.success(request, "Successfully Added")
                return redirect(reverse('add_subject'))

            except Exception as e:
                messages.error(request, "Could Not Add " + str(e))
        else:
            messages.error(request, "Fill Form Properly")

    return render(request, 'hod_template/add_subject_template.html', context)


def manage_staff(request):
    allStaff = CustomUser.objects.filter(user_type=2)
    context = {
        'allStaff': allStaff,
        'page_title': 'Manage Staff'
    }
    return render(request, "hod_template/manage_staff.html", context)


def manage_student(request):
    # Récupérer tous les niveaux uniques
    niveaux = CustomUser.objects.filter(user_type=3).select_related('student').values_list('student__niveau', flat=True).distinct()
    
    # Récupérer le niveau sélectionné
    selected_niveau = request.GET.get('niveau')
    
    # Query de base
    students = CustomUser.objects.filter(user_type=3).select_related('student')
    
    # Appliquer le filtre si un niveau est sélectionné
    if selected_niveau:
        students = students.filter(student__niveau=selected_niveau)
    
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
    # Récupérer tous les sujets
    subjects = Subject.objects.all()

    # Regrouper les sujets par niveau
    niveaux = Subject._meta.get_field('niveau').choices  # Récupérer les choix de niveau
    sujets_par_niveau = {}

    for niveau in niveaux:
        sujets = Subject.objects.filter(niveau=niveau[0])  # Filtrer les sujets par niveau
        sujets_par_niveau[niveau[1]] = sujets  # Stocker les sujets dans un dictionnaire

    context = {
        'sujets_par_niveau': sujets_par_niveau,  # Passer les sujets groupés par niveau
        'page_title': 'Manage Subjects'
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
            name = form.cleaned_data.get('name')
            course = form.cleaned_data.get('course')
            staff = form.cleaned_data.get('staff')
            try:
                subject = Subject.objects.get(id=subject_id)
                subject.name = name
                subject.staff = staff
                subject.course = course
                subject.save()
                messages.success(request, "Successfully Updated")
                return redirect(reverse('edit_subject', args=[subject_id]))
            except Exception as e:
                messages.error(request, "Could Not Add " + str(e))
        else:
            messages.error(request, "Fill Form Properly")
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
        if user:
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
    if request.method != 'POST':
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
    id = request.POST.get('id')
    message = request.POST.get('message')
    staff = get_object_or_404(Staff, admin_id=id)
    try:
        url = "https://fcm.googleapis.com/fcm/send"
        body = {
            'notification': {
                'title': "Student Management System",
                'body': message,
                'click_action': reverse('staff_view_notification'),
                'icon': static('dist/img/AdminLTELogo.png')
            },
            'to': staff.admin.fcm_token
        }
        headers = {'Authorization':
                   'key=AAAA3Bm8j_M:APA91bElZlOLetwV696SoEtgzpJr2qbxBfxVBfDWFiopBWzfCfzQp2nRyC7_A2mlukZEHV4g1AmyC6P_HonvSkY2YyliKt5tT3fe_1lrKod2Daigzhb2xnYQMxUWjCAIQcUexAMPZePB',
                   'Content-Type': 'application/json'}
        data = requests.post(url, data=json.dumps(body), headers=headers)
        notification = NotificationStaff(staff=staff, message=message)
        notification.save()
        return HttpResponse("True")
    except Exception as e:
        return HttpResponse("False")


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


