from aichat_users.models import UserProfile, Favorites
from aichat_chat.models import Expert
import base64
from django import forms
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, get_backends, login, logout
from django.contrib.auth.hashers import check_password
from django.contrib.auth.models import User
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.core.cache import cache
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect, JsonResponse
from django.views.decorators.http import require_http_methods
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import translation
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.safestring import mark_safe
from django.utils.translation import activate, gettext_lazy as _
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from .forms import *
#from google.oauth2 import service_account
#from googleapiclient.discovery import build
from .helpers import *
import logging
import os
import re
import traceback
from urllib.parse import unquote
from translations.helpers.translate import detect_language, supported_languages_selected, translate
logger = logging.getLogger('django')

# Create your views here.
#-------------------------------------------------------------------------


# Get AICHAT_PROJECT_NAME from .env
AICHAT_PROJECT_NAME = os.getenv("AICHAT_PROJECT_NAME") 


#-------------------------------------------------------------------------


# Returns the email if registered or otherwise, None
# Used with jsEmailValidation()
@require_http_methods(['POST'])
def check_email_registered(request):
    logger.debug('running users app, check_email_registered_view(request) ... view started')

    email = request.POST.get('user_input', None)
    if email:
        user = retrieve_email(email)
        # If a user object is found, return the email in the JsonResponse
        if user:
            return JsonResponse({'email': user.email})
        else:
            # If no user is found, return a response indicating the email is not taken
            return JsonResponse({'email': None})
    else:
        # If no email was provided in the request, return an error response
        return JsonResponse({'error': 'No email provided'}, status=400)


#-------------------------------------------------------------------------


# Returns '{'result': True}' if user_input meets password requirements and '{'result': False}' if not.
@require_http_methods(["POST"])
def check_password_strength(request):
    logger.debug('running users app, check_password_strength_view(request) ... view started')

    password = request.POST.get('user_input', None)
    if password:
        result = validate_password_strength(password)
        return JsonResponse({'result': result})
    else:
        # If no email was provided in the request, return an error response
        return JsonResponse({'error': 'No password provided'}, status=400)


#-------------------------------------------------------------------------


# Checks if password passes custom strength requirements
# Used with jsPasswordValidation()
@require_http_methods(["POST"])
def check_password_valid(request):
    logger.debug('running users app, check_password_valid_view(request) ... view started')

    # Step 1: Pull in data passed in by JavaScript
    password = request.POST.get('password')
    password_confirmation = request.POST.get('password_confirmation')

    # Step 2: Initialize checks_passed array
    checks_passed = []
    logger.debug(f'running users app, check_password_valid_view(request) ... initialized checks_passed array ')    
    
    # Step 3: Start performing checks, adding the name of each check passed to the checks_passed array.
    if len(password) >= pw_req_length:
            checks_passed.append('pw-reg-length')
            logger.debug(f'running users app, check_password_valid_view(request) ... password is: { password } appended pw_reg_length to checks_passed array. Length of array is: { len(checks_passed) }.')
    if len(re.findall(r'[a-zA-Z]', password)) >= pw_req_letter:
            checks_passed.append('pw-req-letter')
            logger.debug(f'running users app, check_password_valid_view(request) ... password is: { password } appended pw_req_letter to checks_passed array. Length of array is: { len(checks_passed) }. ')
    if len(re.findall(r'[0-9]', password)) >= pw_req_num:
            checks_passed.append('pw-req-num')
            logger.debug(f'running users app, check_password_valid_view(request) ... password is: { password } appended pw_req_num to checks_passed array. Length of array is: { len(checks_passed) }. ')
    if len(re.findall(r'[^a-zA-Z0-9]', password)) >= pw_req_symbol:
            checks_passed.append('pw-req-symbol')
            logger.debug(f'running users app, check_password_valid_view(request) ... password is: { password } appended pw_req_symbol to checks_passed array. Length of array is: { len(checks_passed) }. ')
    logger.debug(f'running users app, check_password_valid_view(request) ... checks_passed array contains: { checks_passed }. Length of array is: { len(checks_passed) }.')

    # Step 4: Ensure password and confirmation match
    if password == password_confirmation:    
        confirmation_match = True
    else:
        confirmation_match = False
    logger.debug(f'running users app, check_password_valid_view(request) ... confirmation_match is: { confirmation_match }')

    # Step 5: Pass the checks_passed array and confirmation_match back to JavaScript
    logger.debug(f'running users app, check_password_valid_view(request) ... check finished, passing data back to JavaScript')
    return JsonResponse({'checks_passed': checks_passed, 'confirmation_match': confirmation_match} )


