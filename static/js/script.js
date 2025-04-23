// Main JavaScript file for the Modern Form App

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips if they exist
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    if (tooltipTriggerList.length > 0) {
        tooltipTriggerList.map(function(tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }

    // Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });

    // Add input masks for phone fields if they exist
    const phoneInputs = document.querySelectorAll('input[type="tel"]');
    if (phoneInputs.length > 0) {
        phoneInputs.forEach(input => {
            input.addEventListener('input', function(e) {
                // Allow only numbers, +, (), -, and spaces
                const value = e.target.value.replace(/[^\d+() -]/g, '');
                e.target.value = value;
            });
        });
    }

    // Enhance form validation feedback
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        const formInputs = form.querySelectorAll('input, textarea');
        
        formInputs.forEach(input => {
            // Clear invalid state when user starts typing again
            input.addEventListener('input', function() {
                if (input.classList.contains('is-invalid')) {
                    input.classList.remove('is-invalid');
                }
            });
            
            // Add focused class for custom styling
            input.addEventListener('focus', function() {
                input.parentElement.classList.add('focused');
            });
            
            input.addEventListener('blur', function() {
                input.parentElement.classList.remove('focused');
            });
        });
    });

    // Add smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                window.scrollTo({
                    top: target.offsetTop - 100,
                    behavior: 'smooth'
                });
            }
        });
    });
});
