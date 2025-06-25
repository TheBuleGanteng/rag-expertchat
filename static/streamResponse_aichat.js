import { hideSpinner } from './loadingspinner.js';
import { loadChatHistorySidebar, jsScrollDown } from './utils.js';
import { jsFavoriteIconMonitor } from './favorites.js'

document.addEventListener('DOMContentLoaded', function() {
    console.log(`running streamResponse_aichat.js ... DOM content loaded`);
    console.log(`running streamResponse_aichat.js ... current origin is: ${ window.location.origin }`);

    const InputForm = document.getElementById('InputForm');

    if (InputForm) {

        // Add an event listener to detect when the user clicks the submit button
        InputForm.addEventListener('submit', function (event) {
            event.preventDefault();
            jsStreamResponse(InputForm); // Pass the form element explicitly
        });

        // Add an event listener to detect when the user presses the Enter key
        InputForm.addEventListener('keypress', function (event) {
            if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault(); // Prevent the default behavior of adding a new line
                jsStreamResponse(InputForm); // Pass the form element explicitly
            }
        });
    }



    // Streams response from AI
    function jsStreamResponse(form) {
        console.log(`running streamResponse_aichat.js ... function started`);

        const formData = new FormData(form);

        // Extract the user_input value from formData
        const userInput = formData.get('user_input');
        const first_name = formData.get('first_name');
        const timestamp = formData.get('timestamp');
        
        // Logs
        console.log(`running streamResponse_aichat.js ... before appending to formData userInput is: ${userInput}`);
        console.log(`running streamResponse_aichat.js ... before appending to formData first_name is: ${first_name}`);
        console.log(`running streamResponse_aichat.js ... before appending to formData timestamp is: ${timestamp}`);
        
        // Log each key-value pair in the formData to ensure correctness
        for (var pair of formData.entries()) {
            console.log(`running streamResponse_aichat.js ... after appending to formData: ${ pair[0] + ': ' + pair[1] }`);
        }
        console.log(`running streamResponse_aichat.js ... all settings data appended to formData`);

        // Send the form data using fetch API
        fetch(form.getAttribute('action'), {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': formData.get('csrfmiddlewaretoken')
            },
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            // If the response is ok, then parse the JSON response
            return response.json();
        })
        .then(data => {
            hideSpinner(); // Hide the spinner before starting the streaming

            if (data.stream_id) {
                // Create a new EventSource to handle server-sent events (SSE) using the stream ID
                const eventSource = new EventSource(`/aichat/stream_response/?stream_id=${data.stream_id}`);
                console.log(`running streamResponse_aichat.js ... EventSource URL: /aichat/stream_response/?stream_id=${data.stream_id}`);
                
                let answerFeedItemInnerDiv; // Declare the inner div variable
                let sourcesMessage = ""; // Variable to hold sources message

                // Handle incoming streaming messages from the server
                eventSource.onmessage = function (event) {
                    //console.log(`running streamResponse_aichat.js ... received event with ID: ${event.lastEventId || 'no id'}, data: ${event.data}`);
                    
                    // Log all properties of the event object
                    //console.log(`running streamResponse_aichat.js ... event properties:', event);

                    // Event ID
                    //console.log(`running streamResponse_aichat.js ... event ID directly accessed: ${event.id}`);

                    // If we see a BEGIN marker, we know it's a new message and thus, we need to create a new div
                    if (event.data === "[BEGIN]") {
                        // Create the parent feed item for question
                        const questionFeedItemOuterDiv = document.createElement("div");
                        questionFeedItemOuterDiv.setAttribute('class', 'row w-100 justify-content-end d-flex flex-column align-items-end');
                        questionFeedItemOuterDiv.setAttribute('questionFeedItemOuterDiv', data.stream_id);
                        document.getElementById('feedDiv').appendChild(questionFeedItemOuterDiv);

                        // Create the child feed item for question timestamp
                        const questionFeedItemInnerDiv1 = document.createElement("div");
                        questionFeedItemInnerDiv1.setAttribute('class', 'fs-7 fw-lighter fst-italic d-inline-block w-auto');
                        questionFeedItemInnerDiv1.setAttribute('questionFeedItemInnerDiv1', data.stream_id);
                        questionFeedItemInnerDiv1.innerHTML = first_name + ' asked at ' + timestamp;
                        questionFeedItemOuterDiv.appendChild(questionFeedItemInnerDiv1);

                        // Create the child feed item for the question
                        const questionFeedItemInnerDiv2 = document.createElement("div");
                        questionFeedItemInnerDiv2.setAttribute('class', 'border border-secondary border-1 rounded mt-1 mb-1 p-1 d-inline-block w-auto feed-message-human');
                        questionFeedItemInnerDiv2.setAttribute('questionFeedItemInnerDiv2', data.stream_id);
                        questionFeedItemInnerDiv2.innerHTML = userInput;
                        questionFeedItemOuterDiv.appendChild(questionFeedItemInnerDiv2);
                        jsScrollDown();

                        // Create the parent feed item for the answer
                        const answerFeedItemOuterDiv = document.createElement("div");
                        answerFeedItemOuterDiv.setAttribute('class', 'col-lg-10');
                        answerFeedItemOuterDiv.setAttribute('answerFeedItemOuterDiv', data.stream_id);
                        document.getElementById('feedDiv').appendChild(answerFeedItemOuterDiv);

                        // Create the child feed item for the answer
                        answerFeedItemInnerDiv = document.createElement("div");
                        answerFeedItemInnerDiv.setAttribute('class', 'border border-dark border-2 rounded mt-5 mb-3 p-1 d-inline-block w-auto');
                        answerFeedItemInnerDiv.setAttribute('answerFeedItemInnerDiv', data.stream_id);
                        answerFeedItemOuterDiv.appendChild(answerFeedItemInnerDiv);
                    
                    } else if (event.data.startsWith('Expert:')) {
                        // Extract the expert data
                        let expertDataString = event.data.substring('Expert: '.length);
                        let expertData = JSON.parse(expertDataString);
                    
                        // Log the expert data for debugging
                        console.log(`running streamResponse_aichat.js ... expert data is ${ expertData }`);

                        // Create a row div if it doesn't already exist
                        let expertRowDiv = document.getElementById(`expertRowDiv-${data.stream_id}`);
                        if (!expertRowDiv) {
                            expertRowDiv = document.createElement("div");
                            expertRowDiv.setAttribute('class', 'row m-0 w-100');
                            expertRowDiv.setAttribute('id', `expertRowDiv-${data.stream_id}`);
                            

                            // Create the toggle button
                            const toggleButton = document.createElement("button");
                            toggleButton.setAttribute('class', 'btn btn-secondary btn-xsm mt-2');
                            toggleButton.innerHTML = 'Hide expert recommendations';
                            toggleButton.addEventListener('click', function () {
                                if (expertRowDiv.style.display === 'none') {
                                    expertRowDiv.style.display = 'flex';
                                    toggleButton.innerHTML = 'Hide expert recommendations';
                                    toggleButton.setAttribute('class', 'btn btn-secondary btn-xsm mt-2');
                                } else {
                                    expertRowDiv.style.display = 'none';
                                    toggleButton.innerHTML = 'Show expert recommendations';
                                    toggleButton.setAttribute('class', 'btn btn-primary btn-xsm mt-2');
                                }
                            });

                            // Append the toggle button to the answer feed item inner div
                            answerFeedItemInnerDiv.appendChild(toggleButton);

                            // Append the expert row div to the answer feed item inner div
                            answerFeedItemInnerDiv.appendChild(expertRowDiv);
                        }
                    
                        // Create a new parent div for the expert profile card
                        let expertCardParentDiv = document.createElement("div");
                        expertCardParentDiv.setAttribute('class', 'border border-gray-300 bg-gray-100 rounded-lg col-12 col-lg-6 col-xl-4 mt-2 mb-2 p-3');
                        expertCardParentDiv.setAttribute('id', `expertCardParentDiv-${expertData.id}`);
                        expertRowDiv.appendChild(expertCardParentDiv);
                    
                        // Create row for card star, title, and book call button
                        let expertCardTitleRow = document.createElement("div");
                        expertCardTitleRow.setAttribute('class', 'row m-0 w-100 align-items-center');
                        expertCardTitleRow.setAttribute('id', `expertCardTitleRow-${expertData.id}`);
                        expertCardParentDiv.appendChild(expertCardTitleRow);
                                                
                        // Create div to ensure card star and title are left-aligned, while book call btn remains right-aligned within card
                        let expertCardStarTitleDiv = document.createElement("div");
                        expertCardStarTitleDiv.setAttribute('class', 'd-flex align-items-center col-8 p-0 m-0');
                        expertCardStarTitleDiv.setAttribute('id', `expertCardStarTitleDiv-${expertData.id}`);
                        expertCardTitleRow.appendChild(expertCardStarTitleDiv);
                        
                        // Create star icon for expert card
                        let expertCardStar = document.createElement("h5");
                        expertCardStar.setAttribute('id', `expertCardStar-${expertData.id}`);
                        expertCardStar.setAttribute('name', 'favorite-icon');
                        if (expertData.is_favorite) {
                            expertCardStar.setAttribute('class', 'bi bi-star-fill yellow-star me-1');
                        } else {
                            expertCardStar.setAttribute('class', 'bi bi-star me-1');                            
                        };                        
                        expertCardStar.setAttribute('data-expert-id', expertData.id);
                        expertCardStarTitleDiv.appendChild(expertCardStar);

                        // Create card title for expert card
                        let expertCardTitle = document.createElement("h5");
                        expertCardTitle.setAttribute('class', 'title');
                        expertCardTitle.setAttribute('id', `expertCardTitle-${expertData.id}`);
                        expertCardTitle.innerHTML = expertData.name_first + ' ' + expertData.name_last;
                        expertCardStarTitleDiv.appendChild(expertCardTitle);
                        
                        // Create book call btn for expert profile card
                        let expertCardBookCallBtn = document.createElement("button");
                        expertCardBookCallBtn.setAttribute('class', 'btn btn-primary btn-sm col-3 ms-auto');
                        expertCardBookCallBtn.setAttribute('id', `expertCardBookCallBtn-${expertData.id}`);
                        expertCardBookCallBtn.innerHTML = 'Book call';
                        expertCardTitleRow.appendChild(expertCardBookCallBtn);

                        // Create photo and info div for expert profile card
                        let expertCardPhotoInfoDiv = document.createElement("div");
                        expertCardPhotoInfoDiv.setAttribute('class', 'row w-100');
                        expertCardPhotoInfoDiv.setAttribute('id', `expertCardPhotoInfoDiv-${expertData.id}`);
                        expertCardParentDiv.appendChild(expertCardPhotoInfoDiv);

                        // Create photo div for expert profile card
                        let expertCardPhotoDiv = document.createElement("div");
                        expertCardPhotoDiv.setAttribute('class', 'col-5'); // 5/12 of the width
                        expertCardPhotoDiv.setAttribute('id', `expertCardPhotoDiv-${expertData.id}`);
                        expertCardPhotoInfoDiv.appendChild(expertCardPhotoDiv);

                        // Create photo for expert profile card
                        let expertCardPhoto = document.createElement("img");
                        expertCardPhoto.src = expertData.photo;
                        expertCardPhoto.setAttribute('class', 'card-img-top');
                        expertCardPhoto.setAttribute('id', `expertCardPhoto-${expertData.id}`);
                        expertCardPhoto.setAttribute('alt', `photo of ${expertData.name_first} ${expertData.name_last}`);
                        expertCardPhotoDiv.appendChild(expertCardPhoto);
                        console.log(`running streamResponse_aichat.js ... Appended expert photo`);

                        // Create info div for expert profile card
                        let expertCardInfoDiv = document.createElement("div");
                        expertCardInfoDiv.setAttribute('class', 'col-7'); // 7/12 of the width
                        expertCardInfoDiv.setAttribute('id', `expertCardInfoDiv-${expertData.id}`);
                        expertCardPhotoInfoDiv.appendChild(expertCardInfoDiv);

                        let expertCardInfoDivContent1 = document.createElement("small");
                        expertCardInfoDivContent1.innerHTML = `<strong>Total experience: ${ expertData.total_years } years</strong><br>`;
                        expertCardInfoDiv.appendChild(expertCardInfoDivContent1);
                
                        let expertCardInfoDivContent2 = document.createElement("div");
                        expertCardInfoDivContent2.setAttribute('class', 'd-flex align-items-start small fst-italic');
                        expertCardInfoDivContent2.setAttribute('id', `expertCardInfoDivContent2-${expertData.id}`);
                        expertCardInfoDiv.appendChild(expertCardInfoDivContent2);

                        let expertCardInfoDivContent2Sub1 = document.createElement("div");
                        expertCardInfoDivContent2Sub1.setAttribute('class', 'me-1 small');
                        expertCardInfoDivContent2Sub1.setAttribute('id', `expertCardInfoDivContent2Sub1-${expertData.id}`);
                        expertCardInfoDivContent2Sub1.innerHTML = `Speaks:`;
                        expertCardInfoDivContent2.appendChild(expertCardInfoDivContent2Sub1);

                        let expertCardInfoDivContent2Sub2 = document.createElement("div");
                        expertCardInfoDivContent2Sub2.setAttribute('class', 'small');
                        expertCardInfoDivContent2Sub2.setAttribute('id', `expertCardInfoDivContent2Sub2-${expertData.id}`);
                        expertCardInfoDivContent2Sub2.innerHTML = expertData.languages_spoken;
                        expertCardInfoDivContent2.appendChild(expertCardInfoDivContent2Sub2);



                        // Create a list for bullet items
                        let ul = document.createElement("ul");
               
                        let expertCardInfoDivContent3 = document.createElement("small");
                        expertCardInfoDivContent3.innerHTML = `<li>${ expertData.role1 }, ${ expertData.employer1 }, (${expertData.regionCode1 })</li>`
                        ul.appendChild(expertCardInfoDivContent3);

                        let expertCardInfoDivContent4 = document.createElement("small");
                        expertCardInfoDivContent4.innerHTML = `<li>${ expertData.role2 }, ${ expertData.employer2 }, (${expertData.regionCode2 })</li>`
                        ul.appendChild(expertCardInfoDivContent4);

                        // Append the list to the info div
                        expertCardInfoDiv.appendChild(ul);

                    } else if (event.data === "[END]") {

                        // Handle end of stream
                        console.log(`running streamResponse_aichat.js ... streaming completed`);
                            jsScrollDown();
                            jsFavoriteIconMonitor();
                            
                            // Close the EventSource
                            eventSource.close();
                            console.log(`running streamResponse_aichat.js ... EventSource closed successfully after receiving [END] message.`);

                            // Refresh the chat history sidebar
                            console.log(`running streamresponse_aichat.js ... refreshed chat history sidebar`)
                            loadChatHistorySidebar();

                        //
                    } else {
                        if (answerFeedItemInnerDiv) {
                            answerFeedItemInnerDiv.innerHTML += event.data;
                        }
                    }
                    jsScrollDown();
                };
                form.reset();

                // Handle errors from the stream
                eventSource.onerror = function (err) {
                    console.error("EventSource failed:", err);
                    console.error(`Ready state: ${eventSource.readyState}`);
                    console.error(`URL: ${eventSource.url}`);
                    console.error(`Last event ID: ${eventSource.lastEventId || 'undefined'}`);
                    console.error('Event properties:', err);
                    eventSource.close();
                };
            } else {
                throw new Error('Stream ID not returned in response');
            }
        })
        // If there is no data key in the JSON, throw an error
        .catch(error => {
            console.error('Fetch error:', error);
            hideSpinner(); // Hide the spinner if there is a fetch error
        });
    }

});