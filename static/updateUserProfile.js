import { debounce, updateProfileForm } from './utils.js'

document.addEventListener('DOMContentLoaded', function() {
    console.log(`running updateUserProfile.js ... DOM content loaded`);
    console.log(`running updateUserProfile.js ... current origin is: ${ window.location.origin }`);

    // Determine the base path dynamically
    const basePath = window.location.pathname.includes('/rag/') ? '/rag' : '';
    const currentApp = window.location.pathname.includes('/avatar/') ? 'avatar' : 'aichat';
    console.log(`running updateUserProfile.js ... basePath is: ${basePath}`);
    console.log(`running updateUserProfile.js ... window.location.pathname is: ${window.location.pathname}`);
    console.log(`running updateUserProfile.js ... currentApp is: ${currentApp}`);
    
    // The JS below detects a change in elements w/ attribute form-element="profileForm"
    // A change in any such element is saved to the logged-in user's profile
    
    // Select all elements with the attribute below
    const profileFields = document.querySelectorAll('[form-element="profileForm"]');
    console.log(`running updateUserProfile.js ... profileFields is: ${ profileFields }`)

    // This first chunk of JS applies the event listeners to the profileForm elements, 
    // calling updateProfileForm if one of those elements is changed by the user.
    profileFields.forEach((field) => {
        console.log(`running updateUserProfile.js ... adding eventListener for ${ field.name }`);    


        // Define the debounced event
        const debouncedUpdateProfileForm = debounce(function(event) {
            console.log(`running updateUserProfile.js ... change detected in profileForm element ${field.name}, updating to ${event.target.value}`);
            updateProfileForm(field.name, field.value);
        }, 400);

        // Add the eventListener, withthe debounced event as the corresponding action
        field.addEventListener('input', debouncedUpdateProfileForm);
    });



    //------------------------------------------------------------------------------

    

    // Sets eventListeners that will trip updateModelInfo() to show additional info (links, recommended no. of dimensions, etc.) for the preprocessing and vectorization models selected
    function showModelInfo() {
        const preprocessingModel = document.getElementById('preprocessing-model');
        const vectorizationModel = document.getElementById('tokenization-and-vectorization-model')
        const retrieverModel = document.getElementById('retriever-model')
        const debouncedUpdateModelInfo = debounce(updateModelInfo, 400)

        if (preprocessingModel) {
            // Do initial fetch on page load
            updateModelInfo();

            // Add the event listener to preprocessing model
            preprocessingModel.addEventListener('change', function(event) {
                console.log(`running showModelInfo() ... click on element w/ id=preprocessing-model detected`)

                // Upon detecting a change, re-run the fetch to refresh the link 
                debouncedUpdateModelInfo();
            })
        }
        if (vectorizationModel) {
            // Add the event listener to vectorization model
            vectorizationModel.addEventListener('change', function(event) {
                console.log(`running showModelInfo() ... click on element w/ id=tokenization-and-vectorization-model detected`)

                // Upon detecting a change, re-run the fetch to refresh the link 
                debouncedUpdateModelInfo();
            })
        }
        if (retrieverModel) {
            // Add the event listener to vectorization model
            retrieverModel.addEventListener('change', function(event) {
                console.log(`running showModelInfo() ... click on element w/ id=retriever-model detected`)

                // Upon detecting a change, re-run the fetch to refresh the link 
                debouncedUpdateModelInfo();
            })
        }
    }
    showModelInfo();



    //------------------------------------------------------------------------------



    // Works with showModelInfo() to show additional info (links, recommended no. of dimensions, etc.) for the preprocessing and vectorization models selected
    function updateModelInfo() {

        // Step 1: Make an AJAX call to initially load index html with the formset, including the current user data from the DB
        const modelDataUrl = `${basePath}/${currentApp}/model_data/`;
        console.log(`running updateModelInfo() ... modelDataUrl is: ${ modelDataUrl }`);

        const  preprocessingModelLinkDiv = document.getElementById('preprocessing-model-additional-info-link');
        const vectorizationModelLinkDiv = document.getElementById('tokenization-and-vectoriation-model-additional-info-link')
        const similarityMetricRecommendationDiv = document.getElementById('similarity-metric-additional-info-recommendation')
        const retrieverModelLinkDiv = document.getElementById('retriever-model-additional-info-link')

        if (preprocessingModelLinkDiv || vectorizationModelLinkDiv || similarityMetricRecommendationDiv || retrieverModelLinkDiv) {

            fetch(modelDataUrl)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`running updateModelInfo ... HTTP error! status: ${response.status}, error: ${ response.error }`);
                }
                return response.json();
            })
            .then(data => {
                if (data.status === 'success') {
                    console.log(`running updateModelInfo() ... successfully updated preprocessingModelLinkDiv. preprocessing_model_link is: ${data.preprocessing_model_link} and vectorization_model_link is: ${ data.vectorization_model_link }`);
                    // Update preprocessing model link if the div is present
                    if (preprocessingModelLinkDiv) {
                        preprocessingModelLinkDiv.href = data.preprocessing_model_link;
                    }
                    // Update vectorization model link if the div is present
                    if (vectorizationModelLinkDiv) {
                        vectorizationModelLinkDiv.href = data.vectorization_model_link;
                    }
                    // Update similarityMetricRecommendationDiv if the div is present
                    if (similarityMetricRecommendationDiv) {
                        similarityMetricRecommendationDiv.innerHTML = data.vectorization_model_similarity_metric;
                    }
                    if (retrieverModelLinkDiv) {
                        retrieverModelLinkDiv.href = data.retriever_model_link
                    }
                } else {
                    console.error(`running updateModelInfo() ... error submitting form: ${data.errors}`);
                    alert(data.message);  // Display error message
                }
            })
            .catch(error => {
                console.error(`running updateModelInfo() ... Error during form submission: ${error}`);
                alert(`running updateModelInfo() ... An unexpected error occurred: ${ error }`);
            });
        }
    }

});
    
