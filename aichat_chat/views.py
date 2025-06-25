from aichat_users.forms import ProfileForm
from aichat_users.models import UserProfile
from aichat_users.helpers import *
import base64
import copy
from django.shortcuts import render
from django import forms
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.files.storage import FileSystemStorage
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone, translation
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_http_methods
from .forms import *
from .helpers import *
from .models import ChatHistory, RagSource, Vector
import logging
import os
from pinecone import Pinecone, PineconeException
from translations.helpers.translate import supported_languages_selected
import uuid

logger = logging.getLogger('django')


# API ENDPOINTS
#-------------------------------------------------------------------------


@require_http_methods(["POST"])
@login_required(login_url='aichat_users:login')
def delete_rag_sources(request):    
    logger.info(f'running delete_rag_sources() ... view started')

    # Pull the logged-in user object
    user = request.user
    logger.debug(f'running delete_rag_sources() ... user is: { user }')

    if request.headers.get('X-CSRFToken'):
        
        # Step 1: Delete ragsources and vectors from SQL
        ragrources_to_delete = RagSource.objects.filter(user_id=user.id)
        documents_to_delete = RagSource.objects.filter(user_id=user.id, type__in=['document', 'image'])
        ragsources_to_delete_file_names = list(documents_to_delete.values_list('source', flat=True))
        logger.debug(f'running delete_rag_sources() ... '
                    f'ragrources_to_delete is: { ragrources_to_delete }, '
                    f'documents_to_delete is: { documents_to_delete } and '
                    f'ragsources_to_delete_file_names is: { ragsources_to_delete_file_names }')

        vectors_to_delete = Vector.objects.filter(user_id=user.id)
        vector_ids_to_delete_from_index = list(vectors_to_delete.values_list('vector_id', flat=True))
        
        logger.debug(f'running delete_rag_sources() ... '
                    f'vectors_to_delete is: { vectors_to_delete } '
                    f'vector_ids_to_delete_from_index is: { vector_ids_to_delete_from_index }')    
        
        vectors_to_delete.delete()
        ragrources_to_delete.delete()

        
        # Step 2: Delete files from disk, if any
        for file_name in ragsources_to_delete_file_names:
            logger.debug(f'running delete_rag_sources() ... '
                        f'file_name is: { file_name }')
            file_path_on_disk = os.path.join(settings.MEDIA_ROOT, f'{user.id}', file_name)
            logger.debug(f'running delete_rag_sources() ... '
                        f'file_path_on_disk is: { file_path_on_disk }')
                    
            try:
                # Delete the file from disk
                if os.path.exists(file_path_on_disk):
                    os.remove(file_path_on_disk)
                    logger.debug(f'running delete_rag_sources() ... file deleted from disk: {file_path_on_disk}')
                else:
                    logger.error(f'running delete_rag_sources() ... error- file_path_on_disk does not exist, cannot delete file')
            
            except Exception as e:
                logger.error(f'running delete_rag_sources() ... error deleting file {file_path_on_disk}: {str(e)}')

        
        # Step 3: Delete the vectors from the Pinecone index
        try:
            pc = Pinecone(api_key=PINECONE_API_KEY)
            index_name = 'vectorized-sources'
            index = pc.Index(index_name)
            
            success = delete_obsolite_vectors_from_index(
                index=index,
                namespace = str(user.id), # EXPOSE LATER
                pc = pc,
                vector_ids_to_delete_from_index=vector_ids_to_delete_from_index,
                )
            if success:
                logger.debug(f'running delete_rag_sources() ... '
                            f'vector_ids_to_delete_from_index: { vector_ids_to_delete_from_index }')
                return JsonResponse({'status': 'success', 'message': _('Successfully deleted all materials previously uploaded.')})
            else:
                logger.error('Vector deletion from Pinecone failed.')
                return JsonResponse({'status': 'error', 'message': _('Error deleting existing materials from vector database.')}, status=400)
    
        except PineconeException as e:
            logger.error(f'Error during Pinecone operation: {e}')
            return JsonResponse({'status': 'error', 'message': _('Error deleting existing materials.'), 'errors': str(e)}, status=400)


#-------------------------------------------------------------------------


