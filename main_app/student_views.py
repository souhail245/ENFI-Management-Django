import json
import math
from datetime import datetime
import os
from django.conf import settings

from django.contrib import messages
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse, JsonResponse
from django.shortcuts import (HttpResponseRedirect, get_object_or_404,
                              redirect, render)
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from .forms import *
from .models import *



from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from io import BytesIO
from .models import Student

def attestation_scolarite(request):
    # Récupérer les informations de l'étudiant connecté
    student = request.user.student  # Adaptez selon votre modèle d'authentification
    context = {
        'student': student
        
    }
    return render(request, 'student_template/attestation_scolarite.html', context)

def export_attestation_pdf(request, student_id):
    # Récupérer l'étudiant
    student = get_object_or_404(Student, id=student_id)
    
    # Charger le template
    template = get_template('student_template/attestation_pdf_template.html')
    context = {
        'student': student,
        'date': datetime.now()  
       
    }
    
    # Rendre le template HTML
    html = template.render(context)
    
    # Créer le PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="attestation_{student.admin.last_name}.pdf"'
    
    # Générer le PDF
    pdf = pisa.CreatePDF(
        html,
        dest=response,
    )
    
    if not pdf.err:
        return response
    return HttpResponse('Une erreur est survenue lors de la génération du PDF')

def student_home(request):
    student = get_object_or_404(Student, admin=request.user)
    total_subject = Subject.objects.filter(niveau=student.niveau).count()
    subject_name = []
    data_present = []
    data_absent = []
    subjects = Subject.objects.filter(niveau=student.niveau)
    for subject in subjects:
        attendance = Attendance.objects.filter(subject=subject)
        present_count = AttendanceReport.objects.filter(
            attendance__in=attendance, status=True, student=student).count()
        absent_count = AttendanceReport.objects.filter(
            attendance__in=attendance, status=False, student=student).count()
        subject_name.append(subject.name)
        data_present.append(present_count)
        data_absent.append(absent_count)
    context = {
        
        
        'total_subject': total_subject,
        'subjects': subjects,
        'data_present': data_present,
        'data_absent': data_absent,
        'data_name': subject_name,
        'page_title': 'Acceuil : '

    }
    return render(request, 'student_template/home_content.html', context)



@ csrf_exempt
def student_view_attendance(request):
    student = get_object_or_404(Student, admin=request.user)
    if request.method != 'POST':
        course = get_object_or_404(Course, id=student.course.id)
        context = {
            'subjects': Subject.objects.filter(course=course),
            'page_title': 'View Attendance'
        }
        return render(request, 'student_template/student_view_attendance.html', context)
    else:
        subject_id = request.POST.get('subject')
        start = request.POST.get('start_date')
        end = request.POST.get('end_date')
        try:
            subject = get_object_or_404(Subject, id=subject_id)
            start_date = datetime.strptime(start, "%Y-%m-%d")
            end_date = datetime.strptime(end, "%Y-%m-%d")
            attendance = Attendance.objects.filter(
                date__range=(start_date, end_date), subject=subject)
            attendance_reports = AttendanceReport.objects.filter(
                attendance__in=attendance, student=student)
            json_data = []
            for report in attendance_reports:
                data = {
                    "date":  str(report.attendance.date),
                    "status": report.status
                }
                json_data.append(data)
            return JsonResponse(json.dumps(json_data), safe=False)
        except Exception as e:
            return None


def student_apply_leave(request):
    form = LeaveReportStudentForm(request.POST or None)
    student = get_object_or_404(Student, admin_id=request.user.id)
    context = {
        'form': form,
        'leave_history': LeaveReportStudent.objects.filter(student=student),
        'page_title': 'Apply for leave'
    }
    if request.method == 'POST':
        if form.is_valid():
            try:
                obj = form.save(commit=False)
                obj.student = student
                obj.save()
                messages.success(
                    request, "Application for leave has been submitted for review")
                return redirect(reverse('student_apply_leave'))
            except Exception:
                messages.error(request, "Could not submit")
        else:
            messages.error(request, "Form has errors!")
    return render(request, "student_template/student_apply_leave.html", context)


def student_feedback(request):
    form = FeedbackStudentForm(request.POST or None)
    student = get_object_or_404(Student, admin_id=request.user.id)
    context = {
        'form': form,
        'feedbacks': FeedbackStudent.objects.filter(student=student),
        'page_title': 'Student Feedback'

    }
    if request.method == 'POST':
        if form.is_valid():
            try:
                obj = form.save(commit=False)
                obj.student = student
                obj.save()
                messages.success(
                    request, "Feedback submitted for review")
                return redirect(reverse('student_feedback'))
            except Exception:
                messages.error(request, "Could not Submit!")
        else:
            messages.error(request, "Form has errors!")
    return render(request, "student_template/student_feedback.html", context)