#-------------------------------------------------------------------------


# Returns the username if registered or otherwise, None
# Used with jsUsernameValidation()
@require_http_methods(["POST"])
def check_username_registered(request):
    username = request.POST.get('user_input', None)
    if username:
        user = retrieve_username(username)
        # If a user object is found, return the username in the JsonResponse
        if user:
            return JsonResponse({'username': user.username})
        else:
            # If no user is found, return a response indicating the username is not taken
            return JsonResponse({'username': None})
    else:
        # If no username was provided in the request, return an error response
        return JsonResponse({'error': 'No username provided'}, status=400)


#-------------------------------------------------------------------------


@require_http_methods(["GET", "POST"])
@login_required(login_url='aichat_users:login')
def update_favorites(request):
    logger.debug(f'running update_favorites() ... function started')

    if request.method == 'POST':
        logger.debug(f'running update_favorites() ... request via POST')

        expert_id = int(request.POST.get('expert_id'))
        logger.debug(f'running update_favorites() ... expert_id is: { expert_id }')

        user = request.user
        expert = Expert.objects.get(id=expert_id)
        logger.debug(f'running update_favorites() ... user is: { user } and expert is: { expert }')
        
        # Check if the favorite relationship already exists
        favorite, created = Favorites.objects.get_or_create(user=user, expert=expert)

        if created:
                    logger.debug(f'running update_favorites() ... created new favorite relationship between user: { user } and expert: { expert }')
                    return JsonResponse({'success': 'Favorite added'}, status=201)
        else:
            # If the relationship exists, delete it
            favorite.delete()
            logger.debug(f'running update_favorites() ... deleted existing favorite relationship between user: { user } and expert: { expert }')
            return JsonResponse({'success': 'Favorite removed'}, status=200)

    logger.error(f'running update_favorites() ... invalid request method: {request.method}')
    return JsonResponse({'error': 'Invalid request method'}, status=405)




#------------------------------------------------------------------------

@require_http_methods(["GET", "POST"])
@login_required(login_url='aichat_users:login')
def favorites_view(request):
    logger.debug(f'running favorites_view ... view started')

    current_language = request.GET.get('lang', request.session.get('django_language', 'en'))
    logger.debug(f'running favorites_view ... current_language is: { current_language }')
    
    if current_language:
        translation.activate(current_language)
        logger.debug(f'running favorites_view ... current_language activated')
        request.session['django_language'] = current_language
        logger.debug(f'running favorites_view ... request.session[django_language] is: { request.session["django_language"] }')

    user = request.user
    logger.debug(f'running favorites_view ... current_language is: { current_language }, user is: { user }')

    # Initialize ProfileForm with the user object
    profile_form = ProfileForm(user=user)
    logger.debug(f'running favorites_view ... pulled ProfileForm')

    # Get the user's favorite experts
    favorites = user.aichat_favorite.all()
    logger.debug(f'running favorites_view ... favorites retrieved: { favorites }')

    
    favorites_data = []
    
    for favorite in favorites:
        experiences = favorite.expert.experiences.all()
        first_experience = experiences[0] if len(experiences) > 0 else None
        second_experience = experiences[1] if len(experiences) > 1 else None
        total_years = str(int(sum(experience.years for experience in favorite.expert.experiences.all())))

        favorites_data.append({
            'id': favorite.expert.id,
            'name_first': favorite.expert.name_first,
            'name_last': favorite.expert.name_last,
            'photo': favorite.expert.photo,
            'role1': first_experience.role if first_experience else None,
            'employer1': first_experience.employer if first_experience else None,
            'regionCode1': first_experience.geography.region_code if first_experience else None,
            'role2': second_experience.role if second_experience else None,
            'employer2': second_experience.employer if second_experience else None,
            'regionCode2': second_experience.geography.region_code if second_experience else None,
            'total_years': total_years,
            'date_favorited': favorite.added,
            'languages_spoken': ', '.join([language.language.name for language in favorite.expert.languages.all()]),
        })

    # Sort experts by total_score in descending order
    favorites_data.sort(key=lambda x: x['date_favorited'], reverse=True)

    context = {
        'current_language': current_language,
        'favorites_data': favorites_data,
        'profile_form': profile_form,
        'route_used': 'favorites_view',
        'supported_languages': supported_languages_selected,
        'user': user,
        'user_profile': user.aichat_userprofile,
    }
    logger.debug(f'running index_view ... context passed to the template is: {context}')


    return render(request, 'aichat_users/favorites.html', context)

