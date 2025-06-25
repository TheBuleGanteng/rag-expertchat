from django.core.exceptions import ValidationError
from django.shortcuts import render
from django.http import JsonResponse  # Import JsonResponse for returning JSON data
from django.shortcuts import redirect
from django.utils import translation
from django.utils.translation import activate
from .helpers import detect_language, supported_languages_selected, translate
import logging

logger = logging.getLogger('django')

# Create your views here.

def translate_text(request):
    # POST: Handles form submission, validates the form, and stores the input along with a generated stream_id in the session.
    if request.method == 'POST':
        # Pull in the values submitted by JS
        try:
            input_text = request.POST.get('input_text')
            to_language = request.POST.get('to_language')
        except Exception as e:
            logger.error(f'running translations app, translate_input() ... '
                         f'submission via POST but hit the following error: {str(e)}')
            return JsonResponse({'error': 'Invalid data submission'}, status=400)

        # Some basic error checking
        if to_language not in supported_languages_selected:
            logger.error(f'running translations app, translate_input() ... '
                         f'submission via POST but to_language is not supported. Raising ValidationError')
            raise ValidationError("Invalid value for from_language and/or to_language.")
        
        try:
            from_language = detect_language(input_text)
            logger.debug(f'running translations app, translate_input() ... submission via POST and input_text is: {input_text}, from_language is: { from_language }, to_language is: {to_language}')
            
            output_text = translate(input_text=input_text, from_language=from_language, to_language=to_language)
            logger.debug(f'running translations app, translate_input() ... output_text is: {output_text}')
            
            return JsonResponse({'output_text': output_text}, status=200)  # Return JSON response
        
        except Exception as e:
            logger.error(f'running translations app, translate_input() ... submission via POST but hit the following error: {str(e)}')
            return JsonResponse({'error': 'Translation failed'}, status=500)

    # If not POST, return a 405 Method Not Allowed response
    return JsonResponse({'error': 'Invalid request method'}, status=405)


#------------------------------------------------------------------


def set_session_language(request):
    if request.method == 'POST':
        to_language = request.POST.get('lang')

        if to_language:
            logger.debug(f'running translations app, set_session_language() ... to_language is: {to_language}')
            
            translation.activate(to_language)  # Activate the language
            request.session['django_language'] = to_language  # Store it in the session
            logger.debug(f'running translations app, set_session_language() ... to_language: {to_language} activated and stored in session')

            # Optionally, you could also return the new language code or other data
            return JsonResponse({'message': 'Language set successfully'}, status=200)
        
        else:
            logger.error(f'running translations app, set_session_language() ... no value for to_language, returning error status 400')
            return JsonResponse({'error': 'Language code not provided'}, status=400)
            
    else:
        logger.error(f'running translations app, set_session_language() ... access to the function was not via POST, returning error status 405')
        return JsonResponse({'error': 'Invalid request method'}, status=405)