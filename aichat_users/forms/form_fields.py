from .custom_fields import *
import decimal
from django import forms
from django.core.exceptions import ValidationError
from aichat_chat.helpers import *
from translations.helpers.translate import supported_languages_selected
from django.utils.translation import gettext_lazy as _

__all__ = ['chat_history_window', 'chunk_size', 'chunk_overlap', 'CustomDecimalField', 'data_source', 'email', 'expert_speaks_my_lang', 'experts_suggested_number', 'first_name','last_name', 'langchain_k', 'password', 'password_confirmation', 'password_old', 'preferred_language', 'preprocessing', 'preprocessing_model', 'rag_sources_shown', 'rag_sources_used', 'response_length', 'retriever_model', 'similarity_metric', 'temperature', 'tokenization_and_vectorization_model', 'top_p', 'suggest_experts', 'user_employer', 'username', 'username_old', 'weight_years', 'weight_industry', 'weight_role', 'weight_topic', 'weight_geography',]

class CustomDecimalField(forms.DecimalField):
    def to_python(self, value):

        # Handle None and empty values
        if value is None or value == '':
            return None
            
        # Convert to string if it's not already
        if not isinstance(value, str):
            value = str(value)

        try:
            # Attempt to convert comma-separated strings to Python decimal
            return decimal.Decimal(value.replace(',', ''))
        except decimal.InvalidOperation:
            raise ValidationError(_('Enter a valid number.'))

class USDTextInput(forms.TextInput):
    def format_value(self, value):
        # Check if the value is a Decimal instance and format it
        if isinstance(value, decimal.Decimal):
            return f"${value:,.2f}"
        return value  # Return the original value if it's not a Decimal instance


chat_history_window = forms.IntegerField(
    label=_('Chat history window') + ':',
    min_value=0,
    max_value=20,
    required=False,
    widget=forms.NumberInput(attrs={
        'type': 'range',
        'min': '0',
        'max': '20',
        'step': "1",
        'class': 'form-range',
        'id': 'chat-history-window',
        'form-element': 'profileForm',
    })
)


chunk_size = forms.IntegerField(
    label=_('Chunk size (characters)') + ':',
    min_value=100,
    max_value=3000,
    required=False,
    widget=forms.NumberInput(attrs={
        'type': 'range',
        'min': '100',
        'max': '3000',
        'step': "100",
        'class': 'form-range',
        'id': 'chunk-size',
        'form-element': 'profileForm',
    })
)

chunk_overlap = forms.DecimalField(
    label=_('Chunk overlap (% chunk size)') + ':',
    min_value=0.05,
    max_value=0.40,
    required=False,
    widget=forms.NumberInput(attrs={
        'type': 'range',
        'min': '0.05',
        'max': '0.40',
        'step': "0.05",
        'class': 'form-range',
        'id': 'chunk-overlap',
        'form-element': 'profileForm',
    })
)


data_source = forms.ChoiceField(
    label=_('Preferred chat resources') + ':',
    choices=[
        ('rag', _('Uploaded materials only')),
        ('hist_rag', _('Uploaded materials + chat history')),
        ('hist_rag_web', _('Uploaded materials, chat history, and internet')),
    ],
    required=False,
    widget=forms.RadioSelect(attrs={
        'class': 'form-check-input',
        'form-element': 'profileForm'
    })
)


email = EmailFieldLowerRegexStrict(
    label=_('Email address') + ':',
    max_length=100,
    widget=forms.EmailInput(attrs={
        'autocomplete': 'off',
        'class': 'form-control',
        'id': 'email',
    })
)


user_employer = forms.ChoiceField(
    label=_('Employer'),
    choices=[
        ('', _('Select your employer')),  # Placeholder option with an empty value
        ('Kebayoran_Technologies', 'Kebayoran Technologies'),
        ('test_user_general', 'Test user - general'),
        ('test_user_arches', 'Test user - Arches'),
        ('test_user_dialectica', 'Test user - Dialectica'),
        ('test_user_bcc', 'Test user - BCC'),
        ('test_user_ihc', 'Test user - IHC'),
        ('test_user_other', 'Test user - other'),
    ],
    required=True,  # Ensures the field is mandatory
    widget=forms.Select(attrs={
        'class': 'form-select',
    }),
    initial='',  # Set the initial to the placeholder option
)


