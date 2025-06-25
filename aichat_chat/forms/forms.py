from .custom_fields import *
import decimal
from django import forms
from django.core.exceptions import ValidationError
from django.forms import modelformset_factory
from django.utils.translation import gettext_lazy as _
from ..models import RagSource

__all__ = ['InputForm', 'RagDocForm', 'RagUrlForm', 'RagUrlFormSet']

#------------------------------------------------------------------------

# Uses standard django CharField
class InputForm(forms.Form):
    user_input = forms.CharField( 
        max_length=4096,
        widget=forms.Textarea(attrs={
            'autofocus': True,
            'rows': 2,
            'autocomplete': 'off',
            'class': 'form-control border border-2 border-secondary',
            'placeholder': _('ask your question here'),
        })
    )
    first_name = forms.CharField(widget=forms.HiddenInput()) # Included so it can be accessible to the JS via FormData
    timestamp = forms.CharField(widget=forms.HiddenInput()) # Included so it can be accessible to the JS via FormData

    def __init__(self, *args, **kwargs):
        super(InputForm, self).__init__(*args, **kwargs)
        # Set required=True for all fields in this form
        for field_name in self.fields:
            self.fields[field_name].required = True

    def clean(self):
        cleaned_data = super().clean() # Use of super().clean() allows Django's built-in validation to happen first, and then the additional custom validation below is applied to that cleaned data.
        user_input = cleaned_data.get("user_input")
        first_name = cleaned_data.get("first_name")
        timestamp = cleaned_data.get("timestamp")
        
        return cleaned_data


#---------------------------------------------------------------------------


# This form holds the URL records in aichat_source, allowing the page to be populated with those records
# on page load and allowing the user to update those records by submitting the form
class RagUrlForm(forms.ModelForm):
    class Meta:
        model = RagSource
        fields = ['source', 'include_subdomains', 'type']  # Specify the fields you want in the form
        widgets = {
            'source': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': _('Enter full URL') +'. '+ _('Example') +': https://www.mattmcdonnell.net)'
            }),
            'include_subdomains': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'type': forms.HiddenInput()  # Make 'type' a hidden field
        }

    def __init__(self, *args, **kwargs):
        super(RagUrlForm, self).__init__(*args, **kwargs)
        self.fields['source'].label = "URL"
        self.fields['include_subdomains'].label = _("Include subdomains")
        self.initial['type'] = 'website' # Ensures the 'type' field is always set to 'website'

# Create a ModelFormSet for the RagSource model
# Since we could have multiple urls assocaited with a given user, that will generate a RagUrlForm for each url
# The use of the formset allows us to manage the data associated with all those instances of RagUrlForm as if it was a single form.
RagUrlFormSet = modelformset_factory(
    RagSource,
    form=RagUrlForm,
    extra=1,  # This will show 1 additional empty record on top of those records in the DB (used to allow users to add a url)
    can_delete=True  # This allows users to mark forms for deletion
)


#-------------------------------------------------------------------------

class RagDocForm(forms.ModelForm):  # Use forms.Form instead of ModelForm
    class Meta:
        model = RagSource
        fields = ['file_path', 'type']
        widgets = {
            'file_path': forms.ClearableFileInput(attrs={'allow_multiple_selected': True
            }),
            'type': forms.HiddenInput()
        }

    def __init__(self, *args, **kwargs):
        super(RagDocForm, self).__init__(*args, **kwargs)
        self.initial['type'] = 'document' # Ensures the 'type' field is always set to 'document'

    
    # Custom validation to allow only certain file types
    def clean_file_path(self):
        files = self.files.getlist('file_path')
        allowed_extensions = ['.pdf', '.txt', '.docx']
        for file in files:
            if not any(file.name.endswith(ext) for ext in allowed_extensions):
                raise forms.ValidationError(f"{file.name} has an invalid file type.")
        return files

