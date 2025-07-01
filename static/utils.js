// This is a collection of JS utility functions used in other JS files



// Pulls the CSRF token and exports it, making it available for other JS files to pull
let csrfToken = '';
let csrfMeta = document.querySelector('meta[name="csrf-token"]');
if (csrfMeta) {
    csrfToken = csrfMeta.content;
    console.log(`running aichat.js ... CSRF Token set: ${ csrfToken }`);
} else {
    console.log(`running aichat.js ... CSRF meta tag not found.`);
}
export { csrfToken };


//------------------------------------------------------------------------------



// Determine the base path dynamically
const basePath = window.location.pathname.includes('/rag/') ? '/rag' : '';
const currentApp = window.location.pathname.includes('/avatar/') ? 'avatar' : 'aichat';



//------------------------------------------------------------------------------



// Debounce function takes two arguments: function to be debounced and time (with default in ms)
export function debounce(func, timeout) { // Default timeout set to 300ms
    let timer;
    return function(...args) {
        const context = this; // Capture the current context
        clearTimeout(timer);
        timer = setTimeout(() => func.apply(context, args), timeout);
    };
}


// ----------------------------------------------------------------------


// The function below takes LangChain's default message history and formats it to display in the user's feed
export function extractLangChainContent(messageString) {
    try {
        if (messageString.startsWith('[')) {
            const messages = messageString.slice(1, -1).split('), ');
            const extractedMessages = [];
            
            for (let msg of messages) {
                if (msg.includes('HumanMessage')) {
                    const match = msg.match(/content='([^']*)'/) ||
                                msg.match(/content="([^"]*)"/) ||
                                msg.match(/content=([^,}]*)/);
                    if (match) {
                        extractedMessages.push({ type: 'user', content: match[1] });
                    }
                } else if (msg.includes('AIMessageChunk')) {
                    const match = msg.match(/content='([^']*)'/) ||
                                msg.match(/content="([^"]*)"/) ||
                                msg.match(/content=([^,}]*)/);
                    if (match) {
                        extractedMessages.push({ type: 'ai', content: match[1] });
                    }
                }
            }
            return extractedMessages;
        }
        return messageString;
    } catch (e) {
        console.error('Error parsing message:', e);
        return messageString;
    }
}



//------------------------------------------------------------------------------


// The function below reformats the default timestamp for chat history, so as to display a more human-readable timestamp in the UI
export function formatTimestamp(timestamp, timezone = 'Asia/Jakarta') {
    // Handle case where timestamp is already in the desired format
    if (typeof timestamp === 'string' && timestamp.includes(',')) {
        return timestamp.split(',')[1].trim(); // Return just the time portion
    }

    try {
        const date = new Date(timestamp);
        
        // Check if date is valid
        if (isNaN(date.getTime())) {
            throw new Error('Invalid date');
        }

        const options = {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            timeZone: timezone,
            hour12: false
        };

        const formattedDate = new Intl.DateTimeFormat('en-GB', options).formatToParts(date);
        const dateMap = {};
        formattedDate.forEach(({type, value}) => {
            dateMap[type] = value;
        });

        return `${dateMap.day}-${dateMap.month}-${dateMap.year}, ${dateMap.hour}:${dateMap.minute}`;
    } catch (e) {
        console.warn('Error formatting timestamp:', e);
        return timestamp; // Return original timestamp if formatting fails
    }
}

// -------------------------------------------------------------------------------


