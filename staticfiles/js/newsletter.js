document.addEventListener('DOMContentLoaded', function() {
    const newsletterForm = document.getElementById('newsletter-form');
    
    if (newsletterForm) {
        const MESSAGE_DURATION = 3000;
        const DEBOUNCE_DELAY = 3000;  // Increased duration for better readability
        const emailInput = document.getElementById('newsletter-email');
        const submitButton = document.getElementById('newsletter-submit');
        const messageDiv = document.getElementById('newsletter-message');
        let currentMessageTimeout = null;
        let lastSubmissionTime = 0;

        function validateEmail(email) {
            return email.match(/^[^\s@]+@[^\s@]+\.[^\s@]+$/);
        }

        function getCsrfToken() {
            const name = 'csrftoken';
            let cookieValue = null;
            
            if (document.cookie && document.cookie !== '') {
                const cookies = document.cookie.split(';');
                for (let cookie of cookies) {
                    cookie = cookie.trim();
                    if (cookie.substring(0, name.length + 1) === (name + '=')) {
                        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                        break;
                    }
                }
            }
            return cookieValue;
        }

        function showMessage(message, type) {
            if (currentMessageTimeout) {
                clearTimeout(currentMessageTimeout);
                currentMessageTimeout = null;
            }

            messageDiv.textContent = message;
            messageDiv.className = `newsletter-message ${type}`;
            messageDiv.style.opacity = '1';
            
            if (type === 'success') {
                submitButton.classList.add('btn-success');
                submitButton.classList.remove('btn-info');
            }
            
            currentMessageTimeout = setTimeout(() => {
                messageDiv.style.opacity = '0';
                messageDiv.style.transition = 'opacity 0.3s ease';
                
                setTimeout(() => {
                    messageDiv.textContent = '';
                    messageDiv.className = 'newsletter-message';
                    messageDiv.style.opacity = '1';
                    if (type === 'success') {
                        submitButton.classList.remove('btn-info');
                        submitButton.classList.add('btn-success');
                    }
                    currentMessageTimeout = null;
                }, 300);
            }, MESSAGE_DURATION);
        }

        newsletterForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const now = Date.now();
            const timeElapsed = now - lastSubmissionTime;
            
            if (timeElapsed < DEBOUNCE_DELAY) {
                showMessage(`Please wait ${Math.ceil((DEBOUNCE_DELAY - timeElapsed) / 1000)} seconds before trying again`, 'error');
                return;
            }


            if (!validateEmail(emailInput.value)) {
                showMessage('Please enter a valid email address', 'error');
                return;
            }


            // Update last submission time
            lastSubmissionTime = now;
            
            emailInput.disabled = true;
            submitButton.disabled = true;
            
            try {
                const response = await fetch('/subscribe/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCsrfToken(),
                    },
                    body: JSON.stringify({
                        email: emailInput.value.trim()
                    }),
                    credentials: 'same-origin'
                });
                
                const data = await response.json();
                
                if (!response.ok) {
                    throw new Error(data.message || 'An error occurred');
                }
                
                showMessage(data.message, data.status);
                
                if (data.status === 'success') {
                    emailInput.value = '';
                }
            } catch (error) {
                showMessage(error.message || 'An error occurred. Please try again.', 'error');
            } finally {
                emailInput.disabled = false;
                submitButton.disabled = false;
            }
        });
    }
});