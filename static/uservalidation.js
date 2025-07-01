import { csrfToken, debounce } from './utils.js'

document.addEventListener('DOMContentLoaded', function() {
    console.log(`running uservalidation.js ... DOM content loaded`);
    console.log(`running uservalidation.js ... current origin is: ${ window.location.origin }`);



    // Determine the base path dynamically
    const basePath = window.location.pathname.includes('/rag/') ? '/rag' : '';
    console.log(`running uservalidation.js ... basePath is: ${basePath}`);
    
    
    /*
    // Debouncing settings -------------------------------------------------
    let debounce_timeout = 200;
    let isButtonClicked = false;
    
    // Set debounce function globally
    function debounce(func, timeout = debounce_timeout){
        let timer;
        return (...args) => {
            clearTimeout(timer);
            timer = setTimeout(() => { func.apply(this, args); }, timeout);
        };
    }
    // Debouncing settings -------------------------------------------------
    */

    let submit_enabled = true;
    
    // Register settings --------------------------------------------------    
    const RegisterForm = document.getElementById('RegisterForm');
    const PasswordChangeForm = document.getElementById('PasswordChangeForm');
    const PasswordResetForm = document.getElementById('PasswordResetForm');
    const PasswordResetConfirmationForm = document.getElementById('PasswordResetConfirmationForm');
    
    if (RegisterForm || PasswordChangeForm || PasswordResetForm || PasswordResetConfirmationForm) {
        console.log("running uservalidation.js ... RegisterForm, PasswordChangeForm, or PasswordResetForm detected ");
        
        const first_name = document.getElementById('last_name');
        const last_name = document.getElementById('last_name');
        const email = document.getElementById('email');
        const password_old = document.getElementById('password_old');
        const password = document.getElementById('password');
        const passwordConfirmation = document.getElementById('password_confirmation');
        const submitButton = document.getElementById('submit-button');        
        
        const debouncedjsEnableRegisterSubmitButton = debounce(jsEnableRegisterSubmitButton, 400);

        if (first_name) {
            first_name.addEventListener('input', function() {
                debouncedjsEnableRegisterSubmitButton();
            });
        }

        if (last_name) {
            last_name.addEventListener('input', function() {
                debouncedjsEnableRegisterSubmitButton();
            });
        }
        
        
        if (email) {
            email.addEventListener('input', function() {
                debouncedjsEnableRegisterSubmitButton();
            });
        }
             
      
        const debouncedPasswordValidation = debounce(() => {
            jsPasswordValidation().then(() => { 
                jsEnableRegisterSubmitButton();
            });
        }, 200);

        if (password_old) {
            password_old.addEventListener('input', function() {
                debouncedjsEnableRegisterSubmitButton();                
            });
        }


        if (password) {
            password.addEventListener('input', function() {
                submitButton.disabled = true; // Disable immediately
                debouncedPasswordValidation();
            });
        }
        
        
        
        // Debounced password confirmation validation
        const debouncedPasswordConfirmationValidation = debounce(() => {
            jsPasswordConfirmationValidation().then(() => { 
                jsEnableRegisterSubmitButton();
            });
        }, 300);

        
        if (passwordConfirmation) {
            passwordConfirmation.addEventListener('input', function() {
                submitButton.disabled = true; // Disable immediately
                debouncedPasswordConfirmationValidation();
            });
        }
        
    
    }
    // Register settings --------------------------------------------------



    
    
    
    
    // Formatting elements red or green -------------------------------------------
    // Helper function: resets color of element to black
    function resetColor(elements) {
        if (!Array.isArray(elements)) {
            elements = [elements]; // Wrap the single element in an array
        }
        elements.forEach(element => {
            element.classList.remove('text-available');
            element.classList.add('text-taken');
        });
    }

    // Helper function: set color of element to #22bd39 (success green)
    function setGreen(elements) {
        if (!Array.isArray(elements)) {
            elements = [elements]; // Wrap the single element in an array
        }
        elements.forEach(element => {
            element.classList.remove('text-taken');
            element.classList.add('text-available');
        });
    }
    // Formatting elements red or green -------------------------------------------


    // Provides feedback to user whether user-inputted PW meets PW requirements.
    function jsPasswordValidation() {
        return new Promise((resolve, reject) => {
            const password_element = document.getElementById('password') 
            var password = password_element.value.trim();
            var passwordConfirmation = document.getElementById('password_confirmation').value.trim();
            var regLiMinTotChars = document.getElementById('pw-min-tot-chars-li');
            var regLiMinLetters = document.getElementById('pw-min-letters-li');
            var regLiMinNum = document.getElementById('pw-min-num-li');
            var regLiMinSym = document.getElementById('pw-min-sym-li');
            console.log(`running uservalidation.js ... Running jsPasswordValidation()`)
            
            if (password_element) {
                // If password is blank, reset the color of the elements below and return false.
                if (password === '') {
                    resetColor([regLiMinTotChars, regLiMinLetters, regLiMinNum, regLiMinSym]);
                    return resolve(false);
                }
                // If password is not blank, then toss the value over to the /check_password_strength in app.py
                const currentApp = window.location.pathname.includes('/avatar/') ? 'avatar' : 'aichat';

                fetch(`${basePath}/${currentApp}/check_password_valid/`, {
                    method: 'POST',
                    body: new URLSearchParams({ 
                        'password': password,
                        'password_confirmation': passwordConfirmation
                    }),
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                        'X-CSRFToken': csrfToken,
                    }
                })
                // Do the following with the result received back from app.py
                .then(response => response.json())
                .then(data => {
                    submit_enabled = true;
                    if (data.checks_passed.includes('pw-reg-length')) {
                        setGreen(regLiMinTotChars);
                    } else {
                        resetColor(regLiMinTotChars);
                        submit_enabled = false;
                    }
                    if (data.checks_passed.includes('pw-req-letter')) {
                        setGreen(regLiMinLetters);
                    } else {
                        resetColor(regLiMinLetters);
                        submit_enabled = false;
                    }
                    if (data.checks_passed.includes('pw-req-num')) {
                        setGreen(regLiMinNum);
                    } else {
                        resetColor(regLiMinNum);
                        submit_enabled = false;
                    }
                    if (data.checks_passed.includes('pw-req-symbol')) {
                        setGreen(regLiMinSym);
                    } else {
                        resetColor(regLiMinSym);
                        submit_enabled = false;
                    }
                    resolve(submit_enabled);
                })
                .catch(error => {
                    console.error('Error: password checking in registration has hit an error.', error);
                    reject(error);
                });
            }
        });
    }






    // Provides feedback to user regarding whether user-inputted password == user-inputted passwordConfirmation.
    function jsPasswordConfirmationValidation() {
        return new Promise((resolve, reject) => {
            const password_element = document.getElementById('password');
            var password = password_element.value.trim();
            var passwordConfirmation = document.getElementById('password_confirmation').value.trim();
            var passwordConfirmationValidationMatch = document.getElementById('password-confirmation-validation-match') 
            console.log(`running uservalidation.js ... Running jsPasswordConfirmationValidation()`)
            console.log(`running uservalidation.js ... running jsPasswordConfirmationValidation()... CSRF Token is: ${csrfToken}`);
            
            if (password_element) { 
                // If password is blank, reset the color of the elements below and return false.
                if (passwordConfirmation === '') {
                    resetColor([passwordConfirmationValidationMatch]);
                    submit_enabled = false;
                    console.log(`running uservalidation.js ... running jsPasswordConfirmationValidation()... submit_enabled is: ${ submit_enabled }`);
                    resolve(submit_enabled);
                }
                // If password is not blank, then toss the value over to the /check_password_strength
                const currentApp = window.location.pathname.includes('/avatar/') ? 'avatar' : 'aichat';

                fetch(`${basePath}/${currentApp}/check_password_valid/`, {
                    method: 'POST',
                    body: new URLSearchParams({ 
                        'password': password,
                        'password_confirmation': passwordConfirmation
                    }),
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                        'X-CSRFToken': csrfToken,
                    }
                })
                // Do the following with the result received back from app.py
                .then(response => response.json())
                .then(data => {
                    submit_enabled = true;
                    if (data.confirmation_match == true && data.checks_passed.length == 4) {
                        console.log(`running jsPasswordConfirmationValidation()... data.confirmation_match is: ${ data.confirmation_match }`);
                        console.log(`running jsPasswordConfirmationValidation()... setting color to green`);
                        setGreen(passwordConfirmationValidationMatch);
                    } else {
                        resetColor(passwordConfirmationValidationMatch);
                        submit_enabled = false;
                    }
                    resolve(submit_enabled);
                })
                .catch(error => {
                    console.error('Error: password checking in registration has hit an error.', error);
                    reject(error);
                });
            }
        });
    }


    
    async function jsEnableRegisterSubmitButton() {
        var submitButton = document.getElementById('submit-button');

        // Initially disable submit to ensure button is disabled while promises are in progress
        submitButton.disabled = true;

        // Check all present fields have values
        const fieldsToCheck = [
            { id: 'first_name'},
            { id: 'last_name'},
            { id: 'email'},
            { id: 'password_old'},
            { id: 'password'},
            { id: 'password_confirmation'}
        ];

        // Filter to only existing fields and check their values
        const existingFields = fieldsToCheck.filter(field => document.getElementById(field.id));
        const allFieldsHaveValues = existingFields.every(field => {
            const element = document.getElementById(field.id);
            return element && element.value.trim() !== '';
        });

        if (!allFieldsHaveValues) {
            submitButton.disabled = true;
            return;
        }

        // Create an array of promises with labels
        var labeledPromises = [];

        // Only add password validation if password field exists
        if (document.getElementById('password')) {
            labeledPromises.push({ label: 'Password Check', promise: jsPasswordValidation() });
        }

        // Only add password confirmation validation if confirmation field exists
        if (document.getElementById('password_confirmation')) {
            labeledPromises.push({ label: 'Password Confirmation Check', promise: jsPasswordConfirmationValidation() });
        }

        // If no password-related fields exist, enable the button based on other criteria
        if (labeledPromises.length === 0) {
            submitButton.disabled = false;
            return;
        }

        console.log(`Running jsEnableRegisterSubmitButton()`)

        Promise.all(labeledPromises.map(labeledPromise => {
            // Add a console.log statement before each promise
            console.log(`Running jsEnableRegisterSubmitButton()... Executing promise: ${labeledPromise.label}`);
    
            return labeledPromise.promise.then(result => {
                // Add a console.log statement after each promise resolves
                console.log(`Running jsEnableRegisterSubmitButton()... Promise (${labeledPromise.label}) resolved with result: ${result}`);
                return { label: labeledPromise.label, result: result };
            });
        }))
            .then((results) => {
                // Log each promise result
                results.forEach(res => {
                    console.log(`Result of ${res.label}: ${res.result}`);
                });
    
                // Check if any of the promises return false
                var allPromisesPassed = results.every(res => res.result === true);
                
                if (!allPromisesPassed ) {
                    submitButton.disabled = true;
                    console.log(`Running jsEnableRegisterSubmitButton()... Submit button disabled.`);
                } else {
                    // All validations passed
                    console.log(`Running jsEnableRegisterSubmitButton()... All validation checks passed, enabling submit button.`);
                    submitButton.disabled = false;
                }
            }).catch((error) => {
                // Handle errors if any of the Promises reject
                console.error(`Running jsEnableRegisterSubmitButton()... Error is: ${error}.`);
                submitButton.disabled = true;
            });
    }





});