// Auto-refresh service status on dashboard
document.addEventListener('DOMContentLoaded', function() {
    // Add loading state to check buttons
    document.querySelectorAll('.check-btn').forEach(function(btn) {
        btn.addEventListener('click', function() {
            btn.disabled = true;
            btn.textContent = 'Checking...';
            setTimeout(function() {
                btn.disabled = false;
                btn.textContent = 'Check Now';
            }, 2000);
        });
    });
});