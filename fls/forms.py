from django import forms

from fls.models import Competition


class CompetitionForm(forms.ModelForm):
    class Meta:
        model = Competition
        fields = ['name',  'description', 'method_of_estimate', 'type_comp']

    def clean_name(self):
        name = self.cleaned_data['name']
        if len(name) < 5:
            raise forms.ValidationError("Название конкурса должно быть длиннее 5 символов")
        return name
