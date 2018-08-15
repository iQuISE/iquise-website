from django.forms import ModelForm
from .models import Person

class PersonForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(PersonForm, self).__init__(*args, **kwargs)
        self.fields['email'].required = True
    class Meta:
        model=Person
        fields = ['first_name','last_name','email','year','lab']
