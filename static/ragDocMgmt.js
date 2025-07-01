// The JS below manages the forms controlling submission of document RAG sources
import { csrfToken, transitionAccordionTwoToThree} from './utils.js'
import { hideSpinner } from './loadingspinner.js';

document.addEventListener('DOMContentLoaded', function () {
    console.log(`running ragDocMgmt.js ... DOM content loaded`);
    console.log(`running ragDocMgmt.js ... current origin is: ${ window.location.origin }`);

    // Determine the base path dynamically
    const basePath = window.location.pathname.includes('/rag/') ? '/rag' : '';
    const currentApp = window.location.pathname.includes('/avatar/') ? 'avatar' : 'aichat';
    console.log(`running ragDocMgmt.js ... basePath is: ${basePath}`);
    console.log(`running ragDocMgmt.js ... currentApp is: ${currentApp}`);
    console.log(`running ragDocMgmt.js ... window.location.pathname is: ${window.location.pathname}`);

    
    // Injects the html from rag_docs_form.html and initial population/submission of RagDocForm
    function populateRagDocForm() {
        console.log(`running ragDocMgmt.js ... populateRagDocForm() function started`);

        const RagDocsFormCardBody = document.getElementById('RagDocsFormCardBody')
        if (RagDocsFormCardBody) {

            // Step 1: Make an AJAX call to initially load index html with the formset, including the current user data from the DB
            fetch(`${basePath}/${currentApp}/rag_docs/`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}, error: ${ response.error }`);
                }
                return response.text();
            })
            .then(html => {
                RagDocsFormCardBody.innerHTML = html; // Inject the formset into the container
                console.log(`running ragDocMgmt.js ... rag_docs_form.html injected into index.html`);

                setRemoveFileIconListeners();
                console.log(`running ragDocMgmt.js ... setRemoveFileIconListeners(); run on inital files, if any.`);



                // Now that the initial fetch has happened, select the newly-populated RagDocForm
                const RagDocForm =  document.getElementById('RagDocForm'); // The form that was injected into index.html via the JS above
                if (RagDocForm) {

                    // Start: Drag and drop file upload --------------------------------------------
                    const fileUploadArea = document.getElementById("file-upload-and-instructions-area");
                    let fileElem = document.getElementById("fileElem");
                    let directoryElem = document.getElementById("directoryElem");
                    let selectDirectoryLink = document.getElementById("select-directory-link");
                    
                    if (fileUploadArea) {
                        console.log(`running ragDocMgmt.js ... fileUploadArea detected`);

                        // Check if there are existing files
                        let existingFilesCount = document.getElementById('file-list').dataset.existingFiles;
                        console.log(`Existing files count: ${existingFilesCount}`);
                        
                        // Move files declaration inside function scope
                        let files = fileElem.files;  // Assign files to the file input
                        console.log(`running ragDocMgmt.js ... files is: ${ files }`);

                        ["dragenter", "dragover", "dragleave", "drop"].forEach((eventName) => {
                            fileUploadArea.addEventListener(eventName, preventDefaults, false);
                            document.body.addEventListener(eventName, preventDefaults, false);
                        });

                        ["dragenter", "dragover"].forEach((eventName) => {
                            fileUploadArea.addEventListener(eventName, highlight, false);
                        });

                        ["dragleave", "drop"].forEach((eventName) => {
                            fileUploadArea.addEventListener(eventName, unhighlight, false);
                        });

                        fileUploadArea.addEventListener("drop", handleDrop, false);

                        fileUploadArea.addEventListener("click", (e) => {
                            if (!e.target.isEqualNode(selectDirectoryLink)) {
                                fileElem.click();
                            }
                        });

                        selectDirectoryLink.addEventListener("click", (e) => {
                            e.preventDefault();
                            directoryElem.click();
                        });

                        function preventDefaults(e) {
                            e.preventDefault();
                            e.stopPropagation();
                        }

                        function highlight(e) {
                            fileUploadArea.classList.add("highlight");
                        }

                        function unhighlight(e) {
                            fileUploadArea.classList.remove("highlight");
                        }

                        function handleDrop(e) {
                            let dt = e.dataTransfer;
                            let files = dt.files;
                            handleFiles(files, existingFilesCount);
                        }

                        fileElem.addEventListener("change", function (e) {
                            handleFiles(this.files, existingFilesCount);
                        });

                        directoryElem.addEventListener("change", function (e) {
                            handleFiles(this.files, existingFilesCount);
                        });

                        handleFiles(files, existingFilesCount);
                        setRagDocFormEventListener(RagDocForm);    
                    };
                }
            })
        }
    }
    populateRagDocForm();



    //----------------------------------------------------------------------------



    // Sets event listener that handles RagDocForm submission via AJAX to prevent page reload and update DOM accordingly         
    function setRagDocFormEventListener(RagDocForm) {

        RagDocForm.addEventListener('submit', function(event) {
            event.preventDefault();  // Prevent the form from submitting the default way (page reload)
            console.log(`running ragDocMgmt.js ... RagDocForm submission detected`);
            
            // Submit the form via fetch
            fetch(`${basePath}/${currentApp}/rag_docs/`, {
                method: 'POST',
                body: new FormData(RagDocForm),
                headers: {
                    'X-CSRFToken': csrfToken
                },
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}, error: ${ response.error }`);
                }
                return response.json();
            })  
            // Parse the JSON response
            .then(data => {
                if (data.status === 'success') {
                    console.log('Form submission successful!');
                    alert(data.message);  // Display success message as an alert
                    transitionAccordionTwoToThree();  // Update the DOM to transition the accordion
                } else {
                    console.error('Error submitting form:', data.errors);
                    alert(data.message);  // Display error message
                }
                hideSpinner();  // Hide the spinner after processing
            })
            .catch(error => {
                console.error('Error during form submission:', error);
                alert(`running ragDocMgmt.js ... An unexpected error occurred: ${ error }`);
                hideSpinner();  // Hide the spinner in case of error
            });
        });
    }
    


    //----------------------------------------------------------------------------



    // Takes the files passed in as an argument, updates the fileUploadArea accordingly, and re-sets the doc upload form  
    function handleFiles(files, existingFilesCount) {
        let fileList = document.getElementById('file-list');

        if (files.length === 0 && existingFilesCount == 0) {
            jsResetForm();  // Reset the form if no files are present
            hideSpinner();
            return;
        } else {
            document.getElementById('docs-save-button').disabled = false;
            hideSpinner();
        }

        
        // For each new file added, do the followng
        for (let i = 0; i < files.length; i++) {
            
            // Create the fileItem, which holds, the name, size, and remove-file-icon
            let fileItem = document.createElement('li');
            fileItem.setAttribute('class', 'file-item')
            fileItem.setAttribute('fileItem', i);
            fileList.appendChild(fileItem);
            
            // Add the file name to the fileItem
            let fileName = document.createElement('span');
            fileName.setAttribute('class', 'file-name');
            fileName.textContent = files[i].name;
            fileItem.appendChild(fileName);

            // Add the file size to the fileItem
            let fileSize = document.createElement('span');
            fileSize.textContent = (files[i].size / (1024 * 1024)).toFixed(1) + ' MB';
            fileSize.setAttribute('class', 'file-size ml-auto');
            fileItem.appendChild(fileSize);

            // Add the remove icon to the fileItem
            let removeIcon = document.createElement('i');
            removeIcon.setAttribute('class', 'bi bi-x-circle-fill remove-icon');
            removeIcon.setAttribute('name', 'remove-file-icon');
            fileItem.appendChild(removeIcon);

            // Call the function to set the event listeners for all remove icons
            setRemoveFileIconListeners();

            // Update the dataTransfer array
            updateDataTransfer(files);
        }
    }



    //----------------------------------------------------------------------------



    // Detects a click on a remove file icon and if clicked, delete that file
    function setRemoveFileIconListeners() {
        const removeFileIcons = document.getElementsByName('remove-file-icon');
        
        removeFileIcons.forEach(function(element) {

            // Remove the existing listener that sits on this element, looks for a click, and runs handleRemoveFileClick in response to a click 
            element.removeEventListener('click', handleRemoveFileClick);

            // Add new event listener that does the same
            element.addEventListener('click', handleRemoveFileClick); 
        });
    }

    

    //----------------------------------------------------------------------------


    
    // Defines what to do when a remove-file-icon event listener is tripped (works with setRemoveFileIconListeners)
    function handleRemoveFileClick(e) {
        console.log(`running ragDocMgmt.js ... remove icon clicked for element: ${ e.target }`);
        e.stopPropagation();  // Prevent the click event from bubbling up
    
        // Find the closest parent file-item and remove it
        const fileItem = e.target.closest('.file-item');
        if (fileItem) {
            fileItem.remove(); // Remove the file item from the DOM
        }

    }
    


    //----------------------------------------------------------------------------



    // Updates the dataTransfer array for new files added or removed 
    function updateDataTransfer(files) {
        let dataTransfer = new DataTransfer();
        for (let j = 0; j < files.length; j++) {
            //if (j !== i) {
                dataTransfer.items.add(files[j]);
                console.log(`running ragDocMgmt.js ... adding file: ${files[j].name}`);
            //}
        }
        document.getElementById('fileElem').files = dataTransfer.files;
        console.log(`running ragDocMgmt.js ... dataTransfer.files.length is: ${ dataTransfer.files.length }`);
    }
    


    //----------------------------------------------------------------------------



    // Resets the RagDocForm
    function jsResetForm() {
        console.log(`running ragDocMgmt.js, running jsResetForm() ... function started`)

        let form = document.getElementById('RagDocForm');
        form.reset();  // Reset the form to its initial state

        // Reset the drop area content
        let fileList = document.getElementById('file-list');
        fileList.innerHTML = '';
        document.getElementById('docs-save-button').disabled = true;
        console.log(`running ragDocMgmt.js, running jsResetForm() ... form reset`)
    }
    

});