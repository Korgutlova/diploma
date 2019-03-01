from django import forms

from fls.models import Competition


class CompetitionForm(forms.ModelForm):
    class Meta:
        model = Competition
        fields = ['name', 'year_of_study', 'description']
