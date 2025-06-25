// Define the functions outside the event listener
// Function to show the spinner
export function showSpinner() {
    var spinner = document.getElementById('loadingSpinner');
    var overlay = document.getElementById('overlay');
    if (spinner && overlay) {
        spinner.classList.remove('d-none'); // Remove Bootstrap's 'd-none' class to show the spinner
        spinner.classList.add('d-flex');    // Add the flex display class if it's set
        overlay.classList.remove('d-none'); // Remove Bootstrap's 'd-none' class to show the overlay
        overlay.classList.add('d-flex');    // Add the flex display class if it's set
    } else {
        console.log(`running loadingspinner.js ... Spinner or overlay element not found.`);
    }
}

// Function to hide the spinner
export function hideSpinner() {
    var spinner = document.getElementById('loadingSpinner');
    var overlay = document.getElementById('overlay');
    if (spinner && overlay) {
        spinner.classList.remove('d-flex'); // Remove the flex display class if it's set
        spinner.classList.add('d-none');    // Add Bootstrap's 'd-none' class to hide the spinner
        overlay.classList.remove('d-flex'); // Remove the flex display class if it's set
        overlay.classList.add('d-none');    // Add Bootstrap's 'd-none' class to hide the overlay
    } else {
        console.log(`running loadingspinner.js ... Spinner or overlay element not found.`);
    }
}

// Attach event listeners inside the DOMContentLoaded event listener
document.addEventListener('DOMContentLoaded', function() {
    console.log(`running loadingspinner.js ... DOM content loaded`);
    console.log(`running loadingspinner.js ... current origin is: ${ window.location.origin }`);    

    // Hide spinner on initial page load
    window.addEventListener('load', hideSpinner);

    // Hide spinner on page show (including bfcache restore)
    window.addEventListener('pageshow', function(event) {
        console.log(`running loadingspinner.js ... showing spinner due to pageshow`);
        hideSpinner();
    });

    // Show spinner on form submit
    document.addEventListener('submit', function(event) {
        if (event.target.tagName.toLowerCase() === 'form') {
            console.log(`running loadingspinner.js ... showing spinner due to submit`);
            showSpinner();
        }
    });

    // Show spinner on window beforeunload
    window.addEventListener('beforeunload', function(event) {
        console.log(`running loadingspinner.js ... showing spinner due to beforeunload`);
        showSpinner();
    });

    // Show spinner on AJAX start and hide on AJAX complete
    (function() {
        var open = XMLHttpRequest.prototype.open;
        var send = XMLHttpRequest.prototype.send;

        XMLHttpRequest.prototype.open = function() {
            this.addEventListener('loadstart', function() {
                console.log(`running loadingspinner.js ... showing spinner due to AJAX loadstart`);
                showSpinner();
            });
            this.addEventListener('loadend', function() {
                console.log(`running loadingspinner.js ... hiding spinner due to AJAX loadend`);
                hideSpinner();
            });
            open.apply(this, arguments); // Call the original open method
        };

        XMLHttpRequest.prototype.send = function() {
            send.apply(this, arguments); // Call the original send method
        };
    })();
});