#-------------------------------------------------------------------------


@require_http_methods(["GET", "POST"])
def login_view(request):
    logger.debug('running login_view ... view started')

    current_language = request.GET.get('lang', request.session.get('django_language', 'en'))
    if current_language:
        translation.activate(current_language)
        request.session['django_language'] = current_language
    logger.debug(f'running login_view ... current_language is: {current_language}')
    
    nonce = generate_nonce()
    logger.debug(f'running login_view ... generated nonce of: {nonce}')
    
    if request.user.is_authenticated:
        logger.debug('running login_view ... user arrived at login already authenticated, logging user out')
        logout(request)
    
    form = LoginForm(request.POST or None)

    context = {
        'current_language': current_language,
        'form': form,  
        'route_used': 'login_view',
        'supported_languages': supported_languages_selected,
    }
    logger.debug(f'running login_view ... context passed to the template is: {context}')

    if request.method == "POST":
        logger.debug('running login_view ... user submitted via POST')

        if form.is_valid():
            logger.debug('running login_view ... user submitted via POST and form passed validation')

            email = form.cleaned_data["email"]
            password = form.cleaned_data["password"]
            logger.debug(f'running login_view ... email is: {email}')

            user = authenticate(request, username=email, password=password)
            logger.debug(f'running login_view ... retrieved user object: {user}')

            if user and user.is_active:
                logger.debug('running aichat_users app login_view ... user found in DB and is active. Logging in.')
                login(request, user)
                messages.success(request, _('Welcome %(first_name)s, you are now logged in to %(AICHAT_PROJECT_NAME)s.') % {
                    'first_name': user.first_name,
                    'AICHAT_PROJECT_NAME': AICHAT_PROJECT_NAME
                })
                logger.debug(f'running aichat_users app login_view ... session data before redirect: {request.session.items()} and session key after login is: {request.session.session_key}')
                
                redirect_url = request.GET.get('next') or reverse('aichat_chat:index')
                redirect_url_with_lang = f'{redirect_url}?lang={current_language}'
                logger.info(f'running aichat_users app login_view ... '
                            f'user is: { user }, '
                            f'redirect_url_with_lang is: {redirect_url_with_lang}, '
                            f'login successful, redirecting to redirect_url_with_lang')
                return redirect(redirect_url_with_lang)

            elif user and not user.is_active:
                logger.debug('running aichat_users app login_view ... '
                             f'user found in DB and is not active. Showing error message.')
                messages.error(request, _('You must confirm your account before logging in. Please check your email inbox and spam folders for an email from %(AICHAT_PROJECT_NAME)s or re-register your account.') % {
                    'AICHAT_PROJECT_NAME': AICHAT_PROJECT_NAME
                })
            else:
                logger.debug('running aichat_users app login_view ... user not found in DB')
                messages.error(request, _('Error: Invalid credentials. Please check your entries for email and password. If you have not yet registered for %(AICHAT_PROJECT_NAME)s, please do so via the link below.') % {
                    'AICHAT_PROJECT_NAME': AICHAT_PROJECT_NAME
                })

        else:
            logger.debug('running login_view ... user submitted via POST and form failed validation')
            messages.error(request, _('Error: Invalid input. Please see the red text below for assistance.'))

    else:
        logger.debug('running aichat_users app login_view ... user arrived via GET')

    return render(request, 'aichat_users/login.html', context)


#-------------------------------------------------------------------------


@require_http_methods(['GET', 'POST'])
@login_required(login_url='aichat_users:login')
def logout_view(request):
    logger.debug('running logout_view ... view started')

    current_language = request.GET.get('lang', request.session.get('django_language', 'en'))
    if current_language:
        translation.activate(current_language)
        request.session['django_language'] = current_language
    user = request.user
    logger.debug(f'running logout_view ... user is: {user}, current_language is: {current_language}')
    
    logout(request)

    form = LoginForm()
    context = {
        'current_language': current_language,
        'form': form,
        'supported_languages': supported_languages_selected,
    }
    logger.debug(f'running login_view ... context passed to the template is: {context}')

    logger.debug('running logout_view ... user is logged out and is being redirected to login.html')
    redirect_url_with_lang = f'{reverse("aichat_users:login")}?lang={current_language}'
    messages.info(request, _('You have been logged out of %(AICHAT_PROJECT_NAME)s.') % {
        'AICHAT_PROJECT_NAME': AICHAT_PROJECT_NAME
    })
    return redirect(redirect_url_with_lang)



