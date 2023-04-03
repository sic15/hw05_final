from django import forms


class PassChange(forms.ModelForm):
    class Meta:
        fields = ('current_pass', 'new_pass', 'new_pass_2')
