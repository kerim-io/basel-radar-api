// Admin dashboard JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Auto-hide alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            alert.style.opacity = '0';
            alert.style.transition = 'opacity 0.5s';
            setTimeout(function() {
                alert.remove();
            }, 500);
        }, 5000);
    });

    // Confirm dialogs for delete actions
    const deleteButtons = document.querySelectorAll('[data-confirm]');
    deleteButtons.forEach(function(button) {
        button.addEventListener('click', function(e) {
            const message = this.getAttribute('data-confirm') || 'Are you sure?';
            if (!confirm(message)) {
                e.preventDefault();
            }
        });
    });

    // Form validation feedback
    const forms = document.querySelectorAll('form');
    forms.forEach(function(form) {
        form.addEventListener('submit', function(e) {
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn && !form.querySelector('.btn-danger')) {
                submitBtn.disabled = true;
                submitBtn.textContent = 'Saving...';
            }
        });
    });

    // Highlight current nav link
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav-links a');
    navLinks.forEach(function(link) {
        const href = link.getAttribute('href');
        if (currentPath === href || (href !== '/admin/' && currentPath.startsWith(href))) {
            link.style.color = 'white';
            link.style.borderBottomColor = '#6366f1';
        }
    });

    // Table row click to navigate (for rows with a view link)
    const tableRows = document.querySelectorAll('.data-table tbody tr');
    tableRows.forEach(function(row) {
        const viewLink = row.querySelector('a[href*="/admin/"]');
        if (viewLink) {
            row.style.cursor = 'pointer';
            row.addEventListener('click', function(e) {
                // Don't navigate if clicking on a button or link
                if (e.target.tagName === 'A' || e.target.tagName === 'BUTTON' ||
                    e.target.closest('form')) {
                    return;
                }
                window.location.href = viewLink.href;
            });
        }
    });
});
