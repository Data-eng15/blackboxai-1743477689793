// Modal Functionality
function toggleModal() {
    const modal = document.querySelector('.modal-overlay');
    if (modal.style.display === 'flex') {
        modal.style.display = 'none';
        document.body.style.overflow = 'auto';
    } else {
        modal.style.display = 'flex';
        document.body.style.overflow = 'hidden';
    }
}

// Handle all CTA buttons for login redirection
document.querySelectorAll('.hero-cta, .nav-cta, .btn-primary').forEach(button => {
    button.addEventListener('click', (e) => {
        e.preventDefault();
        const href = button.getAttribute('href');
        if (href && href !== '#' && !href.includes('loan-application.html')) {
            window.location.href = href;
        } else {
            toggleModal(); // Show login modal
        }
    });
});

// Close modal when clicking outside or on close button
document.addEventListener('DOMContentLoaded', () => {
    const modal = document.querySelector('.modal-overlay');
    const closeBtn = document.querySelector('.modal-close');

    if (modal) {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                toggleModal();
            }
        });
    }

    if (closeBtn) {
        closeBtn.addEventListener('click', toggleModal);
    }
});

// Form Validation
function validateForm(formElement) {
    const inputs = formElement.querySelectorAll('input[required]');
    let isValid = true;

    inputs.forEach(input => {
        if (!input.value.trim()) {
            isValid = false;
            showError(input, 'This field is required');
        } else {
            clearError(input);
        }

        // Email validation
        if (input.type === 'email' && input.value.trim()) {
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(input.value.trim())) {
                isValid = false;
                showError(input, 'Please enter a valid email address');
            }
        }

        // Password validation
        if (input.type === 'password' && input.value.trim()) {
            if (input.value.length < 8) {
                isValid = false;
                showError(input, 'Password must be at least 8 characters long');
            }
        }
    });

    return isValid;
}

function showError(input, message) {
    const formGroup = input.closest('.form-group');
    const errorElement = formGroup.querySelector('.error-message') || 
                        createErrorElement(formGroup);
    
    input.classList.add('error');
    errorElement.textContent = message;
    errorElement.style.opacity = '0';
    
    // Animate error message
    requestAnimationFrame(() => {
        errorElement.style.opacity = '1';
        errorElement.style.transform = 'translateY(0)';
    });
}

function clearError(input) {
    const formGroup = input.closest('.form-group');
    const errorElement = formGroup.querySelector('.error-message');
    input.classList.remove('error');
    
    if (errorElement) {
        errorElement.style.opacity = '0';
        errorElement.style.transform = 'translateY(-10px)';
        setTimeout(() => errorElement.remove(), 300);
    }
}

function createErrorElement(formGroup) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.style.color = 'red';
    errorDiv.style.fontSize = '0.875rem';
    errorDiv.style.marginTop = '0.25rem';
    errorDiv.style.transition = 'all 0.3s ease';
    errorDiv.style.transform = 'translateY(-10px)';
    errorDiv.style.opacity = '0';
    formGroup.appendChild(errorDiv);
    return errorDiv;
}

// Login Form Submit Handler
const loginForm = document.querySelector('#loginForm');
if (loginForm) {
    loginForm.addEventListener('submit', (e) => {
        e.preventDefault();
        if (validateForm(loginForm)) {
            // Show loading state
            const submitBtn = loginForm.querySelector('button[type="submit"]');
            const originalText = submitBtn.innerHTML;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Logging in...';
            submitBtn.disabled = true;
            
            // Simulate API call and redirect
            setTimeout(() => {
                window.location.href = 'loan-application.html';
            }, 1500);
        }
    });
}

// Password Toggle
const passwordToggles = document.querySelectorAll('.password-toggle');
passwordToggles.forEach(toggle => {
    toggle.addEventListener('click', () => {
        const input = toggle.previousElementSibling;
        const type = input.getAttribute('type') === 'password' ? 'text' : 'password';
        input.setAttribute('type', type);
        toggle.classList.toggle('show-password');
    });
});

// Smooth Scroll for Navigation Links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const href = this.getAttribute('href');
        if (href !== '#') {
            const element = document.querySelector(href);
            if (element) {
                const headerOffset = 80;
                const elementPosition = element.getBoundingClientRect().top;
                const offsetPosition = elementPosition + window.pageYOffset - headerOffset;

                window.scrollTo({
                    top: offsetPosition,
                    behavior: 'smooth'
                });
            }
        }
    });
});

// Initialize number counters for statistics
function animateValue(element, start, end, duration) {
    let startTimestamp = null;
    const step = (timestamp) => {
        if (!startTimestamp) startTimestamp = timestamp;
        const progress = Math.min((timestamp - startTimestamp) / duration, 1);
        const value = Math.floor(progress * (end - start) + start);
        element.innerHTML = value.toLocaleString();
        if (progress < 1) {
            window.requestAnimationFrame(step);
        }
    };
    window.requestAnimationFrame(step);
}

// Initialize counters when they come into view
const counterElements = document.querySelectorAll('.stat-card .text-4xl');
const counterObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            const target = parseInt(entry.target.innerHTML.replace(/[^0-9]/g, ''));
            animateValue(entry.target, 0, target, 2000);
            counterObserver.unobserve(entry.target);
        }
    });
}, {
    root: null,
    rootMargin: '0px',
    threshold: 0.1
});

counterElements.forEach(element => {
    counterObserver.observe(element);
});