expert_speaks_my_lang = forms.BooleanField(
    label=_('Only recommend experts fluent in my language'),
    required=False,
    widget=forms.CheckboxInput(attrs={
        'class': 'form-check-input',
        'id': 'expert_speaks_my_lang_checkbox',
        'form-element': 'profileForm',
    })
)


experts_suggested_number = forms.IntegerField(
    label=_('Experts suggested') + ':',
    min_value=0,
    max_value=6,
    required=False,
    widget=forms.NumberInput(attrs={
        'type': 'range',
        'min': '0',
        'max': '6',
        'class': 'form-range',
        'name': 'number-of-experts',
        'id': 'number-of-experts',
        'form-element': 'profileForm',
    })
)


first_name = CharFieldRegexStrict(
    label=_('First name') + ':',
    required=False,
    max_length=100,
    widget=forms.TextInput(attrs={
        'autocomplete': 'off',
        'class': 'form-control',
    })
)


last_name = CharFieldRegexStrict(
    label=_('Last name') + ':',
    required=False,
    max_length=100,
    widget=forms.TextInput(attrs={
        'autocomplete': 'off',
        'class': 'form-control',
    })
)


langchain_k = forms.IntegerField(
    label=_('LangChain k') + ':',
    min_value=0,
    max_value=20,
    required=False,
    widget=forms.NumberInput(attrs={
        'type': 'range',
        'min': '1',
        'max': '20',
        'class': 'form-range',
        'id': 'langchain-k',
        'form-element': 'profileForm',
    })
)


password = forms.CharField(
    label=_('Password') + ':',
    max_length=50,
    strip=True,
    widget=forms.PasswordInput(attrs={
        'autocomplete': 'off',
        'class': 'form-control',
        'id': 'password',
    })
)


password_confirmation = forms.CharField(
    label=_('Password confirmation') + ':',
    max_length=50,
    strip=True,
    widget=forms.PasswordInput(attrs={
        'autocomplete': 'off',
        'class': 'form-control',
        'id': 'password_confirmation',
    })
)


password_old = forms.CharField(
    label=_('Current password') + ':',
    max_length=50,
    strip=True,
    widget=forms.PasswordInput(attrs={
        'autocomplete': 'off',
        'class': 'form-control',
        'id': 'password_old'
    })
)


preferred_language = forms.ChoiceField(
    label=_('Language') + ':',
    choices=[(code, data['name']) for code, data in supported_languages_selected.items()],
    required=False,
    widget=forms.Select(attrs={
        'class': 'select-custom',
        'form-element': 'profileForm',
    })
)



preprocessing = forms.BooleanField(
    label=_('Preprocessing'),
    required=False,
    widget=forms.CheckboxInput(attrs={
        'class': 'form-check-input',
        'role': 'switch',
        'id': 'preprocessing',
        'form-element': 'profileForm',
    })
)



preprocessing_model = forms.ChoiceField(
    label=_('Text preprocessing model') + ':',
    choices=[
        ('auto-detect', _('Auto-detect'))  # Prepend the Auto-detect option
    ] + [
        (code, data['model_name']) for code, data in preprocessing_models_supported.items()
    ],
    required=False,
    widget=forms.Select(attrs={
        'class': 'select-custom form-select-sm',
        'form-element': 'profileForm',
    })
)



rag_sources_shown = forms.ChoiceField(
    label=_('Sources for data upload made available to user') + ':',
    choices=[
        ('document', _('Documents')),
        ('website', _('Websites')),
        ('all', _('All')),
        ('none', _('None'))
    ],
    required=False,
    widget=forms.RadioSelect(attrs={
        'class': 'form-check-input',
        'form-element': 'profileForm',
    })
)


rag_sources_used = forms.ChoiceField(
    label=_('Data types used in response') + ':',
    choices=[
        ('document', _('Documents')),
        ('website', _('Websites')),
        ('all', _('All')),
    ],
    required=False,
    widget=forms.RadioSelect(attrs={
        'class': 'form-check-input',
        'form-element': 'profileForm',
    })
)


response_length = forms.IntegerField(
    label=_('Maximum response length (sentences)') + ':',
    min_value=0,
    max_value=10,
    required=False,
    widget=forms.NumberInput(attrs={
        'type': 'range',
        'min': '0',
        'max': '10',
        'class': 'form-range',
        'id': 'response-length',
        'form-element': 'profileForm',
    })
)