#-------------------------------------------------------------------------



@require_http_methods(["GET", "POST"])
@login_required(login_url='aichat_users:login')
def password_change_view(request):
    logger.debug('running password_change_view ... view started')

    # Instantiate the form with request.POST or no data depending on the request type
    form = PasswordChangeForm(request.POST or None)
    
    # Since the form is rendered several times, defining context here for brevity
    context = {
        "form": form,
        "pw_req_length": pw_req_length,
        "pw_req_letter": pw_req_letter,
        "pw_req_num": pw_req_num,
        "pw_req_symbol": pw_req_symbol,
    }

    if request.method == "POST":

        # Do the following if submission=POST && submission passes validation...
        if form.is_valid():
            logger.debug('running password_change_view ... user submitted via POST and form passed validation')
        
            try:
                # Assigns to variables the username and password passed in via the form
                password_old = form.cleaned_data['password_old']
                password = form.cleaned_data['password']
                password_confirmation = form.cleaned_data['password_confirmation']
                
            # If pulling in data from the form fails, flash error message and return to password_change
            except Exception as e:
                logger.error(f'running password_change_view ... could not pull in data from form: {e}. Flashing error msg and rendering password_change.html ')
                messages.error(request, _('Error: Please ensure all fields are completed.'))
                return render(request, "aichat_users/password_change.html", context)

            try:                
                # Check if the email+password_old pair submitted are legit.
                user = authenticate(username=request.user.email, password=password_old)
                
                if not user:
                    messages.error(request, "Error: The old password is incorrect.")
                    return render(request, "aichat_users/password_change.html", context)

                # Ensure password (a) differs from password_old and (b) matches password_confirmation
                if password_old == password or password != password_confirmation:
                    logger.error(f'running password_change_view ... user did not submit a valid new password or new password does not match confirmation. Flashing error msg. and rendering password_change.html')
                    messages.error(request, 'Error: New password must differ from existing password and must match password confirmation.')
                    return render(request, "aichat_users/password_change.html", context)

                user.set_password(password)
                user.save()
                
                # Log the user back in with their new password
                updated_user = authenticate(username=request.user.email, password=password)
                login(request, updated_user)

                logger.debug(f'running password_change_view ... user submitted valid password, email_old, email, and email_confirmation. Flashing success msg. and redirecting')
                messages.success(request, 'You have successfully updated your password.')
                return redirect('aichat_chat:index')

            except Exception as e:
                logger.debug(f'running password_change_view ... unable to run authenticate on email+password_old with error: { e }. Flashing error msg. and rendering password_change.html')
                messages.error(request, 'Error: Please check your inputs and try again.')
                return render(request, 'aichat_users/password_change.html', context)

        # If form did not pass validation, throw error and render password_change
        else:
            logger.debug(f'running users app, password_change_view ... Error: form validation errors. flashing message and redirecting user to /register')    
            for field, errors in form.errors.items():
                logger.debug(f'running password_change_view ... erroring field is: { field }')
                for error in errors:
                    logger.debug(f'running password_change_view ... erroring on this field is: {error}')
            messages.error(request, 'Error: Invalid input. Please see the red text below for assistance.')
            return render(request, 'aichat_users/password_change.html', context)

    # User arrived via GET
    else:
        logger.debug(f'running password_change_view ... user arrived via GET')
        return render(request, 'aichat_users/password_change.html', context)


#-------------------------------------------------------------------------


