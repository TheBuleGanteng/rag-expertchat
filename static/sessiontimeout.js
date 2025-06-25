document.addEventListener('DOMContentLoaded', function() {
    console.log(`running sessiontimeout.js ... DOM content loaded`);
    console.log(`running sessiontimeout.js ... current origin is: ${ window.location.origin }`);



    // Session timeout ----------------------------------------------------
    // Shows popup warning before user is logged out due to inactivity
    var SESSION_COOKIE_AGE_SEC = 900;

    // Timer to track inactivity
    var inactivityTimer;

    // Function to show the timeout modal in layout.html
    function showModal() {
        $('#staticBackdrop').modal('show');
    }

    // Function to reset the inactivity timer
    function resetTimer() {
        clearTimeout(inactivityTimer);
        inactivityTimer = setTimeout(showModal, (SESSION_COOKIE_AGE_SEC - 1 * 60) * 1000); // Show modal 5 minutes before timeout
    }

    document.querySelectorAll('form').forEach(function(form) {
        form.addEventListener('submit', function() {
            resetTimer();
        });
    });

    // Extend session button in the modal
    var extendButton = document.querySelector('[name="timeout-extend-button"]');
    if (extendButton) { // Check if the extend session button exists before adding event listener
        extendButton.addEventListener('click', function() {
            var readinessCheckUrl = this.getAttribute('data-readiness-check-url'); // Get the URL from the data attribute

            // Implement AJAX request to the readiness_check view that resets the session timer
            $.get(readinessCheckUrl, function(data) {
                if (data.status === 'ready') {
                    resetTimer();
                    $('#staticBackdrop').modal('hide'); // Hide the modal
                }
            });
        });
    }

    // Log out button in the modal
    var logoutButton = document.querySelector('[name="timeout-logout-button"]');
    if (logoutButton) { // Check if the logout button exists before adding event listener
        logoutButton.addEventListener('click', function() {
            var logoutUrl = this.getAttribute('data-logout-url'); // Get the logout URL from the data attribute
            window.location.href = logoutUrl; // Redirect to the logout URL
        });
    }

    // Start the inactivity timer when the page loads, but only if the user is authenticated
    if (document.querySelector('[name="timeout-extend-button"]') || document.querySelector('[name="timeout-logout-button"]')) {
        window.onload = resetTimer;
    }
    // Session timeout ----------------------------------------------------

});