from django.contrib.auth import update_session_auth_hash
from django.http import JsonResponse
import logging
logger = logging.getLogger('django')


__all__ = ['handle_ajax_form_submission']

def handle_ajax_form_submission(request, form_class):
    logger.debug(f'running aichat_users app, handle_ajax_form_submission ...')

    try:
        form = form_class(request.POST, user=request.user)  # Pass the user argument
        logger.debug(f'running aichat_users app, handle_ajax_form_submission ... form submitted')
        
        if form.is_valid():
            logger.debug(f'running aichat_users app, handle_ajax_form_submission ... form submitted and was valid')
            
            user = form.save()
            logger.debug(f'running aichat_users app, handle_ajax_form_submission ... saved form, updated user data for user: { user }')
            
            # Refresh the user object in the session
            update_session_auth_hash(request, user)
            logger.debug(f'running aichat_users app, handle_ajax_form_submission ... updated session with new user data')
            
            # Return a response indicating successful submission
            return JsonResponse({'status': 'success'})
        else:
            errors = {field: error.get_json_data() for field, error in form.errors.items()}
            return JsonResponse({'status': 'error', 'errors': errors}, status=400) # Typically, status=500 means when problem is with client input

    except Exception as e:
        response = {'error': str(e)}
        logger.error(f'running aichat_users app, handle_ajax_form_submission ... the following error occurred and the function returned the following response: { response } ')

        return JsonResponse({'status':'error', 'error': str(e)}, status=500) # Typically, status=500 means when problem is on server side and the issue cannot be fixed by altering client input