@require_http_methods(["GET", "POST"])
def password_reset_view(request):
    logger.debug('running password_reset_view ... view started')

    # Instantiate the form with request.POST or no data depending on the request type
    form = PasswordResetForm(request.POST or None)

    if request.method == "POST":
        
        # Do the following if submission=POST && submission passes validation...
        if form.is_valid():
            logger.debug('running password_reset_view ... user submitted via POST and form passed validation')
        
            # Try to pull in the data submitted via the form
            try:
                # Assigns to variables the username and password passed in via the form
                email = form.cleaned_data['email']
                logger.debug(f'running password_reset_view ... user-submitted email address is: { email }')
                
            # If pulling in data from the form fails, flash error message and return to password_reset
            except Exception as e:
                logger.error(f'running password_reset_view ... could not pull in data from form: {e}. Flashing error msg and rendering password_change.html ')
                messages.error(request, 'Error: Please ensure all fields are completed.')
                return render(request, 'aichat_users/password_reset.html', {'form':form})
            
            # Try to find the user corresponding to the email address submitted via the form
            try:
                # Queries the DB to check if the user-entered value is in the DB
                user = User.objects.get(email=email)

                # If the user is found and is is_active, compose and sent the email with a token
                if user and user.is_active == True:
                    
                    # Generate token
                    token = generate_unique_token(user)
                    logger.debug(f'running password_reset_view ... token generated')
                
                    # Formulate email
                    TOKEN_TIMEOUT_minutes = int((settings.TOKEN_TIMEOUT)/60)
                    sender = EMAIL_ADDRESS_INFO
                    recipient = user.email
                    subject = f'Reset your { AICHAT_PROJECT_NAME } password'
                    url = generate_confirmation_url(route='password_reset_confirmation', token=token, user=user, request=request)
                    body = f"""<b>Dear {user.username}:</b><br><br>
To reset your {AICHAT_PROJECT_NAME} password, please click the link below within the next {TOKEN_TIMEOUT_minutes} minutes:<br><br>
<a href="{url}" style="color: #0066cc; text-decoration: underline;">Click here to reset your password</a><br><br>
If you did not make this request, you may ignore it.<br><br>
Thank you,<br>
Team {AICHAT_PROJECT_NAME}"""

                    # Send email.
                    send_email(body=body, recipient=recipient, sender=sender, subject=subject)
                    logger.debug(f'running password_reset_view ... user found and reset email sent to email address: { user.email }.')
                    messages.success(request, 'Please check your email inbox and spam folders for an email containing your password reset link.')
                    return redirect('aichat_users:login')
                
                # If no user matching the user-supplied email is found, fake send an email
                else:
                    logger.debug(f'running password_reset_view ... user not found and email not sent. Flashing fake confirmation message and redirecting to login.')
                    messages.success(request, 'Please check your email inbox and spam folders for an email containing your password reset link.')
                    return redirect('users:login')
            
            # Handle if DB query on user-supplied email fails 
            except Exception as e:
                logger.error(f'running password_reset_view ... could not pull in data from form: {e}. Flashing error msg and rendering password_reset.html ')
                messages.error(request, 'Error: Please ensure all fields are completed.')
                return render(request, 'aichat_users/password-reset.html', {'form': form})
        
        # Handle submission via post + user input fails form validation
        else:
            logger.debug(f'running password_reset_view ... Error: form validation errors, flashing message and redirecting user to /password_reset')    
            for field, errors in form.errors.items():
                logger.debug(f'running password_reset_view ... erroring field is: { field }')
                for error in errors:
                    logger.debug(f'running password_reset_view ... erroring on this field is: {error}')
            messages.error(request, 'Error: Invalid input. Please see the red text below for assistance.')
            return render(request, 'aichat_users/password-reset.html', {'form': form})
            
    # Step 3: User arrived via GET
    else:
        logger.debug(f'running password_reset_view ... user arrived via GET')
        return render(request, 'aichat_users/password-reset.html', {'form': form})


#-------------------------------------------------------------------------


@require_http_methods(["GET", "POST"])
def password_reset_confirmation_view(request):
    logger.debug('running password_reset_confirmation_view ... view started')
        
    # Extract 'token' and 'email' from the request
    token = request.GET.get('token') or request.POST.get('token')
    encoded_email = request.GET.get('email') or request.POST.get('email')
    
    # Initialize context
    context = {
        'form': PasswordResetConfirmationForm(),
        'token': token,
        'email': encoded_email,
        'pw_req_length': pw_req_length,
        'pw_req_letter': pw_req_letter,
        'pw_req_num': pw_req_num,
        'pw_req_symbol': pw_req_symbol,
    }
    logger.debug('running password_reset_confirmation_view ... context initialized.')

    # Check for presence of encoded_email and token in the url
    if not encoded_email or not token:
        logger.error(f'running password_reset_confirmation_view ... Error: url is missing encoded_email and/or token.')
        messages.error(request, 'Error: Your token is invalid or expired. Please log in or request a new password reset email.')
        return redirect('aichat_users:login')

    # Try to decode the email in the url and find the associated user
    try:
        email = force_str(urlsafe_base64_decode(encoded_email))
        user = User.objects.get(email=email)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    # Handle if no user found or token is invalid
    if not user or not PasswordResetTokenGenerator().check_token(user, token):
        logger.error(f'running password_reset_confirmation_view ... Error: no user found or token is invalid.')
        messages.error(request, 'Invalid or expired token. Please log in or request a new password reset email.')
        return redirect('aichat_users:login')

    if request.method == "POST":
        logger.debug('running password_reset_confirmation_view ... user submitted via POST')
        
        form = PasswordResetConfirmationForm(request.POST)
        
        if form.is_valid():
            logger.debug('running password_reset_confirmation_view ... user submitted via POST + form passed validation')

            password = form.cleaned_data['password']
            
            if not user.check_password(password):
                user.set_password(password)
                user.save()
                logger.debug(f'running password_reset_confirmation_view ... successfully reset password for user: { user }')
                messages.success(request, 'Your password has been reset successfully.')
                return redirect('aichat_users:login')
            else:
                logger.debug(f'running password_reset_confirmation_view ... failed to reset password for user: { user }')
                messages.error(request, 'New password must differ from the existing password. Please try again.')

    return render(request, 'aichat_users/password-reset-confirmation.html', context)


