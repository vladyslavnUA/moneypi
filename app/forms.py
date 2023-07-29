from django import forms
from .models import Employee

class ClockInForm(forms.Form):
    employee = forms.ModelChoiceField(queryset=Employee.objects.all())
    auto_clock_in_out = forms.BooleanField(required=False)
    latitude = forms.FloatField()
    longitude = forms.FloatField()

class ClockOutForm(forms.Form):
    employee = forms.ModelChoiceField(queryset=Employee.objects.all())
    auto_clock_in_out = forms.BooleanField(required=False)
    latitude = forms.FloatField()
    longitude = forms.FloatField()