retriever_model = forms.ChoiceField(
    label=_('Retriever model') + ':',
    choices=[(code, data['model_name']) for code, data in retriever_models_supported.items()],
    required=False,
    widget=forms.Select(attrs={
        'class': 'select-custom form-select-sm',
        'form-element': 'profileForm',
    })
)



similarity_metric = forms.ChoiceField(
    label=_('Index similarity metric') + ':',
    choices=[(code, data['metric']) for code, data in similarity_metric.items()],
    required=False,
    widget=forms.Select(attrs={
        'class': 'select-custom form-select-sm',
        'form-element': 'profileForm',
    })
)



suggest_experts = forms.BooleanField(
    label=_('Suggest experts'),
    required=False,
    widget=forms.CheckboxInput(attrs={
        'class': 'form-check-input',
        'role': 'switch',
        'id': 'suggestExpertsSwitch',
        'form-element': 'profileForm',
    })
)



temperature = forms.DecimalField(
    label=_('Response creativity (temperature)') + ':',
    min_value=0,
    max_value=1,
    required=False,
    widget=forms.NumberInput(attrs={
        'type': 'range',
        'min': '0',
        'max': '1',
        'step': "0.1",  # Ensure fractional steps
        'class': 'form-range',
        'id': 'response-temperature',
        'form-element': 'profileForm',
    })
)



tokenization_and_vectorization_model = forms.ChoiceField(
    label=_('Tokenization and vectorization model') + ':',
    choices=[(code, data['model_name']) for code, data in tokenization_and_vectorization_models_supported.items()],
    required=False,
    widget=forms.Select(attrs={
        'class': 'select-custom form-select-sm',
        'form-element': 'profileForm',
    })
)


top_p = forms.DecimalField(
    label=_('top_p') + ':',
    min_value=0,
    max_value=1,
    required=False,
    widget=forms.NumberInput(attrs={
        'type': 'range',
        'min': '0',
        'max': '1',
        'step': "0.1",
        'class': 'form-range',
        'id': 'top-p',
        'form-element': 'profileForm',
    })
)


username = CharFieldRegexStrict(
    label=_('Username') + ':',
    max_length=25,
    required=False,  # Makes the field optional
    strip=True,
    widget=forms.TextInput(attrs={
        'autocomplete': 'off',
        'class': 'form-control',
    })
)


username_old = CharFieldRegexStrict(
    label=_('Old username') + ':',
    max_length=25,
    required=False,  # Makes the field optional
    strip=True,
    widget=forms.TextInput(attrs={
        'autocomplete': 'off',
        'class': 'form-control',
    })
)


weight_geography = forms.IntegerField(
    label=_('Geography') + ':',
    min_value=0,
    max_value=10,
    required=False,
    widget=forms.NumberInput(attrs={
        'type': 'range',
        'min': '0',
        'max': '10',
        'class': 'form-range',
        'id': 'recommendation-weight-geography',
        'form-element': 'profileForm',
    })
)




weight_industry = forms.IntegerField(
    label=_('Industry') + ':',
    min_value=0,
    max_value=10,
    required=False,
    widget=forms.NumberInput(attrs={
        'type': 'range',
        'min': '0',
        'max': '10',
        'class': 'form-range',
        'id': 'recommendation-weight-industry',
        'form-element': 'profileForm',
    })
)


weight_role = forms.IntegerField(
    label=_('Role') + ':',
    min_value=0,
    max_value=10,
    required=False,
    widget=forms.NumberInput(attrs={
        'type': 'range',
        'min': '0',
        'max': '10',
        'class': 'form-range',
        'id': 'recommendation-weight-role',
        'form-element': 'profileForm',
    })
)


weight_topic = forms.IntegerField(
    label=_('Topic') + ':',
    min_value=0,
    max_value=10,
    required=False,
    widget=forms.NumberInput(attrs={
        'type': 'range',
        'min': '0',
        'max': '10',
        'class': 'form-range',
        'id': 'recommendation-weight-topic',
        'form-element': 'profileForm',
    })
)



weight_years = forms.IntegerField(
    label=_('Years of experience') + ':',
    min_value=0,
    max_value=10,
    required=False,
    widget=forms.NumberInput(attrs={
        'type': 'range',
        'min': '0',
        'max': '10',
        'class': 'form-range',
        'id': 'recommendation-weight-years',
        'form-element': 'profileForm',
    })
)