@require_http_methods({'POST'})
@login_required(login_url='aichat_users:login')
def generate_embeddings(request):    
    logger.info(f'running generate_embeddings() ... view started')

    # Pull the logged-in user object
    user = request.user
    logger.debug(f'running generate_embeddings() ... user is: { user }')

    set_up_retriever_response = set_up_retriever(user=user)
    
    # Handle the response after running vectroize_sources
    if set_up_retriever_response.status_code == 200:
        logger.info(f'running generate_embeddings() ... set_up_retriever() succeeded with status: {set_up_retriever_response.status_code}')
        return JsonResponse({'status': 'success', 'message': _('Materials uploaded and processed successfully. The bot is ready for chatting!')})
    
    else:
        logger.error(f'running generate_embeddings() ... set_up_retriever() failed with status: {set_up_retriever_response.status_code}')
        return JsonResponse({'status': 'error', 'message': _('Error uploading documents.'), 'errors': set_up_retriever.json().get('errors', {})}, status=400)


# -------------------------------------------------------------------------


@require_http_methods(["GET", "POST"])
@login_required(login_url='aichat_users:login')
def rag_docs(request):    
    logger.info(f'running rag_docs() ... view started')

    # Pull language data
    current_language = request.GET.get('lang', request.session.get('django_language', 'en'))
    if current_language:
        translation.activate(current_language)
        request.session['django_language'] = current_language

    # Pull the logged-in user object
    user = request.user
    logger.debug(f'running rag_docs() ... user is: { user }')

    type = 'document' # Used for subsequent filtering
    upload_path = 'uploads/'

    # Handle POST requests (form submission)
    if request.method == 'POST':
        
        # Ensure user is logged into pinecone and determine if an existing index was deleted due to change in model
        deleted_existing_index, index, namespace = connect_to_pinecone(user)
        logger.debug(f'running rag_docs() ... '
                    f'user: { user } connected to pinecone index: { index } '
                    f'with namespace { namespace }. deleted_existing_index is: { deleted_existing_index }')

        # If an existing index was deleted due to change in model, then also delete the corresponding records in SQL
        if deleted_existing_index:
            RagSource.objects.filter(user=user).delete()
            Vector.objects.filter(user=user).delete()
            logger.debug(f'running rag_docs() ... '
                    f'deleted existing RagSource and Vector objects for user: { user }')

        # Update the queryset after SQL deletions
        existing_sources = RagSource.objects.filter(type=type, user=user)
        existing_vectors = Vector.objects.filter(type=type, user=user)
        logger.debug(f'running rag_docs() ... on form submission, '
                    f'existing_sources is: { existing_sources } and '
                    f'existing_vectors is: { existing_vectors }'
                    )

        # Pull in the submitted RagDocForm
        form = RagDocForm(request.POST, request.FILES)
        
        #try:
        if form.is_valid():

            docs_to_vectorize = [] # Instantiate the list that will hold docs not already in the DB and thus, need to be vectorized

            # Pull in the existing files from the form
            existing_files = request.POST.getlist('existing_files')
            logger.debug(f'running rag_docs() ... '
                        f'request.method is: { request.method } and existing_files is: {existing_files}')
            
            # Pull in the submitted RagDocForm
            files = request.FILES.getlist('file_path')
            newly_submitted_docs = [file.name for file in files]  # Get the names of the newly uploaded files
            logger.debug(f'running rag_docs() ... '
                        f'newly_submitted_docs is: { newly_submitted_docs }')
            
            # Combine existing files and newly submitted files for validation
            all_submitted_docs = set(newly_submitted_docs + existing_files)
            logger.debug(f'running rag_docs() ... all_submitted_docs is:{ all_submitted_docs }')

            # Take note of what files were present on page load, but not present when form was submitted, so we can remove those files from disk and the corresponding records from SQL and Pinecone
            deleted_sources = set(existing_sources.values_list('source', flat=True)) - set(existing_files) # Compare existing sources with submitted ones to identify deleted files
            logger.debug(f'running rag_docs() ... deleted_sources is: { deleted_sources }')

            for file in files:
                
                # Pull the file's name and size
                file_name = file.name
                file_size = file.size / (1024 * 1024)  # Save file size in MB
                
                # Take the list of docs already in the DB and see if the submitted doc is in there
                existing_source = existing_sources.filter(source=file_name).first()

                # Case 1: The submitted doc is already in the DB --> do nothing
                if existing_source:
                    logger.debug(f'running rag_docs() ... file_name is: { file_name } and '
                                f'Submitted value matches existing DB entry. '
                                f'No DB change needed for this URL and not appended to docs_to_vectorize.'
                                )
                # Case 2: The submitted document is not already in the DB --> save to sources
                else:
                    # Create an instance of FileSystemStorage with your desired path
                    upload_directory = os.path.join(settings.MEDIA_ROOT, f'{user.id}')
                    fs = FileSystemStorage(location=upload_directory)
                    logger.debug(f'running rag_docs() ... '
                                f'set up with upload_directory: { upload_directory }')

                    # Save uploaded doc to the server for future access
                    try:
                        file_saved_to_disk = fs.save(file_name, file)
                        logger.debug(f'File successfully saved to: {file_saved_to_disk}')
                    except Exception as e:
                        logger.error(f'Error saving file: {str(e)}')
                    logger.debug(f'running rag_docs() ... '
                                f'Submitted doc is not in DB '
                                f'Saved file: { file } to upload_directory: { upload_directory }'
                                )

                    # Reset the file pointer to ensure it can be read again
                    file.seek(0)

                    # Save to aichat_ragsource in SQL 
                    new_source_to_rag = RagSource(
                        source=file_name,
                        type=type,
                        user=user,
                        file_path=upload_path+file_name,
                        file_size=file_size,
                        )
                    new_source_to_rag.save()
                    docs_to_vectorize.append(file)   
                    logger.debug(f'running rag_docs() ... '
                                f'Submitted doc is not in DB '
                                f'Saved new_source_to_rag: { new_source_to_rag } to SQL and '
                                f'docs_to_vectorize updated to: { docs_to_vectorize }'
                                )

            # Delete the RagSource and Vectors from the DB if a user has removed a pre-existing source from the submitted form
            if deleted_sources:

                # Fetch the vector IDs as a list of strings, ensuring uniqueness
                vector_ids_to_delete_from_index = list(Vector.objects.filter(source__in=deleted_sources, user=user).values_list('vector_id', flat=True))
                
                # Convert the IDs to strings if Pinecone expects string-based IDs
                vector_ids_to_delete_from_index = [str(vector_id) for vector_id in vector_ids_to_delete_from_index]
                logger.debug(f'running rag_docs() ... vector_ids_to_delete_from_index is: { vector_ids_to_delete_from_index }')

                for deleted_source in deleted_sources:
                    logger.debug(f'running rag_docs() ... deleted_source is: { deleted_source }')

                    file_path_on_disk = os.path.join(settings.MEDIA_ROOT, f'aichat_chat/user_uploads/{user.id}',deleted_source)
                    logger.debug(f'running rag_docs() ... file_path_on_disk is: { file_path_on_disk }')
                    
                    try:
                        # Delete the file from disk
                        if os.path.exists(file_path_on_disk):
                            os.remove(file_path_on_disk)
                            logger.debug(f'running rag_docs() ... file deleted from disk: {file_path_on_disk}')
                        else:
                            logger.error(f'running rag_docs() ... error- file_path_on_disk does not exist, cannot delete file')
                    
                    except Exception as e:
                        logger.error(f'running rag_docs() ... error deleting file {file_path_on_disk}: {str(e)}')

                # Delete the corresponding records in the SQL aichat_ragsources table
                existing_sources_to_delete = existing_sources.filter(source__in=deleted_sources, user=user)
                existing_sources_to_delete.delete()
                
                # Delete the corresponding records in the SQL aichat_vector table
                existing_vectors_to_delete = existing_vectors.filter(source__in=deleted_sources, user=user)
                existing_vectors_to_delete.delete()
                logger.info(f'running rag_docs() ... '
                                f'Removed the following stale sources and vectors from SQL '
                                f'existing_sources_to_delete: { existing_sources_to_delete } '
                                f'existing_vectors_to_delete: { existing_vectors_to_delete }'
                                )
                
                # Remove the obsolite vectors from the index
                delete_obsolite_vectors_from_index(
                    index=index,
                    namespace=namespace,
                    pc=pc,
                    vector_ids_to_delete_from_index=vector_ids_to_delete_from_index,
                )
                logger.info(f'running rag_docs() ... '
                            f'deleted the following vector IDs from the index: { vector_ids_to_delete_from_index }')

            
            summary_method = 'mean_last_layer' # EXPOSE LATER
            
            if docs_to_vectorize:        
                vectorize_docs(
                    files=docs_to_vectorize,  
                    pc=pc,
                    summary_method=summary_method, 
                    user=user,
                )
                logger.info(f'running vectorize_sources() ... called vectiorize_docs()')

                #return JsonResponse({'status': 'success', 'message': _('Materials uploaded and processed successfully. The bot is ready for chatting!')})

            
            # Set up the retriever
            if user.aichat_userprofile.rag_sources_used in ('all', 'document'):
                retriever = set_up_retriever(user=user)
                if retriever:
                    logger.debug(f'running aichat_chat app, rag_docs() ... successfully set up retriever: {retriever}')
                    return JsonResponse({'status': 'success', 'message': _('Materials uploaded and processed successfully. The bot is ready for chatting!')})
                else:
                    logger.error(f'running aichat_chat app, rag_docs() ... Error: vectorization failed.')
                    return JsonResponse({'status': 'error', 'message': _('Error uploading documents.')}, status=400)

            return JsonResponse({'status': 'success', 'message': _('Settings updated successfully.')})

            # Set the conversation_id in the SQL DB
            user.aichat_userprofile.conversation_id = f'{user.id}--{request.session.session_key}'
            user.aichat_userprofile.save()


        # Return an error if the form is not valid
        else:
            return JsonResponse({'status': 'error', 'message': 'Invalid form data.'}, status=400)
            
        """    
        except Exception as e:
            logger.error(f'running aichat_chat app, rag_docs() ... error during form submission: {str(e)}')
            return JsonResponse({'status': 'error', 'message': f'An error occurred: {str(e)}'}, status=500)
        """
    # Handle GET requests (initial page load)
    if request.method == 'GET':

        # Pull the existing documents in the SQL DB, if any
        documents = RagSource.objects.filter(type=type, user=user)
        form = RagDocForm()
        logger.debug(f"Loaded form with existing documents: {documents}")
    
        if request.headers.get('x-requested-with') == 'XMLHttpRequest': # Checks if is AJAX
            logger.debug(f'running rag_docs() ... request.method is: { request.method } + AJAX')
            
            path_to_injected_html = os.path.join(settings.BASE_DIR, 'aichat_chat/templates/aichat_chat/rag_docs_form.html')
            logger.debug(f'running rag_docs() ... path_to_injected_html is: { path_to_injected_html }')
            
            html = render_to_string(path_to_injected_html, {'form': form, 'documents': documents}, request=request)
            logger.debug(f'running rag_docs() ... html is: { html }')
            return JsonResponse({'html': html})
        else:
            logger.info(f'running rag_docs() ... request.method is: { request.method }')
            return render(request,'aichat_chat/rag_docs_form.html',{
                'form': form,
                'documents': documents,
                'MEDIA_URL': settings.MEDIA_URL,
                }
            )


