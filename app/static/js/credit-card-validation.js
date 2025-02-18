// Credit card type patterns
const cardPatterns = {
    visa: /^4[0-9]{12}(?:[0-9]{3})?$/,
    mastercard: /^5[1-5][0-9]{14}$/,
    amex: /^3[47][0-9]{13}$/,
    discover: /^6(?:011|5[0-9]{2})[0-9]{12}$/
};

// Detect credit card type based on number
function detectCardType(number) {
    number = number.replace(/\D/g, '');
    
    for (let [card, pattern] of Object.entries(cardPatterns)) {
        if (pattern.test(number)) {
            return card;
        }
    }
    return 'unknown';
}

// Luhn algorithm for card number validation
function isValidLuhn(number) {
    let sum = 0;
    let isEven = false;
    
    // Loop through values starting from the rightmost one
    for (let i = number.length - 1; i >= 0; i--) {
        let digit = parseInt(number.charAt(i), 10);

        if (isEven) {
            digit *= 2;
            if (digit > 9) {
                digit -= 9;
            }
        }

        sum += digit;
        isEven = !isEven;
    }

    return (sum % 10) === 0;
}

// Validate credit card number
function isValidCardNumber(number) {
    number = number.replace(/\D/g, '');
    
    // Check if the number matches any card pattern
    let validPattern = false;
    for (let pattern of Object.values(cardPatterns)) {
        if (pattern.test(number)) {
            validPattern = true;
            break;
        }
    }
    
    // If number matches a pattern, verify with Luhn algorithm
    return validPattern && isValidLuhn(number);
}

// Format credit card number with spaces
function formatCardNumber(number) {
    return number.replace(/\D/g, '')
                .replace(/(.{4})/g, '$1 ')
                .trim();
}

// Validate expiration date
function isValidExpirationDate(month, year) {
    const currentDate = new Date();
    const expDate = new Date(year, month - 1); // Month is 0-based in Date constructor
    return expDate > currentDate;
}

// Validate CVV based on card type
function isValidCVV(cvv, cardType) {
    const isAmex = cardType === 'amex';
    const cvvPattern = isAmex ? /^[0-9]{4}$/ : /^[0-9]{3}$/;
    return cvvPattern.test(cvv);
}

// Validate credit card fields
function validateCreditCard() {
    const ccNumber = document.getElementById('cc_number');
    const ccName = document.getElementById('cc_name');
    const ccExpMonth = document.getElementById('cc_expiration_month');
    const ccExpYear = document.getElementById('cc_expiration_year');
    const ccCVV = document.getElementById('cc_cvv');
    const cardTypeIcon = document.getElementById('card-type-icon');
    
    let isValid = true;
    
    // Validate card number
    const cardNumber = ccNumber.value.replace(/\D/g, '');
    const cardType = detectCardType(cardNumber);
    
    // Update card type icon
    cardTypeIcon.className = 'fab fa-cc-' + cardType;
    cardTypeIcon.style.display = 'inline';
    
    if (!isValidCardNumber(cardNumber)) {
        ccNumber.classList.add('is-invalid');
        isValid = false;
    } else {
        ccNumber.classList.remove('is-invalid');
    }
    
    // Validate name
    if (ccName.value.trim().length < 3) {
        ccName.classList.add('is-invalid');
        isValid = false;
    } else {
        ccName.classList.remove('is-invalid');
    }
    
    // Validate expiration date
    if (!isValidExpirationDate(ccExpMonth.value, ccExpYear.value)) {
        ccExpMonth.classList.add('is-invalid');
        ccExpYear.classList.add('is-invalid');
        isValid = false;
    } else {
        ccExpMonth.classList.remove('is-invalid');
        ccExpYear.classList.remove('is-invalid');
    }
    
    // Validate CVV
    if (!isValidCVV(ccCVV.value, cardType)) {
        ccCVV.classList.add('is-invalid');
        isValid = false;
    } else {
        ccCVV.classList.remove('is-invalid');
    }
    
    return isValid;
}

// Format credit card number with spaces
function formatCreditCard(e) {
    let input = e.target;
    let value = input.value.replace(/\D/g, '');
    
    // Add spaces every 4 digits
    value = formatCardNumber(value);
    input.value = value;
    
    // Update card type icon
    const cardType = detectCardType(value.replace(/\s/g, ''));
    const cardTypeIcon = document.getElementById('card-type-icon');
    cardTypeIcon.className = 'fab fa-cc-' + cardType;
    cardTypeIcon.style.display = 'inline';
}

// Initialize credit card validation
document.addEventListener('DOMContentLoaded', function() {
    const ccNumber = document.getElementById('cc_number');
    const checkoutForm = document.getElementById('checkout-form');
    
    if (ccNumber) {
        ccNumber.addEventListener('input', formatCreditCard);
    }
    
    if (checkoutForm) {
        checkoutForm.addEventListener('submit', function(e) {
            if (!validateCreditCard()) {
                e.preventDefault();
            }
        });
    }
});

// Export functions for use in other scripts
window.detectCardType = detectCardType;
window.isValidCardNumber = isValidCardNumber;
window.formatCardNumber = formatCardNumber;
window.isValidExpirationDate = isValidExpirationDate;
window.isValidCVV = isValidCVV;