// Triggers aichat_chat generate_embeddings, which generates the embeddings and retriever
export function generateEmbeddings() {
    console.log(`running utils.js ... running generateEmbeddings()`);
     
    return fetch(`${basePath}/${currentApp}/generate_embeddings/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrfToken,
            'X-Requested-With': 'XMLHttpRequest'
        },
    })
    .then(response => {
        if (!response.ok) {
            return response.text().then(text => {
                console.error(`running utils.js ... Server responded with status: ${response.status}`);
                console.error(`running utils.js ... Response text: ${text}`);
                throw new Error(`HTTP error! status: ${response.status}`);
            });
        }
        return response.json();
    })
    .catch(error => {
        console.error(`running utils.js ... error during AJAX request: ${error}`);
        throw error;
    });
}



//------------------------------------------------------------------------------



// Submits various forms via Ajax, which allows for form submission without page reload
export function handleAjaxFormSubmission(url, formData) {
    
    return fetch(url, {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': csrfToken,
            'X-Requested-With': 'XMLHttpRequest'
        },
    })
    .then(response => {
        // Attempt to parse the response as JSON regardless of the status
        return response.json().then(data => {
            if (!response.ok) {
                console.error(`running utils.js ... Server responded with status: ${response.status}`);
                console.error(`running utils.js ... Response text: ${text}`);
                throw new Error(`HTTP error! status: ${response.status}`);
            };
            return data;
        });
    })
    .catch(error => {
        console.error(`running utils.js ... error during AJAX request: ${error}`);
        throw error;
    });
}



// --------------------------------------------------------------------


// The function below populates the chat history sidebar
export function loadChatHistorySidebar() {
    console.log(`running loadChatHistorySidebar ... function started`);

    const chatHistoryParentDiv = document.getElementById('chat-history-div')

    if (chatHistoryParentDiv) {    
        // Send the form data using fetch API
        fetch(`${basePath}/${currentApp}/retrieve-chat-history/`, {
            method: 'GET',
            headers: {
                'X-CSRFToken': csrfToken,
            },
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`running loadChatHistorySidebar() ... HTTP error! status: ${response.status}, error: ${ response.error }`);
            }
            return response.json();
        })
        .then(data => {
            if (data.status === 'success') {
                console.log(`running loadChatHistorySidebar() ... data is: ${ data }`);
                
                // First load the current conversation
                loadChatConversation(data, data.conversation_id);
                console.log(`running loadChatHistorySidebar() ... loaded current conversation`);

                // Group messages by session_id and find latest timestamp for each
                const conversationTimestamps = {};
                data.message_data.forEach(message => {
                    if (!conversationTimestamps[message.session_id] || 
                        new Date(message.timestamp) > new Date(conversationTimestamps[message.session_id].timestamp)) {
                        conversationTimestamps[message.session_id] = message;
                    }
                });

                // Convert to array and sort by timestamp descending
                const sortedConversations = Object.values(conversationTimestamps)
                    .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));

                // First, clear chatHistoryParentDiv of any existing content before overwriting it
                chatHistoryParentDiv.innerHTML = '';
                console.log(`running loadChatHistorySidebar() ... cleared chatHistoryDiv`);

                // Create buttons for each conversation
                sortedConversations.forEach(lastMessage => {
                    const chatHistoryConvo = document.createElement("button");
                    chatHistoryConvo.setAttribute('class', 'm-1 p-1 border border-secondary d-block w-100 small text-truncate');
                    if (lastMessage.session_id == data.conversation_id) {
                        chatHistoryConvo.classList.add('feed-message-human');
                    }
                    chatHistoryConvo.setAttribute('id', `chatHistoryConvo-${lastMessage.session_id}`);
                    chatHistoryConvo.setAttribute('name', `chatHistoryConvoItem`);
                    chatHistoryConvo.textContent = formatTimestamp(lastMessage.timestamp);
                    chatHistoryParentDiv.append(chatHistoryConvo);

                    const fieldName = 'conversation_id';
                    const fieldValue = lastMessage.session_id;

                    chatHistoryConvo.addEventListener('click', () => {
                        // Remove highlight from all items
                        document.getElementsByName('chatHistoryConvoItem').forEach(item => {
                            item.classList.remove('feed-message-human');
                        });
                        
                        // Add highlight to clicked item
                        chatHistoryConvo.classList.add('feed-message-human');
                        loadChatConversation(data, lastMessage.session_id);
                        updateProfileForm(fieldName, fieldValue);
                    });
                });
            } else {
                console.error('Response data does not contain message_data property');
            }
        })
    }
}



//------------------------------------------------------------------------------


// Works with loadChatHistorySidebar to load prior conversations into FeedDiv 
function loadChatConversation(data, session_id) {
    console.log(`running loadChatConversation ... function started`);

    const feedDiv = document.getElementById('feedDiv');

    if (feedDiv) {
        feedDiv.innerHTML = ''; // Clear existing content

        data.message_data
            .filter(message => message.session_id === session_id)
            .forEach(message => {
                const extractedMessages = extractLangChainContent(message.message);
                
                if (Array.isArray(extractedMessages)) {
                    extractedMessages.forEach(msg => {
                        if (msg.type === 'user') {
                            // Create user message container
                            const questionFeedItemOuterDiv = document.createElement("div");
                            questionFeedItemOuterDiv.setAttribute('class', 'row w-100 justify-content-end d-flex flex-column align-items-end');
                            questionFeedItemOuterDiv.setAttribute('id', `questionFeedItemOuterDiv-${message.session_id}`);
                            questionFeedItemOuterDiv.setAttribute('name', 'feedItem');
                            feedDiv.appendChild(questionFeedItemOuterDiv);

                            // Create timestamp div for user message
                            const questionFeedItemInnerDiv1 = document.createElement("div");
                            questionFeedItemInnerDiv1.setAttribute('class', 'fs-7 fw-lighter fst-italic d-inline-block w-auto');
                            questionFeedItemInnerDiv1.setAttribute('id', `questionFeedItemInnerDiv1-${message.session_id}`);
                            // Set timestamp from message data if available
                            questionFeedItemInnerDiv1.innerHTML = `Asked at ${formatTimestamp(message.timestamp) || 'unknown time'}`;
                            questionFeedItemOuterDiv.appendChild(questionFeedItemInnerDiv1);

                            // Create content div for user message
                            const questionFeedItemInnerDiv2 = document.createElement("div");
                            questionFeedItemInnerDiv2.setAttribute('class', 'border border-secondary border-1 rounded mt-1 mb-1 p-1 d-inline-block w-auto feed-message-human');
                            questionFeedItemInnerDiv2.setAttribute('id', `questionFeedItemInnerDiv2-${message.session_id}`);
                            questionFeedItemInnerDiv2.textContent = msg.content;
                            questionFeedItemOuterDiv.appendChild(questionFeedItemInnerDiv2);
                        } else if (msg.type === 'ai') {
                            // Create AI response container
                            const answerFeedItemOuterDiv = document.createElement("div");
                            answerFeedItemOuterDiv.setAttribute('class', 'col-lg-10');
                            answerFeedItemOuterDiv.setAttribute('id', `answerFeedItemOuterDiv-${message.session_id}`);
                            answerFeedItemOuterDiv.setAttribute('name', 'feedItem');
                            feedDiv.appendChild(answerFeedItemOuterDiv);

                            // Create content div for AI response
                            const answerFeedItemInnerDiv = document.createElement("div");
                            answerFeedItemInnerDiv.setAttribute('class', 'border border-dark border-2 rounded mt-5 mb-3 p-1 d-inline-block w-auto');
                            answerFeedItemInnerDiv.setAttribute('id', `answerFeedItemInnerDiv-${message.session_id}`);
                            answerFeedItemInnerDiv.textContent = msg.content;
                            answerFeedItemOuterDiv.appendChild(answerFeedItemInnerDiv);
                        }
                    });
                }
            });
            
        // Scroll to bottom after loading messages
        jsScrollDown();
    }
}


//------------------------------------------------------------------------------



// Adds an event listener to the button with id='reset_page_button'
export function setResetButtonEventListener() {
    const resetButton = document.getElementById('reset_page_button');
    if (resetButton) {
        resetButton.addEventListener('click', () => {
            window.location.reload();
        });
    }
}



//------------------------------------------------------------------------------



// Scroll to the bottom of feedDiv
export function jsScrollDown() {
    // Scroll to the bottom of the page
    window.scrollTo(0, document.body.scrollHeight);
}



//------------------------------------------------------------------------------

// Format number with commas
export function toDateGB(dateString) {
    return new Intl.DateTimeFormat('en-GB', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric'
    }).format(new Date(dateString));
}


//------------------------------------------------------------------------------


// Format number with commas
export function toNumberWithCommas(number) {
    return Number(number).toLocaleString();
}



//------------------------------------------------------------------------------



// Convert a decimal to a percentage
export function toPercentage(value) {
    return (value * 100).toFixed(0) + '%';
}



//------------------------------------------------------------------------------



// Collapse accordion 1, expand accordion 2
export function transitionAccordionOneToTwo() {
    const accordion1Element = document.getElementById('panelsStayOpen-collapseOne');
    const accordion2Element = document.getElementById('panelsStayOpen-collapseTwo');

    // Ensure that both elements exist in the DOM before proceeding
    if (accordion1Element && accordion2Element) {
        var accordion1 = new bootstrap.Collapse(accordion1Element, { toggle: false });
        var accordion2 = new bootstrap.Collapse(accordion2Element, { toggle: false });

        accordion1.hide(); // Collapse the first accordion
        accordion2.show(); // Show the second accordion
        console.log(`running transitionAccordionOneToTwo() ... collapsed accordion1 and expanded accordion2`);
    } else {
        console.log(`running transitionAccordionOneToTwo() ... accordion1 and/or accordion2 not present in the DOM. Unable to run transitionAccordionOneToTwo()`);
    }
}



//------------------------------------------------------------------------------



// Collapse accordion 2, expand accordion 1
export function transitionAccordionTwoToOne() {
    
    const accordion1Element = document.getElementById('panelsStayOpen-collapseOne');
    const accordion2Element = document.getElementById('panelsStayOpen-collapseTwo');

    // Ensure that both elements exist in the DOM before proceeding
    if (accordion1Element && accordion2Element) {

        var accordion1 = new bootstrap.Collapse(accordion1Element, { toggle: false });
        var accordion2 = new bootstrap.Collapse(accordion2Element, { toggle: false });

        accordion2.hide(); // Collapse the first accordion
        accordion1.show(); // Show the second accordion
    } else {
        console.log(`running transitionAccordionTwoTpOne() ... accordion1 and/or accordion2 not present in the DOM. Unable to run transitionAccordionTwoToOne()`)

    }

}



//------------------------------------------------------------------------------



// Collapse accordion 2, expand accordion 3
export function transitionAccordionTwoToThree() {
    
    // If DB updated successfully, hide accordion 1, expand accordion 2
    var accordion2Element = document.getElementById('panelsStayOpen-collapseTwo')
    var accordion3Element = document.getElementById('panelsStayOpen-collapseThree')

    if (accordion2Element && accordion3Element) {
        var accordion2 = new bootstrap.Collapse(accordion2Element, { toggle: false });
        var accordion3 = new bootstrap.Collapse(accordion3Element, { toggle: false });

        accordion2.hide(); // Collapse the first accordion
        accordion3.show(); // Show the second accordion
    } else {
        console.log(`running transitionAccordionTwoToThree() ... accordion2 and/or accordion3 not present in the DOM. Unable to run transitionAccordionTwoToThree()`)
    }

}



//------------------------------------------------------------------------------


// Update the profileForm for the field submitted
export function updateProfileForm(fieldName, fieldValue) {

    // Prepare data to send in the request
    const formData = new FormData();

    formData.append('field', fieldName);  // Use the field name from the input
    formData.append('value', fieldValue);  // Use the field value from the input

    // If password is not blank, then toss the value over to the /check_password_strength
    // Determine the base path dynamically
    const updateProfileUrl = `${basePath}/${currentApp}/update_profile/`;
    console.log(`running updateProfileForm() ... updateProfileUrl is: ${ updateProfileUrl }`);

    handleAjaxFormSubmission(updateProfileUrl, formData)
    .then(data => {
        if (data.status === 'success') {
            console.log('running updateProfileForm() ... profile updated successfully');

        } else {
            console.error(`running updateProfileForm() ... error submitting form: ${ data.errors}`);
            alert('Failed to update profile');
        }
    })
    .catch(error => {
        console.error(`running updateProfileForm() ... error during form submission: ${ error}`);
        alert('An unexpected error occurred.');
    });
};