def student_view_profile(request):
    student = get_object_or_404(Student, admin=request.user)
    form = StudentEditForm(request.POST or None, request.FILES or None,
                           instance=student)
    context = {'form': form,
               'page_title': 'View/Edit Profile'
               }
    if request.method == 'POST':
        try:
            if form.is_valid():
                first_name = form.cleaned_data.get('first_name')
                last_name = form.cleaned_data.get('last_name')
                password = form.cleaned_data.get('password') or None
                address = form.cleaned_data.get('address')
                gender = form.cleaned_data.get('gender')
                phone_number = form.cleaned_data.get('phone_number') 
                passport = request.FILES.get('profile_pic') or None
                admin = student.admin
                if password != None:
                    admin.set_password(password)
                if passport != None:
                    fs = FileSystemStorage()
                    filename = fs.save(passport.name, passport)
                    passport_url = fs.url(filename)
                    admin.profile_pic = passport_url
                admin.first_name = first_name
                admin.last_name = last_name
                admin.address = address
                admin.gender = gender
                admin.save()
                student.phone_number = phone_number
                student.save()
                messages.success(request, "Profile Updated!")
                return redirect(reverse('student_view_profile'))
            else:
                messages.error(request, "Invalid Data Provided")
        except Exception as e:
            messages.error(request, "Error Occured While Updating Profile " + str(e))

    return render(request, "student_template/student_view_profile.html", context)


@csrf_exempt
def student_fcmtoken(request):
    token = request.POST.get('token')
    student_user = get_object_or_404(CustomUser, id=request.user.id)
    try:
        student_user.fcm_token = token
        student_user.save()
        return HttpResponse("True")
    except Exception as e:
        return HttpResponse("False")


def student_view_notification(request):
    student = get_object_or_404(Student, admin=request.user)
    notifications = NotificationStudent.objects.filter(student=student)
    context = {
        'notifications': notifications,
        'page_title': "View Notifications"
    }
    return render(request, "student_template/student_view_notification.html", context)


def student_view_result(request):
    student = get_object_or_404(Student, admin=request.user)
    results = StudentResult.objects.filter(student=student)
    context = {
        'results': results,
        'page_title': "View Results"
    }
    return render(request, "student_template/student_view_result.html", context)

from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from .models import CustomUser

@csrf_exempt
def update_fcm_token(request):
    if request.method == 'POST':
        token = request.POST.get('token')
        if token and request.user.is_authenticated:
            user = CustomUser.objects.get(id=request.user.id)
            user.update_fcm_token(token)
            return JsonResponse({'success': True, 'message': 'Token FCM mis à jour avec succès.'})
        return JsonResponse({'success': False, 'message': 'Token ou utilisateur non valide.'})
    return JsonResponse({'success': False, 'message': 'Méthode non autorisée.'})

@csrf_exempt
def delete_student_notification(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Méthode non autorisée'})
    
    try:
        data = json.loads(request.body)
        notification_id = data.get('notification_id')
        
        if not notification_id:
            return JsonResponse({'success': False, 'error': 'ID de notification manquant'})

        notification = NotificationStudent.objects.get(id=notification_id)
        
        # Vérifier que la notification appartient bien à l'étudiant connecté
        if notification.student.admin != request.user:
            return JsonResponse({'success': False, 'error': 'Non autorisé'})
            
        # Supprimer le fichier associé s'il existe
        if notification.file:
            file_path = os.path.join(settings.MEDIA_ROOT, str(notification.file))
            if os.path.exists(file_path):
                os.remove(file_path)
        
        notification.delete()
        return JsonResponse({'success': True})
        
    except NotificationStudent.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Notification non trouvée'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})




from django.shortcuts import render
from datetime import date, timedelta
from .models import EmploiTemps

def emploi_du_temps(request):
    # Niveau sélectionné
    promotions = ['3ème année', '4ème année', '5ème année']  # Ajoutez d'autres niveaux si nécessaire
    promotion_selected = request.GET.get('promotion', promotions[0])  # Valeur par défaut : '3ème année'

    # Dates sélectionnées
    date_debut = request.GET.get('date_debut', date.today())
    date_fin = request.GET.get('date_fin', date.today() + timedelta(days=14))

    # Récupérer les données
    emplois = EmploiTemps.objects.filter(
        niveau=promotion_selected,
        date__range=[date_debut, date_fin]
    ).order_by('date', 'horaire')

    # Organiser les données par date et horaire pour le tableau
    sessions_by_date = {}
    horaires = ['08:00-10:00', '10:00-12:00', '14:00-16:00', '16:00-18:00']
    dates = [date.fromordinal(d) for d in range(date.fromisoformat(str(date_debut)).toordinal(),
                                                date.fromisoformat(str(date_fin)).toordinal() + 1)]

    for emploi in emplois:
        if emploi.date not in sessions_by_date:
            sessions_by_date[emploi.date] = {}
        sessions_by_date[emploi.date][emploi.horaire] = emploi

    context = {
        'page_title': 'Emploi du Temps',
        'promotions': promotions,
        'promotion_selected': promotion_selected,
        'horaires': horaires,
        'dates': dates,
        'sessions_by_date': sessions_by_date,
    }

    return render(request, 'student_template/emploi_du_temps.html', context)
