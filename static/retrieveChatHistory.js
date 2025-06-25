import { csrfToken, extractLangChainContent, formatTimestamp, jsScrollDown, loadChatHistorySidebar, updateProfileForm } from './utils.js';



// The JS below retrieves the logged-in user's message history to display in the sidebar
document.addEventListener('DOMContentLoaded', function() {
    console.log(`running retrieveChatHistory.js ... DOM content loaded`);
    
    // Call the function when the page loads
    loadChatHistorySidebar(); 
    
});