# -------------------------------------------------------------------------


@require_http_methods(["GET", "POST"])
@login_required(login_url='aichat_users:login')
def rag_url(request):
    logger.info(f'running rag_url() ... view started')

    # Pull language data
    current_language = request.GET.get('lang', request.session.get('django_language', 'en'))
    if current_language:
        translation.activate(current_language)
        request.session['django_language'] = current_language
    logger.debug(f'running rag_url() ... current_language is: { current_language } and '
                f'request.session[django_language] is: { request.session["django_language"] }')

    # Pull the logged-in user object
    user = request.user

    # Set type to 'website' (used for subsequent filtering)
    type = 'website'

    # Handle POST requests (form submission)
    if request.method == 'POST':
        logger.debug(f'running rag_url() ... request.method is: { request.method }')

        # First, save the submitted form to re-populate it after potential DB deletion
        formset = RagUrlFormSet(request.POST)
        logger.debug(f'running rag_url() ... formset is: { formset }')
        
        # Ensure user is logged into pinecone and determine if an existing index was deleted due to change in model
        deleted_existing_index, index, namespace = connect_to_pinecone(user)
        logger.debug(f'running rag_url() ... '
                    f'user: { user } connected to pinecone index: { index } '
                    f'with namespace { namespace }. deleted_existing_index is: { deleted_existing_index }')

        # If an existing index was deleted due to change in model, then also delete the corresponding records in SQL
        if deleted_existing_index:
            RagSource.objects.filter(user=user).delete()
            Vector.objects.filter(user=user).delete()
            logger.debug(f'running rag_url() ... '
                    f'deleted existing RagSource and Vector objects for user: { user }')

        # Update the queryset after SQL deletions
        existing_urls = RagSource.objects.filter(user=user)
        existing_vectors = Vector.objects.filter(user=user)
        logger.debug(f'running rag_url() ... updated existing_urls is: {existing_urls}')

        
        if formset.is_valid():
            
            # Instantiates list to hold submitted URLs (used for deleting URLs from DB later)
            urls_from_formset =[]
            urls_to_vectorize = []
            logger.debug(f'running rag_url() ... '
                        f'before updating DB, urls_from_formset is: { urls_from_formset } and '
                        f'before updating DB, urls_to_vectorize is: { urls_to_vectorize }'
                        )

            for form in formset:
                
                # Pull the url and include_subdomains checkbox from submitted form
                form_url = form.cleaned_data.get('source')
                form_url_full = format_full_web_address(abbreviated_url=form_url)
                form_include_subdomains = form.cleaned_data.get('include_subdomains')
                logger.debug(f'running rag_url() ... '
                            f'form_url is: { form_url }, '
                            f'form_url_full is: { form_url_full } and '
                            f'form_include_subdomains is: { form_include_subdomains }'
                            )

                if form_url:
                    urls_from_formset.append(form_url_full)

                    # Take the list of URLs already in the DB and see if the submitted URL is in there
                    existing_url = existing_urls.filter(source=form_url).first()

                    # Case 1: If the submitted URL is already in the DB and no change to include_subdomains --> do nothing
                    if existing_url and existing_url.include_subdomains == form_include_subdomains:
                        logger.debug(f'running rag_url() ... form_url_full is: { form_url_full } and '
                                    f'form_include_subdomains is: { form_include_subdomains }. '
                                    f'Submitted value matches existing DB entry. '
                                    f'No DB change needed for this URL and not appended to urls_to_vectorize.'
                                    )

                    # Case 2: If the submitted URL is already in the DB and THERE IS change to include_subdomains --> update DB and append to urls_to_vectorize
                    elif existing_url and existing_url.include_subdomains != form_include_subdomains:
                        existing_url.include_subdomains = form_include_subdomains
                        existing_url.save()
                        urls_to_vectorize.append(form_url)
                        logger.debug(f'running rag_url() ... form_url_full is: { form_url_full } and '
                                    f'form_include_subdomains is: { form_include_subdomains }. '
                                    f'Submitted url matches existing DB entry, but value for form_include_subdomains differs from DB. '
                                    f'Updated DB and appended to form_url to urls_to_vectorize.'
                                    )
                    
                    # Case 3: If the url is not already in SQL, save URL and value for include_subdomains to SQL
                    else:
                        new_rag_url = RagSource(
                            user=user, 
                            source=form_url_full, 
                            include_subdomains=form_include_subdomains, 
                            type=type,
                            )
                        urls_to_vectorize.append(form_url_full)
                        new_rag_url.save()
                        logger.debug(f'running rag_url() ... form_url_full is: { form_url_full }, '
                                    f'form_include_subdomains is: { form_include_subdomains }, and '
                                    f'Submitted url is not in DB '
                                    f'Saved to DB and appended to form_url to urls_to_vectorize.'
                                    )
            
            # Intialize the list that will hold the vector IDs that will
            vector_ids_to_delete_from_index = []

            # Handle deletions via deleted_forms
            for deleted_form in formset.deleted_forms:
                deleted_url = deleted_form.cleaned_data.get('source')
                
                if deleted_url:
                    existing_urls_to_delete = existing_urls.filter(source=deleted_url)
                    existing_vectors_to_delete = existing_vectors.filter(source=deleted_url)
                    existing_vectors_to_delete_ids = list(existing_vectors_to_delete.values_list('vector_id', flat=True))
                    vector_ids_to_delete_from_index.extend(existing_vectors_to_delete_ids)
                                        
                    if existing_urls_to_delete:
                        existing_urls_to_delete.delete()
                        existing_vectors_to_delete.delete()

                        logger.debug(f'running rag_url() ... '
                                    f'deleted existing_urls_to_delete: { existing_urls_to_delete } and '
                                    f'existing_vectors_to_delete { existing_vectors_to_delete } from SQL DB '
                                    )  
            logger.debug(f'running rag_url() ... after updating DB, '
                        f'urls_to_vectorize is: { urls_to_vectorize } and '
                        f'vector_ids_to_delete_from_index is: { vector_ids_to_delete_from_index }'
                        )
            
            
            if vector_ids_to_delete_from_index:
                delete_obsolite_vectors_from_index(
                    index=index,
                    namespace=namespace,
                    pc=pc,
                    vector_ids_to_delete_from_index=vector_ids_to_delete_from_index,
                )
                logger.debug(f'running rag_url() ... '
                            f'deleted the following urls from the index: { urls_from_formset }')
            
            
            if urls_to_vectorize:
                vectorize_web( 
                    index=index,
                    namespace=namespace, 
                    summary_method='mean_last_layer', # EXPOSE LATER
                    urls=urls_to_vectorize,
                    user=user
                    )
                logger.info(f'running rag_url() ... '
                            f'successfully ran vectorize_web() on urls_to_vectorize: { urls_to_vectorize }'
                            )
            else:
                logger.info(f'running rag_url() ... '
                            f'did not run vectorize_web() because urls_to_vectorize is empty'
                            )
                
            # Set the conversation_id in the SQL DB
            user.aichat_userprofile.conversation_id = f'{user.id}--{request.session.session_key}'
            user.aichat_userprofile.save()
            
            
            html = render_to_string('aichat_chat/rag_url_formset.html', {'formset': formset}, request=request)
            return JsonResponse({'status': 'success', 'message': _('URLs ready for use!'), 'html': html})
                
        # If form fails valiation
        else:
            logger.error(f'running rag_url() ... '
                         f'RagUrlFormSet failed validation with the following errors { formset.errors }')
            # Return the form errors as JSON for AJAX handling
            html = render_to_string('aichat_chat/rag_url_formset.html', {'formset': formset}, request=request)
            return JsonResponse({'status': 'error', 'errors': formset.errors, 'html': html})

    
    
    # Handle GET requests (initial form population)
    else:
        formset = RagUrlFormSet(queryset=RagSource.objects.filter(type=type, user=user))
        
        logger.debug(f'running rag_url() ... formset is: { formset }')

        if request.headers.get('x-requested-with') == 'XMLHttpRequest': # Checks if is AJAX
            logger.debug(f'running rag_url() ... request is GET + AJAX')
            
            path_to_injected_html = os.path.join(settings.BASE_DIR, 'aichat_chat/templates/aichat_chat/rag_url_formset.html')
            logger.debug(f'running rag_url() ... path_to_injected_html is: { path_to_injected_html }')
            
            html = render_to_string(path_to_injected_html, {'formset': formset}, request=request)
            logger.debug(f'running rag_url() ... html is: { html }')
            return JsonResponse({'html': html})
        
        # For non-AJAX requests, render the formset as part of the full page
        else:
            logger.info(f'running rag_url() ... request is GET + NOT AJAX')
            return render(request, 'aichat_chat/rag_url_formset.html', {'formset': formset})


