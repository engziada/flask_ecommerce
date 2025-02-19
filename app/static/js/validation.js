// Password validation functions
function validatePassword(password) {
    const specialChars = '!@#$%^&*()_+-=[]{};:,./<>?`~';
    const requirements = {
        length: password.length >= 8,
        uppercase: /[A-Z]/.test(password),
        lowercase: /[a-z]/.test(password),
        number: /\d/.test(password),
        special: [...password].some(char => specialChars.includes(char))
    };

    return {
        isValid: Object.values(requirements).every(req => req),
        requirements
    };
}

// Form validation
function initializeFormValidation(formId) {
    const form = document.getElementById(formId);
    if (!form) {
        console.error('Form not found:', formId);
        return;
    }

    const inputs = {
        password: form.querySelector('#password'),
        confirmPassword: form.querySelector('#confirm_password'),
        terms: form.querySelector('#terms'),
        email: form.querySelector('#email'),
        firstName: form.querySelector('#first_name'),
        lastName: form.querySelector('#last_name')
    };

    const elements = {
        registerButton: form.querySelector('#registerButton'),
        requirements: {
            length: document.querySelector('#length-check'),
            uppercase: document.querySelector('#uppercase-check'),
            lowercase: document.querySelector('#lowercase-check'),
            number: document.querySelector('#number-check'),
            special: document.querySelector('#special-check')
        }
    };

    // Validate that we have all required elements
    if (!inputs.password || !elements.registerButton) {
        console.error('Required form elements not found');
        return;
    }

    function updateRequirementUI(element, isValid) {
        if (element) {
            const symbol = isValid ? '✓' : '✗';
            const text = element.textContent.replace(/^[✓✗]\s/, '');
            element.textContent = `${symbol} ${text}`;
            element.classList.toggle('valid', isValid);
            element.classList.toggle('invalid', !isValid);
        }
    }

    function validateForm() {
        const { isValid, requirements } = validatePassword(inputs.password.value);
        
        // Update requirement checks
        Object.entries(requirements).forEach(([key, value]) => {
            updateRequirementUI(elements.requirements[key], value);
        });

        // Validate other fields
        const isPasswordMatch = inputs.confirmPassword ? 
            inputs.password.value === inputs.confirmPassword.value : true;
        const isEmailValid = inputs.email ? 
            /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(inputs.email.value) : true;
        const isFirstNameValid = inputs.firstName ? 
            inputs.firstName.value.trim() !== '' : true;
        const isLastNameValid = inputs.lastName ? 
            inputs.lastName.value.trim() !== '' : true;
        const isTermsAccepted = inputs.terms ? 
            inputs.terms.checked : true;

        // Show/hide password match error
        if (inputs.confirmPassword?.value) {
            inputs.confirmPassword.classList.toggle('is-invalid', !isPasswordMatch);
        }

        // Enable/disable register button
        const allValid = isValid && isPasswordMatch && isEmailValid && 
                        isFirstNameValid && isLastNameValid && isTermsAccepted;
        elements.registerButton.disabled = !allValid;

        return allValid;
    }

    // Add event listeners
    Object.values(inputs).forEach(input => {
        if (input) {
            if (input.type === 'checkbox') {
                input.addEventListener('change', validateForm);
            } else {
                input.addEventListener('input', validateForm);
                input.addEventListener('blur', validateForm);
            }
        }
    });

    // Handle form submission
    form.addEventListener('submit', function(e) {
        if (!validateForm()) {
            e.preventDefault();
            e.stopPropagation();
        }
        form.classList.add('was-validated');
    });

    // Initial validation
    validateForm();
}
