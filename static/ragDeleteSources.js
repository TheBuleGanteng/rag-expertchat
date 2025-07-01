// The JS below clears existing RAG sources (URLs and docs)
import { csrfToken } from './utils.js'
import { showSpinner, hideSpinner } from './loadingspinner.js';

document.addEventListener('DOMContentLoaded', function () {

    // Determine the base path dynamically
    const basePath = window.location.pathname.includes('/rag/') ? '/rag' : '';
    const currentApp = window.location.pathname.includes('/avatar/') ? 'avatar' : 'aichat';
    console.log(`running ragDeleteSources.js ... basePath is: ${basePath}`);
    console.log(`running ragDeleteSources.js ... window.location.pathname is: ${window.location.pathname}`);
    console.log(`running ragDeleteSources.js ... currentApp is: ${currentApp}`);

    // Calls aichat_chat/views.py/delete_rag_sources to delete all ragsources and vectors from SQL, all files from disk, and all vectors from pinecone 
    
    // Event listener for the delete button    
    function jsSetDeleteAllRagMaterialsEventListeners() {
        console.log(`running jsDeleteAllRagMaterials(), ... function started`)
        const deleteAllRagMaterialsBtn = document.getElementById('delete-all-rag-materials-btn');
        const preprocessingSwitch = document.getElementById('preprocessing')
        const preprocessingModel = document.getElementById('preprocessing-model')
        const vectoriationModel = document.getElementById('vectorization-model')
        const similarityMetric = document.getElementById('similarity-metric')
        
        if (deleteAllRagMaterialsBtn) {
            deleteAllRagMaterialsBtn.addEventListener('click', function(event) {
                console.log(`running ragsources.js ... RagDocForm submission detected`);
                jsShowConfirmationAndDelete();
            });
        }

        if (preprocessingSwitch) {
            preprocessingSwitch.addEventListener('change', function(event) {
                console.log(`running ragsources.js ... preprocessingSwitch change detected`);
                jsShowConfirmationAndDelete();
            });
        }

        if (preprocessingModel) {
            preprocessingModel.addEventListener('change', function(event) {
                console.log(`running ragsources.js ... preprocessingModel change detected`);
                jsShowConfirmationAndDelete();
            });
        }

        if (vectoriationModel) {
            vectoriationModel.addEventListener('change', function(event) {
                console.log(`running ragsources.js ... vectoriationModel change detected`);
                jsShowConfirmationAndDelete();
            });
        }

        if (similarityMetric) {
            similarityMetric.addEventListener('change', function(event) {
                console.log(`running ragsources.js ... vectoriationModel change detected`);
                jsShowConfirmationAndDelete();
            });
        }
    }
    jsSetDeleteAllRagMaterialsEventListeners();



    //----------------------------------------------------------------------------



    // Function to show confirmation modal and if confirm is clicked, delete all source materials and reload the page
    function jsShowConfirmationAndDelete() {
        console.log(`running jsShowConfirmationAndDelete`)
        
        
        const deleteRagSourcesUrl = `${basePath}/${currentApp}/delete_rag_sources/`;
        const confirmationModalElement = document.getElementById('confirmationModal');
        const confirmationModal = new bootstrap.Modal(confirmationModalElement);
        const confirmDeleteBtn = document.getElementById('confirmDeleteBtn');

        confirmationModal.show();

        // Remove any previous event listener to prevent multiple submissions
        confirmDeleteBtn.replaceWith(confirmDeleteBtn.cloneNode(true));
        const newConfirmDeleteBtn = document.getElementById('confirmDeleteBtn');

        // Add a new event listener for the "Confirm" button
        newConfirmDeleteBtn.addEventListener('click', function () {
            console.log(`running ragsources.js ... Confirm button clicked`);

            showSpinner();

            // Submit the form via fetch
            fetch(deleteRagSourcesUrl, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken,  // Add CSRF token
                    'Content-Type': 'application/json',
                },
            })
            .then(response => response.json())  // Parse the JSON response
            .then(data => {
                if (data.status === 'success') {
                    console.log('Successfully deleted all RAG materials.');
                    alert(data.message);  // Display success message as an alert
                    window.location.reload();  // Reload the page after successful deletion
                } else {
                    console.error('Error submitting form:', data.errors);
                    alert(data.message);  // Display error message
                }
                hideSpinner();  // Hide the spinner after processing
            })
            .catch(error => {
                console.error('Error during form submission:', error);
                alert(`jsDeleteAllRagMaterials ... An unexpected error occurred: ${ error }`);
                hideSpinner();  // Hide the spinner in case of error
            });
            
            // Hide the modal after the "Confirm" button is clicked
            confirmationModal.hide();
        });
    }
    // Initialize event listeners
    jsSetDeleteAllRagMaterialsEventListeners();

});