# -------------------------------------------------------------------------


@require_http_methods(['GET'])
@login_required(login_url='aichat_users:login')
def retrieve_chat_history(request):
    logger.debug(f'running retrieve_chat_history() ...  function started')

    user = request.user
    conversation_id = user.aichat_userprofile.conversation_id

    messages = ChatHistory.objects.filter(session_id__startswith=f"{user.id}--")
    logger.debug(f'running retrieve_chat_history() ... messages is: { messages }')

    message_data = []
    for message in messages:
        message_data.append({
            'id': message.id,
            'session_id': message.session_id,
            'message': message.message,
            'timestamp': message.timestamp,
        })
    logger.debug(f'running retrieve_chat_history() ... message_data is: { message_data }, conversation_id is: {conversation_id}')
    return JsonResponse({'status': 'success', 'message_data': message_data, 'conversation_id': conversation_id})


# -------------------------------------------------------------------------


@require_http_methods(["GET"])
@login_required(login_url='aichat_users:login')
def retrieve_model_details(request):
    logger.debug(f'running aichat_chat app, retrieve_model_details ... view started')


    # Pull the logged-in user object
    user = request.user
    preprocessing_model = user.aichat_userprofile.preprocessing_model
    vectorization_model = user.aichat_userprofile.tokenization_and_vectorization_model
    retriever_model = user.aichat_userprofile.retriever_model
    # Retrieve the link_description from preprocessing_models_supported
    preprocessing_model_link = preprocessing_models_supported.get(preprocessing_model, {}).get('link_description') or None
    vectorization_model_link = tokenization_and_vectorization_models_supported.get(vectorization_model, {}).get('link') or None
    vectorization_model_similarity_metric = tokenization_and_vectorization_models_supported.get(vectorization_model, {}).get('similarity_metric') or None
    retriever_model_link = retriever_models_supported.get(retriever_model, {}).get('link') or None

    logger.debug(f'running retrieve_model_details() ... '
                 f'user is: { user }, ' 
                 f'preprocessing_model is: { preprocessing_model }, and '
                 f'vectorization_model is: { vectorization_model }')
    
    if preprocessing_model_link:
        logger.debug(f'running retrieve_model_details ... '
                    f'preprocessing_model_link is: { preprocessing_model_link }, '
                    f'vectorization_model_link is: { vectorization_model_link }, '
                    f'vectorization_model_similarity_metric is: {vectorization_model_similarity_metric}, and '
                    f'retriever_model_link is: { retriever_model_link }')
        return JsonResponse({'status': 'success', 'preprocessing_model_link': preprocessing_model_link, 'vectorization_model_link': vectorization_model_link, 'vectorization_model_similarity_metric': vectorization_model_similarity_metric, 'retriever_model_link': retriever_model_link})
    
    # This handles if it's auto-detect (e.g no specific model designated)
    else:
        logger.debug(f'running retrieve_model_details ... no link_description found for model: {preprocessing_model}')
        return JsonResponse({'status': 'success', 'preprocessing_model_link': preprocessing_model_link, 'vectorization_model_link': vectorization_model_link, 'vectorization_model_similarity_metric': vectorization_model_similarity_metric, 'retriever_model_link': retriever_model_link})
    
    
