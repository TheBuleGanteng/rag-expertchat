// The JS below manages the forms controlling submission of URL RAG sources
import { generateEmbeddings, handleAjaxFormSubmission, transitionAccordionOneToTwo, transitionAccordionTwoToOne,  transitionAccordionTwoToThree} from './utils.js'
import { showSpinner, hideSpinner } from './loadingspinner.js';

document.addEventListener('DOMContentLoaded', function () {


    // Injects the html for RAG URL formset and manages submission of RagUrlFormSet
    function populateRagUrlFormset() {
        console.log(`running ragsources.js ... function started`);

        const RagUrlFormCardBody = document.getElementById('RagUrlFormCardBody')
        if (RagUrlFormCardBody) {

            // Step 1: Make an AJAX call to initially load index html with the formset, including the current user data from the DB
            const ragUrlsViewUrl = '/aichat/rag_url/';
            console.log(`running ragsources.js ... ragUrlsUrl is: ${ ragUrlsViewUrl }`);

            fetch(ragUrlsViewUrl, {
                method: 'GET',  // Assuming this is a GET request
                headers: {
                    'X-Requested-With': 'XMLHttpRequest', // This tells Django it's an AJAX request
                }
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                // Check what data type is coming back from the get request to the view
                const contentType = response.headers.get('content-type');
                if (contentType && contentType.includes('application/json')) {
                    return response.json();  // If the response is JSON, parse it as JSON
                } else {
                    return response.text();  // If the response is not JSON, parse it as text
                }
            })
            .then(data => {
                RagUrlFormCardBody.innerHTML = data.html; // Inject the formset into the container
                console.log(`running ragsources.js ... formset injected to container and event listeners initially applied to add and remove icons`);

                // Now that the initial fetch has happened, select the newly-populated UrlForm
                const ragUrlForm =  document.getElementById('RagUrlForm'); // The form that was injected into index.html via the JS above
                if (ragUrlForm) {
                    
                    // Listen for clicks on the add and remove icons
                    ragUrlForm.addEventListener('click', function (event) {
                        const target = event.target;

                        // Add a new row when the 'add' icon is clicked
                        if (target.id === 'add-additional-url-icon') {
                            console.log('running ragsources.js ... remove-icon-url event listener detected click, running addFormToFormset');
                            event.preventDefault();
                            addFormToFormset();
                        }

                        // Remove the relevent row when it's associated 'remove' icon is clicked
                        if (target.getAttribute('name') === 'remove-icon-url') {
                            console.log('running ragsources.js ... remove-icon-url event listener detected click, running removeFormFromFormset(formRow)');
                            event.preventDefault();  // Prevent default behavior
                            const formRow = target.closest('.row');  // Find the closest form row
                            removeFormFromFormset(formRow); // Call function to remove the form row
                        }
                    });        
                    
                    // Listen if user clicks on the 'skip' button and update profile accordingly
                    setRagSourcesUsed();
        
                    // Listen for UrlForm submission
                    ragUrlForm.addEventListener('submit', function(event) {
                        console.log(`running ragsources.js ... form submission detected`);

                        event.preventDefault(); // Prevent default form submission
                        const formData = new FormData(ragUrlForm)  // Collects the form data submitted

                        handleAjaxFormSubmission(ragUrlsViewUrl, formData)
                        .then(data => {
                            if (data.status === 'success') {
                                console.log('Form submitted successfully!');
                                alert(data.message);

                                // Inject the updated formset HTML back into the page after successful form submission
                                RagUrlFormCardBody.innerHTML = data.html;
                                
                                transitionAccordionOneToTwo();

                            } else {
                                console.error('Error submitting form:', data.errors);
                                alert(data.message);
                            }
                            hideSpinner();
                        })
                        .catch(error => {
                            console.error('Error during form submission:', error);
                            alert(`running populateUrlRagFormset ... An unexpected error occurred: ${ error }`);
                            hideSpinner();
                        });
                    })
                }
            })
        }
    }
    populateRagUrlFormset();



    //----------------------------------------------------------------------------


    
    // Adds a url line to the formset
    function addFormToFormset() {
        const formsetContainer = document.getElementById('formset-container'); // The container inside the form that holds the URL records
        const totalFormsInput = document.querySelector('#id_form-TOTAL_FORMS'); // Fetch the total forms input
        const totalForms = parseInt(totalFormsInput.value); // Fetch the current number of forms dynamically
        console.log(`running ragsources.js ... before running addFormToFormset, totalFormsInput.value is: ${ totalFormsInput.value }`);

        // Create a new row div for the form inputs
        const rowDiv = document.createElement('div');
        rowDiv.classList.add('row', 'align-items-center', 'mb-2');

        // Add label for new URL
        const labelDiv = document.createElement('div');
        labelDiv.classList.add('col-1', 'fw-bold');
        labelDiv.innerText = `URL ${totalForms + 1}`;
        rowDiv.appendChild(labelDiv);

        // Create the URL input field
        const urlDiv = document.createElement('div');
        urlDiv.classList.add('col-6');
        const urlInput = document.createElement('input');
        urlInput.type = 'url';
        urlInput.name = `form-${totalForms}-url`;
        urlInput.id = `id_form-${totalForms}-url`;
        urlInput.classList.add('form-control');
        urlDiv.appendChild(urlInput);
        rowDiv.appendChild(urlDiv);

        // Create the checkbox label and checkbox for include_subdomains
        const subdomainsDiv = document.createElement('div');
        subdomainsDiv.classList.add('col');
        const subdomainsLabel = document.createElement('label');
        subdomainsLabel.setAttribute('for', `id_form-${totalForms}-include_subdomains`);
        subdomainsLabel.setAttribute('class', `me-1`);
        subdomainsLabel.innerText = 'Include Subdomains:';
        const subdomainsInput = document.createElement('input');
        subdomainsInput.type = 'checkbox';
        subdomainsInput.name = `form-${totalForms}-include_subdomains`;
        subdomainsInput.id = `id_form-${totalForms}-include_subdomains`;
        subdomainsInput.classList.add('form-check-input');
        subdomainsDiv.appendChild(subdomainsLabel);
        subdomainsDiv.appendChild(subdomainsInput);
        rowDiv.appendChild(subdomainsDiv);

        // Create the hidden remove checkbox associated with the new row
        const deleteInput = document.createElement('input');
        deleteInput.type = 'checkbox';
        deleteInput.name = `form-${totalForms}-DELETE`;
        deleteInput.id = `id_form-${totalForms}-DELETE`;
        deleteInput.style.display = 'none'; // Hidden DELETE checkbox
        rowDiv.appendChild(deleteInput);
        
        
        // Create the remove icon for the new row, assuming there is at least 2 rows
        const removeIconDiv = document.createElement('div');
        removeIconDiv.setAttribute('class', 'col-1');
        const removeIcon = document.createElement('i');
        removeIcon.setAttribute('class', 'bi bi-x-circle-fill remove-icon fs-4');
        removeIcon.setAttribute('name', 'remove-icon-url');
        removeIconDiv.appendChild(removeIcon);
        rowDiv.appendChild(removeIconDiv);
        
        // Append the new row to the formset container
        formsetContainer.appendChild(rowDiv);
        
        // Update the total forms in the management form
        totalFormsInput.value = totalForms + 1;
        console.log(`running ragsources.js ... after running addFormToFormset, totalFormsInput.value is: ${ totalFormsInput.value }`);
    }
    


    //----------------------------------------------------------------------------


    // Removes a url line from the formset
    function removeFormFromFormset(formRow) {

        // Find the DELETE checkbox inside the formRow
        const deleteCheckbox = formRow.querySelector('input[name*="DELETE"]');  // Target the remove-checkbox
        console.log(`running ragsources.js ... found deleteCheckbox: ${ deleteCheckbox }`);
        
        if (deleteCheckbox) {
            // Mark the form as deleted
            deleteCheckbox.checked = true;

            // Hide the form row (but don't remove it from the DOM)
            formRow.style.display = 'none';
        }
    }
    


    //----------------------------------------------------------------------------

    
    
    // Updates ProfileForm to set user.aichat_userprofile.rag_sources_used to 'docs' if 'Don't use URLs' button is clicked
    function setRagSourcesUsed() {
        const dontUseUrlsButton = document.getElementById('dont-use-urls-button')
        const saveUrlsButton = document.getElementById('urls-save-button')
        const dontUseDocsButton = document.getElementById('dont-use-docs-button')
        const saveDocsButton = document.getElementById('docs-save-button')

        if (dontUseUrlsButton) {
            dontUseUrlsButton.addEventListener('click', function(event) {
                console.log(`running setRagSourcesUsed() ... dontUseUrlsButton click detected`);

                // Prepare data to send in the request
                const formData = new FormData();
                formData.append('field', 'rag_sources_used');
                formData.append('value', 'document');
                
                const updateProfileUrl = '/aichat/update_profile/';
                console.log(`running setRagSourcesUsed() ... updateProfileUrl is: ${ updateProfileUrl }`);

                handleAjaxFormSubmission(updateProfileUrl, formData)
                .then(data => {
                    if (data.status === 'success') {
                        console.log('running setRagSourcesUsed() ... profile updated successfully');
                        transitionAccordionOneToTwo();

                    } else {
                        console.error(`running setRagSourcesUsed() ... error submitting form: ${ data.errors}`);
                        alert('Failed to update profile');
                    }
                })
                .catch(error => {
                    console.error(`running setRagSourcesUsed() ... error during form submission: ${ error}`);
                    alert(`running setRagsourcesUsed ... An unexpected error occurred: ${ error }`);
                });
            });
        };

        if (saveUrlsButton) {
            saveUrlsButton.addEventListener('click', function(event) {
                console.log(`running setRagSourcesUsed() ... saveUrlsButton click detected`);

                // Prepare data to send in the request
                const formData = new FormData();
                formData.append('field', 'rag_sources_used');
                formData.append('value', 'all');
                
                const updateProfileUrl = '/aichat/update_profile/';
                console.log(`running setRagSourcesUsed() ... updateProfileUrl is: ${ updateProfileUrl }`);

                handleAjaxFormSubmission(updateProfileUrl, formData)
                .then(data => {
                    if (data.status === 'success') {
                        console.log('running setRagSourcesUsed() ... profile updated successfully');
                        transitionAccordionOneToTwo();

                    } else {
                        console.error(`running setRagSourcesUsed() ... error submitting form: ${ data.errors}`);
                        alert('Failed to update profile');
                    }
                })
                .catch(error => {
                    console.error(`running setRagSourcesUsed() ... error during form submission: ${ error}`);
                    alert(`running setRagsourcesUsed ... An unexpected error occurred: ${ error }`);
                });
            });
        };

        if (dontUseDocsButton) {
            dontUseDocsButton.addEventListener('click', async function(event) {
                console.log(`running setRagSourcesUsed() ... dontUseDocsButton click detected`);
                
                showSpinner();

                // Prepare data to send in the request
                const formData = new FormData();
                formData.append('field', 'rag_sources_used');
                formData.append('value', 'website-index');

                const updateProfileUrl = '/aichat/update_profile/';
                console.log(`running setRagSourcesUsed() ... updateProfileUrl is: ${ updateProfileUrl }`);

                // This first (outer) try-catch updates user.aichat_userprofile.rag_sources_used
                try {
                    const data = await handleAjaxFormSubmission(updateProfileUrl, formData) 
                    if (data.status === 'success') {
                        // If the user successfully skips docs (eg. the rag_sources_used = web), then proceed to generate embeddings
                        console.log('running setRagSourcesUsed() ... profile updated successfully, now triggering generateEmbeddings()');

                        // This second (innter) try-catch runs generateEmbeddings()
                        try {
                            const response = await generateEmbeddings();
                            if (response.status === 'success') {
                                console.log('running ragsources.js ... generateEmbeddings ran successfully:', response);                      
                                populateRagDocForm();  // Refresh the form with the newly uploaded files
                                transitionAccordionTwoToThree(); 
                                alert(response.message);
                            } else {
                                console.log('running ragsources.js ... error running generateEmbeddings:', response);
                                alert(response.message);   
                            }
                        } catch (error) {
                            console.error(`running setRagSourcesUsed() ... error submitting form: ${ data.errors}`);
                            alert(`Please select websites and/or documents to use. Cannot skip both. Error: ${ data.errors }`);
                        }

                    // If the outer try-catch's response != success    
                    } else {
                        console.error(`running setRagSourcesUsed() ... error submitting form: ${ data.errors}`);
                        alert(`Please select websites and/or documents to use. Cannot skip both. Error: ${ data.errors }`);
                    }
                
                // If the outer try-catch's try fails
                } catch(error) {
                    console.error(`running setRagSourcesUsed() ... error during form submission: ${ error}`);
                    alert(`Please select websites and/or documents to use. Cannot skip both. Error: ${ error }`);
                    transitionAccordionTwoToOne();
                };
            
                hideSpinner();    
            });
        }         
        
        if (saveDocsButton) {
            saveDocsButton.addEventListener('click', function(event) {
                console.log(`running setRagSourcesUsed() ... saveDocsButton click detected. No change to rag_sources_used is needed`);
                // Note: no need to update rag_sources_used here, because set to either "all" (if saved websites) or "document" if skipped websites
            });
        };
    };    
    
});