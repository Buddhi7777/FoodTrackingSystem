document.addEventListener('DOMContentLoaded', function() {
    // Toggle meal options based on attendance status
    const statusComing = document.getElementById('status_coming');
    const statusNotComing = document.getElementById('status_not_coming');
    const mealOptions = document.getElementById('meal_options');
    
    if (statusComing && statusNotComing && mealOptions) {
        // Initial state setup
        mealOptions.style.display = 'none';
        
        // Event listeners for attendance status change
        statusComing.addEventListener('change', function() {
            if (this.checked) {
                mealOptions.style.display = 'block';
            }
        });
        
        statusNotComing.addEventListener('change', function() {
            if (this.checked) {
                mealOptions.style.display = 'none';
                // Uncheck all meal checkboxes
                document.querySelectorAll('#meal_options input[type="checkbox"]').forEach(function(checkbox) {
                    checkbox.checked = false;
                });
            }
        });
    }
    
    // Admin reset confirmation functions
    window.confirmAllReset = function() {
        if (confirm('Are you sure you want to reset ALL attendance data across ALL dates? This action cannot be undone.')) {
            document.getElementById('resetAllForm').submit();
        }
    };
    
    window.confirmDateReset = function(date) {
        if (confirm(`Are you sure you want to reset attendance data for ${date} only? This action cannot be undone.`)) {
            document.getElementById('resetCurrentForm').submit();
        }
    };
    
    // Auto-dismiss flash messages after 5 seconds
    const flashMessages = document.querySelectorAll('.alert');
    flashMessages.forEach(function(alert) {
        setTimeout(function() {
            const bootstrapAlert = new bootstrap.Alert(alert);
            bootstrapAlert.close();
        }, 5000);
    });
});