#-------------------------------------------------------------------------


@require_http_methods(["POST"])
@login_required(login_url='aichat_users:login')
def update_profile(request):
    logger.info(f'running update_profile() ... view started')

    # Pull the logged-in user object
    user = request.user

    # Handle POST requests (form submission)
    if request.method == 'POST':
        logger.debug(f'running update_profile() ... request.method is: { request.method }')

        # Get the user's profile
        user_profile = user.aichat_userprofile

        # Get the field to update from POST request
        field_name = request.POST.get('field')
        field_value = request.POST.get('value')

        # Handle special case for suggest_expert switch, which always returns 'on'
        if field_name == 'suggest_experts':
            field_value = not user.aichat_userprofile.suggest_experts
        if field_name == 'preprocessing':
            field_value = not user.aichat_userprofile.preprocessing
        logger.debug(f'running update_profile_vew ... updated field_name: { field_name } to field_value: { field_value }')

        # Handle special case for rag_sources_used wherein the user skips websites (setting rag_sources_used to none) and then also skips docs (setting rag_souces_used to none)
        if field_name == 'rag_sources_used' and field_value == 'website-index':
            
            # If the previous value is document (e.g. user previously skipped website) and then submitted value is website-index, that means user tried to skip both
            if user.aichat_userprofile.rag_sources_used == 'document': 
                logger.info(f'running update_profile() ... user tried to skip both websites and docs- throwing error.')
                return JsonResponse({'status': 'error', 'message': 'Please select websites or documents to use. Cannot skip both.'}, status=400)
            else:
                logger.info(f'running update_profile() ... user saved website and skipped document. Setting rag_sources_used to "website"')
                field_value = 'website'
              

        # Do the following if there is a field_name and it's a valid part of user_profile
        if field_name and hasattr(user_profile, field_name): 
            setattr(user_profile, field_name, field_value)  # Dynamically set the field's value
            user_profile.save()
            logger.info(f'running update_profile() ... Updated {field_name} to {field_value} for user {user.username}')
            return JsonResponse({'status': 'success', 'message': f'{field_name} updated successfully!'})
        
        else:
            logger.error(f'running update_profile() ... Invalid field: {field_name}')
            return JsonResponse({'status': 'error', 'message': 'Invalid field.'}, status=400)

    # If the submission isn't POST, throw an error
    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=400)






