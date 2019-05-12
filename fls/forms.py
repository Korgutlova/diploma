from django import forms

from fls.models import Competition, CustomUser


class CompetitionForm(forms.ModelForm):
    jurys = forms.ModelMultipleChoiceField(queryset=CustomUser.objects.filter(role=2), label="Жюри конкурса", required=False)

    class Meta:
        model = Competition
        fields = ['name', 'description', 'method_of_estimate', 'max_for_criteria', 'jurys']

    def clean_name(self):
        name = self.cleaned_data['name']
        if len(name) < 5:
            raise forms.ValidationError("Название конкурса должно быть длиннее 5 символов")
        return name
