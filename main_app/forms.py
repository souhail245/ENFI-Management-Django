import re
from django import forms
from django.forms.widgets import DateInput, TextInput

from .models import *


class FormSettings(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormSettings, self).__init__(*args, **kwargs)
        # Here make some changes such as:
        for field in self.visible_fields():
            field.field.widget.attrs['class'] = 'form-control'


class CustomUserForm(FormSettings):
    email = forms.EmailField(required=True)
    gender = forms.ChoiceField(choices=[('M', 'Male'), ('F', 'Female')])
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)
    address = forms.CharField(widget=forms.Textarea)
    password = forms.CharField(widget=forms.PasswordInput)
    widget = {
        'password': forms.PasswordInput(),
    }
    profile_pic = forms.ImageField()
    phone_number = forms.CharField(max_length=15, required=False, widget=forms.TextInput(attrs={'placeholder': 'Phone number'}))
    def __init__(self, *args, **kwargs):
        super(CustomUserForm, self).__init__(*args, **kwargs)

        if kwargs.get('instance'):
            instance = kwargs.get('instance').admin.__dict__
            self.fields['password'].required = False
            for field in CustomUserForm.Meta.fields:
                self.fields[field].initial = instance.get(field)
            if self.instance.pk is not None:
                self.fields['password'].widget.attrs['placeholder'] = "Fill this only if you wish to update password"

    def clean_email(self, *args, **kwargs):
        formEmail = self.cleaned_data['email'].lower()
        if self.instance.pk is None:  # Insert
            if CustomUser.objects.filter(email=formEmail).exists():
                raise forms.ValidationError(
                    "The given email is already registered")
        else:  # Update
            dbEmail = self.Meta.model.objects.get(
                id=self.instance.pk).admin.email.lower()
            if dbEmail != formEmail:  # There has been changes
                if CustomUser.objects.filter(email=formEmail).exists():
                    raise forms.ValidationError("The given email is already registered")

        return formEmail
    
    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        if phone_number:
            # Exemple de validation pour un format international
            if not re.match(r'^\+?[1-9]\d{1,14}$', phone_number):
                raise forms.ValidationError("Invalid phone number format")
        return phone_number
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'gender', 'phone_number', 'password','profile_pic', 'address' ]


class StudentForm(CustomUserForm):
    def __init__(self, *args, **kwargs):
        super(StudentForm, self).__init__(*args, **kwargs)

    class Meta(CustomUserForm.Meta):
        model = Student
        fields = CustomUserForm.Meta.fields + \
            ['niveau' , 'matricule','lieu', 'dateN']


class AdminForm(CustomUserForm):
    def __init__(self, *args, **kwargs):
        super(AdminForm, self).__init__(*args, **kwargs)

    class Meta(CustomUserForm.Meta):
        model = Admin
        fields = CustomUserForm.Meta.fields


class StaffForm(CustomUserForm):
    def __init__(self, *args, **kwargs):
        super(StaffForm, self).__init__(*args, **kwargs)

    class Meta(CustomUserForm.Meta):
        model = Staff
        fields = CustomUserForm.Meta.fields
            


class CourseForm(FormSettings):
    def __init__(self, *args, **kwargs):
        super(CourseForm, self).__init__(*args, **kwargs)

    class Meta:
        fields = ['name', 'niveau']  # Ajout du champ 'niveau'
        model = Course


class SubjectForm(FormSettings):
    class Meta:
        model = Subject
        fields = ['name', 'staff', 'niveau', 'volume_horaire_total']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'staff': forms.Select(attrs={'class': 'form-control'}),
            'niveau': forms.Select(attrs={'class': 'form-control'}),
            'volume_horaire_total': forms.NumberInput(attrs={'class': 'form-control'})
        }


class SessionForm(FormSettings):
    def __init__(self, *args, **kwargs):
        super(SessionForm, self).__init__(*args, **kwargs)

    class Meta:
        model = Session
        fields = '__all__'
        widgets = {
            'start_year': DateInput(attrs={'type': 'date'}),
            'end_year': DateInput(attrs={'type': 'date'}),
        }


class LeaveReportStaffForm(FormSettings):
    def __init__(self, *args, **kwargs):
        super(LeaveReportStaffForm, self).__init__(*args, **kwargs)

    class Meta:
        model = LeaveReportStaff
        fields = ['date', 'message']
        widgets = {
            'date': DateInput(attrs={'type': 'date'}),
        }


class FeedbackStaffForm(FormSettings):

    def __init__(self, *args, **kwargs):
        super(FeedbackStaffForm, self).__init__(*args, **kwargs)

    class Meta:
        model = FeedbackStaff
        fields = ['feedback']


class LeaveReportStudentForm(FormSettings):
    def __init__(self, *args, **kwargs):
        super(LeaveReportStudentForm, self).__init__(*args, **kwargs)

    class Meta:
        model = LeaveReportStudent
        fields = ['date', 'message']
        widgets = {
            'date': DateInput(attrs={'type': 'date'}),
        }


class FeedbackStudentForm(FormSettings):

    def __init__(self, *args, **kwargs):
        super(FeedbackStudentForm, self).__init__(*args, **kwargs)

    class Meta:
        model = FeedbackStudent
        fields = ['feedback']


class StudentEditForm(CustomUserForm):
    matricule = forms.CharField(max_length=14)  # Ajouter le champ matricule

    def __init__(self, *args, **kwargs):
        super(StudentEditForm, self).__init__(*args, **kwargs)
        
        # Réorganiser l'ordre des champs dans le formulaire
        fields_order = ['first_name', 'last_name', 'matricule', 'email', 'gender', 'phone_number', 'password', 'profile_pic', 'address']
        self.fields = {field: self.fields[field] for field in fields_order}  # Redéfinir l'ordre des champs

    class Meta(CustomUserForm.Meta):
        model = Student
        fields = ['first_name', 'last_name', 'matricule', 'email', 'gender', 'phone_number', 'password', 'profile_pic', 'address']



class StaffEditForm(CustomUserForm):
    def __init__(self, *args, **kwargs):
        super(StaffEditForm, self).__init__(*args, **kwargs)

    class Meta(CustomUserForm.Meta):
        model = Staff
        fields = CustomUserForm.Meta.fields


class EditResultForm(FormSettings):
    session_list = Session.objects.all()
    session_year = forms.ModelChoiceField(
        label="Session Year", queryset=session_list, required=True)

    def __init__(self, *args, **kwargs):
        super(EditResultForm, self).__init__(*args, **kwargs)

    class Meta:
        model = StudentResult
        fields = ['session_year', 'subject', 'student', 'test', 'exam']

class AbsenceForm(forms.ModelForm):
    matricule = forms.CharField(
        max_length=20, 
        widget=forms.TextInput(attrs={
            'class': 'form-control', 
            'placeholder': 'Saisir le matricule de l\'étudiant'
        })
    )

    class Meta:
        model = Absence
        fields = ['matricule', 'student', 'subject', 'staff', 'date', 'time_from', 'time_to', 'reason']
        widgets = {
            'student': forms.Select(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'subject': forms.Select(attrs={'class': 'form-control'}),
            'staff': forms.Select(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'time_from': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'time_to': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }