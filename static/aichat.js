
// Load DOM before doing all JS below -------------------------------------------------
document.addEventListener('DOMContentLoaded', function() {
    console.log(`running aichat.js ... DOM content loaded`);
    console.log(`running aichat.js ... current origin is: ${ window.location.origin }`);
    
    
    // The JS below manages the width of the sidebar, making it wider for the login page ------
    const currentPath = window.location.pathname; 

    // Select the sidebar element
    const sidebarDiv = document.getElementById('sidebar-div');

    
    // Check if the route is 'login'
    if (currentPath.includes('/login') || currentPath.includes('/logout')) {
      // Set the sidebar to col-5
      sidebarDiv.classList.add('col-8', 'col-sm-6', 'col-md-4');
      sidebarDiv.classList.remove('col-3');
    } else {
      // Set the sidebar to col-3
      sidebarDiv.classList.add('col-3');
      sidebarDiv.classList.remove('col-8', 'col-sm-6', 'col-md-4');
    } 
    
    



    
    
    // The JS below manages the 'Show Settings' button used for small screens ---------------

    // If the show/hide settings button is present, select it
    const btnShowSettings = document.getElementById('btn-show-settings');
    const sidebarCollapsableDiv = document.getElementById('sidebar-collapsable-div');
    const settingsDropDown = document.getElementById('settings-collapse');
    const nonSidebarDiv = document.getElementById('non-sidebar-div');

    if (btnShowSettings) {
        btnShowSettings.addEventListener('click', function () {
            console.log(`running aichat.js ... sidebar settings button click detected`)

            const smScreenSideBarContracted = sidebarCollapsableDiv.classList.contains('d-none');
            
            if (smScreenSideBarContracted) {
                console.log(`running aichat.js ... showing sidebar`)
                // Expand the side bar
                sidebarDiv.classList.remove('col-3', 'col-lg-2');
                sidebarDiv.classList.add('w-100');
                // Show the settings and history drop-downs inside the sidebar
                sidebarCollapsableDiv.classList.remove('d-none');
                settingsDropDown.classList.remove('collapse');
                // Update the button's color and innerHTML
                btnShowSettings.innerHTML = 'Hide settings';
                btnShowSettings.classList.remove('btn-primary');
                btnShowSettings.classList.add('btn-secondary');
                // Hide the chat/file upload section of the page 
                nonSidebarDiv.classList.add('d-none');
                //fileUploadInstructions.classList.add('d-none');
                //tempFileUploadInstructions.classList.remove('d-none')
            } else {
                console.log(`running aichat.js ... hiding sidebar`)
                // Shrink the sidebar
                sidebarDiv.classList.remove('w-100');
                sidebarDiv.classList.add('col-3', 'col-lg-2');
                // Hide the settings and history drop-downs inside the sidebar
                sidebarCollapsableDiv.classList.add('d-none');
                settingsDropDown.classList.add('collapse');
                // Update the button's color and innerHTML
                btnShowSettings.innerHTML = 'Show settings';
                btnShowSettings.classList.remove('btn-secondary');
                btnShowSettings.classList.add('btn-primary');
                // Show the chat/file upload section of the page
                nonSidebarDiv.classList.remove('d-none'); 
                //fileUploadInstructions.classList.remove('d-none');
                //tempFileUploadInstructions.classList.add('d-none')
            }
        });
    }

    // Tooltips, sliders, and popovers ------------------------------------
    // Allow for tooltip text to appear on any page where it is located. 
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Enable Bootstrap5 popovers wherever they appear
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'))
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
    return new bootstrap.Popover(popoverTriggerEl)
    })
    // Tooltips, sliders, and popovers ------------------------------------


        
});