#-------------------------------------------------------------------------


@require_http_methods(['GET', 'POST'])
@login_required(login_url='aichat_users:login')
def profile_view(request):
    logger.debug(f'running profile_view ... view started')

    current_language = request.GET.get('lang', request.session.get('django_language', 'en'))
    logger.debug(f'running favorites_view ... current_language is: { current_language }')
    
    if current_language:
        translation.activate(current_language)
        logger.debug(f'running favorites_view ... current_language activated')
        request.session['django_language'] = current_language
        logger.debug(f'running favorites_view ... request.session[django_language] is: { request.session["django_language"] }')

    user = request.user
    logger.debug(f'running profile_view ... user is: {user}, view started and current_language is: {current_language}')

    # Define profile_form and context here for all cases
    profile_form = ProfileForm(user=user)
    context = {
        'current_language': current_language,
        'current_language_translated': supported_languages_selected[current_language]['translated_name'],
        'profile_form': profile_form,
        'route_used': 'profile_view',
        'supported_languages': supported_languages_selected,
    }

    if request.method == 'POST':
        if request.headers.get('X-CSRFToken'):
            logger.debug(f'running profile_view ... submission was via POST and the JS included the required CSRF headers')

            # Calls the handle_ajax_form_submission to submit via AJAX to avoid page reload 
            response = handle_ajax_form_submission(request, ProfileForm)
            logger.debug(f'running profile_view ... called handle_ajax_form_submission and response is { response }')

            # If the response is successful, show a success message in the pop-up
            if response.status_code == 200:
                return JsonResponse({'status': 'success'})
            else:
                logger.error(f'running profile_view ... handle_ajax_form_submission returned an error code')
                return JsonResponse({'status': 'error', 'errors': response.get('errors')}, status=400)
            
        else:
            logger.error(f'running profile_view ... the form submission via AJAX was missing CSRF headers')
            messages.error(request, _('There were errors in your form. Please correct them and try again.'))

    logger.debug(f'running profile_view ... context passed to the template is: { context }')
    return render(request, 'aichat_users/profile.html', context)



#-------------------------------------------------------------------------


