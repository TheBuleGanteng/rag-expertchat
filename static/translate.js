// The JS below watches the language selector in the DOM and updates the language based on the user's manipulation of that language selector.

import { csrfToken } from './utils.js';

document.addEventListener('DOMContentLoaded', function() {
    console.log(`running translate.js ... DOM content loaded`);
    console.log(`running translate.js ... current origin is: ${window.location.origin}`);
    console.log(`running translate.js ... csrfToken is: ${csrfToken}`);

    // Access the language select element
    const languageSelector = document.getElementById('language-selector');

    // Add an event listener for change events
    if (languageSelector) {
        languageSelector.addEventListener('change', function(event) {
            const selectedLanguage = event.target.value;
            console.log(`running translate.js ... selected language is: ${selectedLanguage}`);

            // Make a POST request to set the session language
            fetch('/translate/set-session-language/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': csrfToken
                },
                body: `lang=${selectedLanguage}`
            })
            .then(response => {
                if (response.ok) {
                    console.log(`running translate.js ... session language set to: ${selectedLanguage}`);
                    // Reload the page to apply the new language setting
                    //window.location.reload();

                    // Get the current URL
                    let currentUrl = new URL(window.location.href);

                    // Remove the existing 'lang' parameter
                    currentUrl.searchParams.delete('lang');

                    // Add the new 'lang' parameter
                    currentUrl.searchParams.set('lang', selectedLanguage);

                    // Reload the page with the updated URL
                    window.location.href = currentUrl.toString();

                } else {
                    console.error(`running translate.js ... failed to set session language`);
                    // Optionally, handle errors (e.g., show a notification)
                }
            })
            .catch(error => {
                console.error(`running translate.js ... error setting session language: ${error}`);
                // Optionally, handle errors (e.g., show a notification)
            });
        });
    }
});
