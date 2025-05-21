// Task Filter Animation
document.addEventListener('DOMContentLoaded', function() {
    // Animate cards when page loads
    const cards = document.querySelectorAll('.card');
    cards.forEach((card, index) => {
        setTimeout(() => {
            card.classList.add('fade-in');
        }, 100 * index);
    });
    
    // Filter animation
    const filterButtons = document.querySelectorAll('.dropdown-item');
    filterButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Add loading state
            const tasksContainer = document.querySelector('.list-group');
            if (tasksContainer) {
                tasksContainer.style.opacity = '0.6';
                
                // Reset opacity after server response (simulated here)
                setTimeout(() => {
                    tasksContainer.style.opacity = '1';
                }, 500);
            }
        });
    });
    
    // Task status toggle (for demo purposes)
    const taskCards = document.querySelectorAll('.list-group-item');
    taskCards.forEach(card => {
        card.addEventListener('click', function(e) {
            // Only toggle if not clicking a button
            if (!e.target.closest('button') && !e.target.closest('a')) {
                card.classList.toggle('selected-task');
            }
        });
    });
    
    // Form validation enhancement
    enhanceFormValidation();
});

// Enhanced Form Validation
function enhanceFormValidation() {
    const forms = document.querySelectorAll('.needs-validation');
    
    forms.forEach(form => {
        // Real-time validation
        const inputs = form.querySelectorAll('input, textarea, select');
        
        inputs.forEach(input => {
            input.addEventListener('blur', function() {
                if (!this.checkValidity()) {
                    this.classList.add('is-invalid');
                } else {
                    this.classList.remove('is-invalid');
                    this.classList.add('is-valid');
                }
            });
            
            input.addEventListener('input', function() {
                if (this.checkValidity()) {
                    this.classList.remove('is-invalid');
                }
            });
        });
        
        // The existing form validation code...
    });
}

// Due Date Highlighting
function highlightDueDates() {
    const dueDates = document.querySelectorAll('.due-date');
    
    dueDates.forEach(dateElement => {
        const dueDate = new Date(dateElement.getAttribute('data-date'));
        const today = new Date();
        
        // Clear time component for date comparison
        today.setHours(0, 0, 0, 0);
        
        if (dueDate < today) {
            // Overdue
            dateElement.classList.add('text-danger', 'fw-bold');
        } else if (
            dueDate.getDate() === today.getDate() &&
            dueDate.getMonth() === today.getMonth() &&
            dueDate.getFullYear() === today.getFullYear()
        ) {
            // Due today
            dateElement.classList.add('text-warning', 'fw-bold');
        }
    });
}

// Call the function when DOM is loaded
document.addEventListener('DOMContentLoaded', highlightDueDates);