@require_http_methods(["GET", "POST"])
def register_view(request):
    logger.debug('running register_view ... view started')

    # Instantiate the form with request.POST or no data depending on the request type
    registration_form = RegistrationForm(request.POST or None)
    
    # Since the form is registered several times, defining context here for brevity
    context = {
        "registration_form": registration_form,
        "pw_req_length": pw_req_length,
        "pw_req_letter": pw_req_letter,
        "pw_req_num": pw_req_num,
        "pw_req_symbol": pw_req_symbol,
    }

    if request.method == "POST":
        logger.info('running register_view ... user submitted via POST')

        # Do the following if submission=POST && submission passes validation...
        if registration_form.is_valid():
            logger.info('running register_view ... user submitted via POST and form passed validation')
        
            # Assigns to variables the username and password passed in via the form in login.html
            first_name = registration_form.cleaned_data['first_name']
            last_name = registration_form.cleaned_data['last_name']
            user_employer = registration_form.cleaned_data['user_employer']
            username = registration_form.cleaned_data['username']
            email = registration_form.cleaned_data['email']
            password = registration_form.cleaned_data['password']
            
            try:
                # Step 2.1.1.1: If email and/or username are already registered, flash error and redirect to register.html.
                if retrieve_email(email) or retrieve_username(username):
                    logger.error(f'running register_view ... user-submitted email and/or username is already registered. Flashing error msg and returning to register.html')
                    messages.error(request, _('Error: Email address and/or username is unavailable. If you already have an account, please log in. Otherwise, please amend your entries.'))
                    return render(request, 'aichat_users/register.html', context)
                logger.info(f'running register_view ... user-submitted email and username are not already in DB. Proceeding with account creation.')
                
                logger.info(f'running register_view ... structure of User object is as follows: { ([field.name for field in User._meta.get_fields()]) }')
                
                #test_user = User.objects.get(id=1)
                #logger.info(f'running register_view ... example of User with id=1 is: { test_user.__dict__}')
                
                # Step 2.1.1.2: If email and username are not already registered, input data to DB.
                logger.info(f'running register_view ... creating user with: first_name={first_name}, last_name={last_name}, username={username}, email={email}, password=******')
                
                try:
                    user = User.objects.create_user(
                        first_name=first_name,
                        last_name=last_name,
                        username=username, 
                        email=email, 
                        password=password,
                        is_active=False, # Sets is_active to false, so that it can be flipped to on after confirmation link is clicked. 
                    )
                    logger.info(f'running register_view ... new user object created: { user }')
                    user.save()
                    logger.info(f'running register_view ... new user object saved: { user }')
                except Exception as e:
                    logger.error(f'running register_view ... error occurred during user creation: {e}')
                    return render(request, 'aichat_users/register.html', context)

                logger.info(f'running register_view ... new creating new user_profile object with: user: { user } and user_employer: { user_employer }')
                user_profile = UserProfile.objects.create(
                    user=user,
                    user_employer=user_employer,
                )
                logger.info(f'running register_view ... new user_profile object created: { user_profile }')
                user_profile.save()
                logger.info(f'running register_view ... new user_profile object saved: { user_profile }')

                
                # Step 2.1.1.3: Query new user object from DB.
                user = User.objects.get(email=email)
                logger.info(f'running register_view ... '
                             f'successfully pulled user object post-creation using email: { email }. '
                             f'User object is: { user }')
                
                # Step 2.1.1.3: Generate token
                token = generate_unique_token(user)
                logger.debug(f'running register_view ... token generated')
                
                # Step 2.1.1.4: Formulate email
                TOKEN_TIMEOUT_minutes = int((settings.TOKEN_TIMEOUT)/60)
                username = user.username
                sender = EMAIL_ADDRESS_INFO
                recipient = user.email
                subject_text_translated = _('Confirm your registration with')
                subject = f'{ subject_text_translated } { AICHAT_PROJECT_NAME }'
                url = generate_confirmation_url(route='register_confirmation', token=token, user=user, request=request)
                body_text_1= _('Dear ')
                body_text_2= _('To confirm your registration with')
                body_text_3= _('please visit the following link within the next')
                body_text_4= _('minutes')
                body_text_5= _('If you did not make this request, you may ignore it.')
                body_text_6= _('Thank you')
                body = f'''<b>{body_text_1} { user.username }:</b>
                <br>
                { body_text_2 } { AICHAT_PROJECT_NAME }, { body_text_3 } { TOKEN_TIMEOUT_minutes } { body_text_4 }:
                <br>
                <br>                    
                <a href="{url}" style="color: #0066cc; text-decoration: underline;">Click here to confirm you registration</a>
                <br>
                <br>
                { body_text_5 }
                <br>
                { body_text_6 },
                <br>
                {AICHAT_PROJECT_NAME}'''
            
            
                # Step 2.1.1.5: Send email.
                send_email(body=body, recipient=recipient, sender=sender, subject=subject)
                #logger.debug(f'running users app, register_view ... reset email sent to email address: { user.email }.')
                
                response = HttpResponseRedirect(reverse('aichat_users:login'))
                logger.debug(f'running register_view ... response is: { response }')

                cookie_token = generate_unique_token(user)
                logger.debug(f'running register_view ... cookie_token is: { cookie_token }')
                
                response.set_cookie(key='registration_id', value=cookie_token, max_age=3600, secure=True, httponly=True)
                logger.debug(f'running register_view ... set registration_id equal to cookie_token. All cookies now: { request.COOKIES }')
                
                messages.success(request, 'Thank you for registering. Please check your email inbox and spam folders for an email containing your confirmation link.')
                return response

            # Step 2.1.2: If sending email fails, flash error message and return to register
            except Exception as e:
                logger.debug(f'running register_view ... Error 2.1.2 (unable to register user in DB and send email): {e}. Flashing error msg and rendering register.html ')
                messages.error(request, f'Error: { e }')
                return render(request, 'aichat_users/register.html', context)

        # Step 2.2: Handle submission via post + user input fails form validation
        else:
            logger.debug(f'running register_view ... Error 2.2 (form validation errors), flashing message and redirecting user to /register')    
            for field, errors in registration_form.errors.items():
                logger.debug(f'running register_view ... erroring field is: { field }')
                for error in errors:
                    logger.debug(f'running register_view ... erroring on this field is: {error}')
            messages.error(request, 'Error: Invalid input. Please see the red text below for assistance.')
            return render(request, 'aichat_users/register.html', context)
            
    # Step 3: User arrived via GET
    else:
        logger.debug(f'running register_view ... user arrived via GET')
        return render(request, 'aichat_users/register.html', context)


