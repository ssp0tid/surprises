document.addEventListener('DOMContentLoaded', function() {
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            alert.style.transition = 'opacity 0.3s';
            alert.style.opacity = '0';
            setTimeout(function() {
                alert.remove();
            }, 300);
        }, 5000);
    });

    const deleteButtons = document.querySelectorAll('[data-action="delete"]');
    deleteButtons.forEach(function(button) {
        button.addEventListener('click', function(e) {
            if (!confirm('Are you sure you want to delete this item?')) {
                e.preventDefault();
            }
        });
    });

    const toggleButtons = document.querySelectorAll('[data-action="toggle"]');
    toggleButtons.forEach(function(button) {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const url = button.getAttribute('href');
            fetch(url, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCSRFToken()
                }
            })
            .then(function(response) {
                return response.json();
            })
            .then(function(data) {
                if (data.success) {
                    const badge = button.closest('.component-item').querySelector('.status-badge');
                    if (badge) {
                        badge.textContent = data.is_enabled ? 'enabled' : 'disabled';
                        badge.className = 'status-badge ' + (data.is_enabled ? 'status-operational' : 'status-unknown');
                    }
                }
            })
            .catch(function(error) {
                console.error('Error:', error);
            });
        });
    });

    function getCSRFToken() {
        const meta = document.querySelector('meta[name="csrf-token"]');
        return meta ? meta.getAttribute('content') : '';
    }
});