# VIEWS
#-------------------------------------------------------------------------


@require_http_methods(["GET"])
@login_required(login_url='aichat_users:login')
def index_view(request):
    logger.debug(f'running aichat_chat app, index_view ... view started')

    # Pull language data
    current_language = request.GET.get('lang', request.session.get('django_language', 'en'))
    if current_language:
        translation.activate(current_language)
        request.session['django_language'] = current_language
    
    # Pull user and timestamp data
    user = request.user
    session_id = request.session.session_key
    timestamp = timezone.localtime(timezone.now()).strftime('%H:%M, %d-%m-%Y')
    logger.debug(f'running aichat_users app, index_view ... user is: {user},'
                 f'current_language is: {current_language}, session_id is: { session_id },'
                 f'timestamp is { timestamp }'
                 )
    
    # Ensure user has a UserProfile, create if it doesn't exist
    profile, created = UserProfile.objects.get_or_create(user=user)
    if created:
        logger.debug(f"running aichat_users app, index_view ... new UserProfile created for user: {user.username}, Profile : {profile}")
    else:
        logger.debug(f"running aichat_users app, index_view ... existing UserProfile found for user: {user.username}, Profile ID: {profile}")


    # Check if this session_id exists in any of the user's conversations
    session_exists = ChatHistory.objects.filter(
        session_id__startswith=f"{user.id}--",
        session_id__contains=session_id
    ).exists()

    # Only create new conversation_id if this is truly a new session
    if not session_exists:
        conversation_id = f'{user.id}--{session_id}'
        profile.conversation_id = conversation_id
        profile.save()
        logger.debug(f'running index_view ... new session detected, setting conversation_id to: {conversation_id}')


    # If the language currently in use by the browser is not the user's preferred language, then update that field in the DB
    if current_language != profile.preferred_language :
        profile.preferred_language = current_language
        profile.save()
        logger.debug(f'running aichat_users app, index_view ... user is: { user }, updating preferred_language to: { current_language }')
     
    # Initialize ProfileForm with the user object
    profile_form = ProfileForm(user=user)

    initial_data = {
        'first_name': user.first_name,
        'timestamp': timestamp,
    }
    input_form = InputForm(initial=initial_data)

    context = {
        'current_language': current_language,
        'current_language_translated': supported_languages_selected[current_language]['translated_name'],
        'input_form': input_form,
        'profile_form': profile_form,
        'route_used': 'index_view',
        'session_id': session_id,
        'supported_languages': supported_languages_selected,
        'user': user,
        'user_profile': profile,
    }
    logger.debug(f'running aichat_chat app, index_view ... context passed to the template is: {context}')
    
    return render(request, 'aichat_chat/index.html', context)
        