#-------------------------------------------------------------------------


# Changes user's status to is_active
@require_http_methods(["GET", "POST"])
def register_confirmation_view(request):
    logger.debug('running register_confirmation_view ... view started')

    try:
        token = request.GET.get('token')
        encoded_email = request.GET.get('email')
        email = force_str(urlsafe_base64_decode(encoded_email))
        logger.debug(f'running register_confirmation_view ... email from url is: { email }')

        user = User.objects.get(email=email)
        logger.debug(f'running register_confirmation_view ... user object retrieved via email in url: { email } is: { user }')

        # Step 1: Take the token and decode it
        #user = verify_unique_token(decoded_token, settings.SECRET_KEY, int(os.getenv('MAX_TOKEN_AGE_SECONDS')))
        token_generator = PasswordResetTokenGenerator()

        # Step 2: If token is invalid, flash error msg and redirect user to register
        if not token_generator.check_token(user, token):
            logger.debug(f'running register_confirmation_view ... no user found.')
            messages.error(request, 'Error: If you have already confirmed your account, please log in. Otherwise please re-register your account to get a new confirmation link via email.')    
            return redirect('aichat_users:login')

        # Step 4: If user.is_active = false, change to true.
        if not user.is_active:
            user.is_active = True
            user.save()
            logger.debug(f'running register_confirmation_view ... updated user: { user } to is_active.')
            
            # Log the current URL
            current_url = request.build_absolute_uri()
            logger.debug(f'running register_confirmation_view ... current URL is: {current_url}')
            logger.debug(f'running register_confirmation_view ... All cookies now: { request.COOKIES }')

            # Step 5: Check for the presence of a cookie.  If present, authenticate user and direct to index. If not present, force user to log in.
            registration_id = request.COOKIES.get('registration_id')
            logger.debug(f'running register_confirmation_view ... registration_id from cookie is: {registration_id}. All cookies are: { request.COOKIES }  ')
            
            if not registration_id: 
                logger.debug(f'running register_confirmation_view ... updated user: { user } to is_active. Since cookie is not present, redirecting to users:login.')
                messages.error(request, "Congratulations, your account is is_active. Please log in.")
                return redirect('aichat_users:login')
            else:
                logger.debug(f'running register_confirmation_view ... updated user: { user } to is_active. Since cookie is present, redirecting to aichat_chat:index.')
                messages.success(request, f'Congratulations, your account is confirmed. Welcome to { AICHAT_PROJECT_NAME } ')
                
                # Log in the user with the correct backend
                backend = settings.AUTHENTICATION_BACKENDS[0]
                logger.debug(f'running register_confirmation_view ... backend is: { backend }')
                
                setattr(user, 'backend', backend)
                logger.debug(f'running register_confirmation_view ... backend is: { backend }')

                login(request, user, backend=backend)
                logger.debug(f'running register_confirmation_view ... user: { user } is logged in.')
                return redirect('aichat_chat:index')

        # If user + is_active = true, flash error message and redirect to login. Note: this should not be possible since token is one-time-use.
        else:
            logger.debug(f'running register_confirmation_view ... Error: user already is_active. Flashing msg and redirecting to login.')
            messages.error(request, 'Error: This account is already confirmed. Please log in.')
            return redirect('aichat_users:login')

    # Step 5: If token is invalid or DB update fails, flask error message and redirect to reset.html
    except Exception as e:
            logger.debug(f'running register_confirmation_view ... Error: unable to change user.is_active to True. Error is: {e}. Flashing error msg and rendering register.html ')
            messages.error(request, f'Error: {e} Please log in or re-register.')
            return redirect('aichat_users:login')
