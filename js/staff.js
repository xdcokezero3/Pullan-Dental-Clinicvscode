document.addEventListener('DOMContentLoaded', function() {
    // Tab switching functionality
    const tabs = document.querySelectorAll('.tab');
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            tabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            
            document.querySelectorAll('.tab-content').forEach(content => {
                content.classList.remove('active');
            });
            
            const tabId = tab.getAttribute('data-tab');
            document.getElementById(tabId).classList.add('active');
        });
    });

    // Search functionality
    const searchInput = document.getElementById('staffSearch');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase();
            const staffCards = document.querySelectorAll('.staff-card');
            const staffRows = document.querySelectorAll('tbody tr');
            
            staffCards.forEach(card => {
                const name = card.querySelector('.staff-details h3').textContent.toLowerCase();
                const role = card.querySelector('.staff-details p').textContent.toLowerCase();
                const email = card.querySelector('.staff-info p:nth-child(1)').textContent.toLowerCase();
                
                if (name.includes(searchTerm) || role.includes(searchTerm) || email.includes(searchTerm)) {
                    card.style.display = 'block';
                } else {
                    card.style.display = 'none';
                }
            });
            
            staffRows.forEach(row => {
                const name = row.cells[1].textContent.toLowerCase();
                const role = row.cells[2].textContent.toLowerCase();
                const email = row.cells[3].textContent.toLowerCase();
                
                if (name.includes(searchTerm) || role.includes(searchTerm) || email.includes(searchTerm)) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
        });
    }

    // Filter functionality
    const roleFilter = document.getElementById('roleFilter');
    const accessFilter = document.getElementById('accessFilter');
    
    if (roleFilter && accessFilter) {
        roleFilter.addEventListener('change', filterStaff);
        accessFilter.addEventListener('change', filterStaff);
    }

    function filterStaff() {
        const roleFilterValue = roleFilter.value;
        const accessFilterValue = accessFilter.value;
        
        const staffCards = document.querySelectorAll('.staff-card');
        const staffRows = document.querySelectorAll('tbody tr');
        
        staffCards.forEach(card => {
            const roleMatch = roleFilterValue === 'all' || card.getAttribute('data-role') === roleFilterValue;
            const accessMatch = accessFilterValue === 'all' || card.getAttribute('data-access') === accessFilterValue;
            
            if (roleMatch && accessMatch) {
                card.style.display = 'block';
            } else {
                card.style.display = 'none';
            }
        });
        
        staffRows.forEach(row => {
            const roleMatch = roleFilterValue === 'all' || row.getAttribute('data-role') === roleFilterValue;
            const accessMatch = accessFilterValue === 'all' || row.getAttribute('data-access') === accessFilterValue;
            
            if (roleMatch && accessMatch) {
                row.style.display = '';
            } else {
                row.style.display = 'none';
            }
        });
    }

    // Modal functionality
    const modal = document.getElementById('addStaffModal');
    const addBtn = document.getElementById('addStaffBtn');
    const closeBtn = document.querySelector('.close');
    const cancelBtn = document.getElementById('cancelAddStaff');

    if (addBtn) {
        addBtn.addEventListener('click', () => {
            modal.style.display = 'block';
        });
    }

    if (closeBtn) {
        closeBtn.addEventListener('click', () => {
            modal.style.display = 'none';
        });
    }

    if (cancelBtn) {
        cancelBtn.addEventListener('click', () => {
            modal.style.display = 'none';
        });
    }

    window.addEventListener('click', (event) => {
        if (event.target === modal) {
            modal.style.display = 'none';
        }
    });

    // Delete staff confirmation
    document.querySelectorAll('.delete-staff').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const staffId = this.getAttribute('data-id');
            if (confirm('Are you sure you want to delete this staff member?')) {
                window.location.href = `/delete_staff/${staffId}`;
            }
        });
    });

    // Edit staff redirect
    document.querySelectorAll('.edit-staff').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const staffId = this.getAttribute('data-id');
            window.location.href = `/edit_staff/${staffId}`;
        });
    });

    // View staff redirect
    document.querySelectorAll('.view-staff').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const staffId = this.getAttribute('data-id');
            window.location.href = `/staff_details/${staffId}`;
        });
    });
});