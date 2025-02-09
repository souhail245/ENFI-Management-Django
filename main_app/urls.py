"""college_management_system URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path
from .student_views import update_fcm_token

from main_app.EditResultView import EditResultView

from . import hod_views, staff_views, student_views, views

urlpatterns = [

    # urls.py  export pdf 
    path('students/export/excel/', hod_views.export_students_excel, name='export_students_excel'),
    path('students/export/pdf/', hod_views.export_students_pdf, name='export_students_pdf'),
   
    path("", views.login_page, name='login_page'),
    path("get_attendance", views.get_attendance, name='get_attendance'),
    path("firebase-messaging-sw.js", views.showFirebaseJS, name='showFirebaseJS'),
    path("doLogin/", views.doLogin, name='user_login'),
    path("logout_user/", views.logout_user, name='user_logout'),
    path("admin/home/", hod_views.admin_home, name='admin_home'),
    path("staff/add", hod_views.add_staff, name='add_staff'),
    path("course/add", hod_views.add_course, name='add_course'),
    path("send_student_notification/", hod_views.send_student_notification,name='send_student_notification'),
    path('send_promotion_notification/', hod_views.send_promotion_notification, name='send_promotion_notification'),
    path("send_staff_notification/", hod_views.send_staff_notification,
         name='send_staff_notification'),
    path("add_session/", hod_views.add_session, name='add_session'),
    path("admin_notify_student", hod_views.admin_notify_student,
         name='admin_notify_student'),
    path("admin_notify_staff", hod_views.admin_notify_staff,
         name='admin_notify_staff'),
    path("admin_view_profile", hod_views.admin_view_profile,
         name='admin_view_profile'),
    path("check_email_availability", hod_views.check_email_availability,
         name="check_email_availability"),
    path("session/manage/", hod_views.manage_session, name='manage_session'),
    path("session/edit/<int:session_id>",
         hod_views.edit_session, name='edit_session'),
    path("student/view/feedback/", hod_views.student_feedback_message,
         name="student_feedback_message",),
    path("staff/view/feedback/", hod_views.staff_feedback_message,
         name="staff_feedback_message",),
    path("student/view/leave/", hod_views.view_student_leave,
         name="view_student_leave",),
    path("staff/view/leave/", hod_views.view_staff_leave, name="view_staff_leave",),
    path("attendance/view/", hod_views.admin_view_attendance,
         name="admin_view_attendance",),
    path("attendance/fetch/", hod_views.get_admin_attendance,
         name='get_admin_attendance'),
    path("student/add/", hod_views.add_student, name='add_student'),
    path("subject/add/", hod_views.add_subject, name='add_subject'),
    path("staff/manage/", hod_views.manage_staff, name='manage_staff'),
    path("student/manage/", hod_views.manage_student, name='manage_student'),
    path("course/manage/", hod_views.manage_course, name='manage_course'),
    path("subject/manage/", hod_views.manage_subject, name='manage_subject'),
    path("staff/edit/<int:staff_id>", hod_views.edit_staff, name='edit_staff'),
    path("staff/delete/<int:staff_id>",
         hod_views.delete_staff, name='delete_staff'),

    path("course/delete/<int:course_id>",
         hod_views.delete_course, name='delete_course'),

    path("subject/delete/<int:subject_id>",
         hod_views.delete_subject, name='delete_subject'),

    path("session/delete/<int:session_id>",
         hod_views.delete_session, name='delete_session'),

    path("student/delete/<int:student_id>",
         hod_views.delete_student, name='delete_student'),
    path("student/edit/<int:student_id>",
         hod_views.edit_student, name='edit_student'),
    path("course/edit/<int:course_id>",
         hod_views.edit_course, name='edit_course'),
    path("subject/edit/<int:subject_id>",
         hod_views.edit_subject, name='edit_subject'),
  
  # gestion d'absensces view_absences
    path('add-absence/', hod_views.add_absence, name='add_absence'),
    path('get_student_details/', hod_views.get_student_details, name='get_student_details'),
    path('view-absences/', hod_views.view_absences, name='view_absences'),

   # export pdf/excel    absences 

    path('export-absences-excel/', hod_views.export_absences_excel, name='export_absences_excel'),
    path('export-absences-pdf/', hod_views.export_absences_pdf, name='export_absences_pdf'),

   # Page pour afficher les emplois du temps
    
    path('emploi/create/', hod_views.creer_emploi_temps, name='creer_emploi_temps'),  # Page pour créer un emploi du temps
    path('emploi/list/', hod_views.liste_emplois, name='liste_emplois'),
    path('emploi/historique/', hod_views.historique_emploi, name='historique_emploi'),


    path('emploi/choisir_promotion/', hod_views.choisir_promotion, name='choisir_promotion'),
    
    path('get_progression_data', hod_views.get_progression_data, name='get_progression_data'),
# emploi Options 
    path('options_5eme/', hod_views.gerer_emploi_temps_options, name='gerer_emploi_temps_options'),
    path('supprimer-evenement-option/<int:evenement_id>/', hod_views.supprimer_evenement_option, name='supprimer_evenement_option'),

    # Staff
    path("staff/home/", staff_views.staff_home, name='staff_home'),
    path("staff/apply/leave/", staff_views.staff_apply_leave,
         name='staff_apply_leave'),
    path("staff/feedback/", staff_views.staff_feedback, name='staff_feedback'),
    path("staff/view/profile/", staff_views.staff_view_profile,
         name='staff_view_profile'),
    path("staff/attendance/take/", staff_views.staff_take_attendance,
         name='staff_take_attendance'),
    path("staff/attendance/update/", staff_views.staff_update_attendance,
         name='staff_update_attendance'),
    path("staff/get_students/", staff_views.get_students, name='get_students'),
    path("staff/attendance/fetch/", staff_views.get_student_attendance,
         name='get_student_attendance'),
    path("staff/attendance/save/",
         staff_views.save_attendance, name='save_attendance'),
    path("staff/attendance/update/",
         staff_views.update_attendance, name='update_attendance'),
    path("staff/fcmtoken/", staff_views.staff_fcmtoken, name='staff_fcmtoken'),
    path("staff/view/notification/", staff_views.staff_view_notification,
         name="staff_view_notification"),
    path("staff/result/add/", staff_views.staff_add_result, name='staff_add_result'),
    path("staff/result/edit/", EditResultView.as_view(),
         name='edit_student_result'),
    path('staff/result/fetch/', staff_views.fetch_student_result,
         name='fetch_student_result'),



    path('staff/notification/delete/', staff_views.delete_staff_notification, name='delete_staff_notification'),


    # Student
    path("student/home/", student_views.student_home, name='student_home'),
    path("student/view/attendance/", student_views.student_view_attendance,
         name='student_view_attendance'),
    path("student/apply/leave/", student_views.student_apply_leave,
         name='student_apply_leave'),
    path("student/feedback/", student_views.student_feedback,
         name='student_feedback'),
    path("student/view/profile/", student_views.student_view_profile,
         name='student_view_profile'),
    path("student/fcmtoken/", student_views.student_fcmtoken,
         name='student_fcmtoken'),
    path("student/view/notification/", student_views.student_view_notification,
         name="student_view_notification"),
    path('student/view/result/', student_views.student_view_result,
         name='student_view_result'),

     path('attestation-scolarite/', student_views.attestation_scolarite, name='attestation_scolarite'),
     # URL pour exporter l'attestation en PDF
     path('export-attestation/<int:student_id>/', student_views.export_attestation_pdf, name='export_attestation_pdf'),

    path('update_fcm_token/', update_fcm_token, name='update_fcm_token'),
    path('student/notification/delete/', student_views.delete_student_notification, name='delete_student_notification'),
    path('get-matieres-by-niveau/', hod_views.get_matieres_by_niveau, name='get_matieres_by_niveau'),
   
      path('emploi-du-temps/', student_views.emploi_du_temps, name='emploi_du_temps'),
    path('supprimer-evenement/<int:evenement_id>/', hod_views.supprimer_evenement, name='supprimer_evenement'),
]