# -------------------------------------------------------------------------

@require_http_methods(['GET', 'POST'])
@login_required(login_url='aichat_users:login')
def stream_response(request):

    user = request.user

    # POST: Handles form submission, validates the form, and stores the input along with a generated stream_id in the session.
    if request.method == 'POST':
        
        input_form = InputForm(request.POST) # Display the InputForm

        if input_form.is_valid(): # Check for form validity
            logger.debug(f'running stream_response() ... user submitted via post and form passed validation')

            input_text = input_form.cleaned_data.get('user_input')
            conversation_id = user.aichat_userprofile.conversation_id
            logger.debug(f'running stream_response() ...' 
                         f'input_text is: { input_text },'  
                         f'conversation_id is: { conversation_id }'
                         )

            stream_id = str(uuid.uuid4()) # Create a unique stream ID which will be passed back to JS and used to establish the streaming connection
            logger.debug(f'running stream_response() ... stream_id generated is: { stream_id }')

            # Store the context for this stream ID in session data
            request.session[stream_id] = { 
                'user_input': input_text,
                'conversation_id': conversation_id,
                'first_name': user.first_name,
                'timestamp': now().strftime('%H:%M, %d-%m-%Y')
            }

            # This is a check to ensure the stream_id is stored in the session
            if stream_id in request.session:
                logger.debug(f'running stream_response() ... stream_id {stream_id} successfully stored in session')
            else:
                logger.debug(f'running stream_response() ... failed to store stream_id {stream_id} in session')
            

            # Return JSON response with the stream_id
            response_data = {"stream_id": stream_id}
            logger.debug(f'Returning response: {response_data}')
            return JsonResponse(response_data)

        # If submission = POST && the form fails validation, return a JSON with an error message
        else:
            logger.debug(f'Stream response view: form validation failed: { input_form.errors }')
            return JsonResponse({'success': False, 'errors': input_form.errors}, status=400)

    
    # GET: Uses the stream_id to retrieve the stored context and streams the AI response back to the client
    elif request.method == 'GET':
        stream_id = request.GET.get('stream_id') # Get the stream_id provided by the JS
        
        # If stream_id is missing, throw an error
        if not stream_id or stream_id not in request.session:
            return JsonResponse({"error": "Invalid or missing stream ID"}, status=400)

        context = request.session.pop(stream_id) # This uses stream_id to retrieve the context stored in session
        return stream_response_to_user(
            conversation_id=context['conversation_id'],
            user_input=context['user_input'],
            user=user,
            )
    







