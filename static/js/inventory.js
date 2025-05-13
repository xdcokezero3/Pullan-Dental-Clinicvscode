document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const addItemBtn = document.getElementById('addItemBtn');
    const itemModal = document.getElementById('itemModal');
    const confirmationModal = document.getElementById('confirmationModal');
    const closeModalBtns = document.querySelectorAll('.close-modal');
    const cancelBtn = document.getElementById('cancelBtn');
    const inventoryForm = document.getElementById('inventoryForm');
    const inventoryTable = document.getElementById('inventoryTable');
    const modalTitle = document.getElementById('modalTitle');
    const searchInput = document.getElementById('inventorySearch');
    const filterBtns = document.querySelectorAll('.filter-btn');
    
    // Cancel delete elements
    const cancelDeleteBtn = document.getElementById('cancelDeleteBtn');
    const confirmDeleteBtn = document.getElementById('confirmDeleteBtn');
    
    let currentItemId = null; // Track the ID of the item being edited/deleted
    
    // Open modal when add item button is clicked
    addItemBtn.addEventListener('click', function() {
        // Reset form before showing
        inventoryForm.reset();
        document.getElementById('itemId').value = '';
        modalTitle.textContent = 'Add New Item';
        itemModal.style.display = 'block';
    });
    
    // Close any modal when close button is clicked
    closeModalBtns.forEach(function(btn) {
        btn.addEventListener('click', function() {
            itemModal.style.display = 'none';
            confirmationModal.style.display = 'none';
        });
    });
    
    // Close modal when cancel button is clicked
    cancelBtn.addEventListener('click', function() {
        itemModal.style.display = 'none';
    });
    
    // Close modal when clicking outside of it
    window.addEventListener('click', function(event) {
        if (event.target === itemModal) {
            itemModal.style.display = 'none';
        } else if (event.target === confirmationModal) {
            confirmationModal.style.display = 'none';
        }
    });
    
    // Handle form submission
    inventoryForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // Gather form data
        const formData = new FormData();
        formData.append('name', document.getElementById('itemName').value);
        formData.append('type', document.getElementById('itemType').value);
        formData.append('quantity', document.getElementById('itemQuantity').value);
        formData.append('remarks', document.getElementById('itemRemarks').value);
        
        const expiryDate = document.getElementById('itemExpiry').value;
        if (expiryDate) {
            formData.append('expiry_date', expiryDate);
        }
        
        const itemId = document.getElementById('itemId').value;
        
        // Determine if we're adding or updating
        let url = '/add_inventory';
        if (itemId) {
            url = `/update_inventory/${itemId}`;
        }
        
        // Send the request - use full path to ensure proper routing
        fetch(url, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Close the modal
                itemModal.style.display = 'none';
                
                // Update the UI
                if (itemId) {
                    // Update existing row
                    updateTableRow(data.item);
                } else {
                    // Add new row
                    addTableRow(data.item);
                }
                
                // Update stats
                updateInventoryStats(data.stats);
                
                // Show success message
                showNotification('Item saved successfully!', 'success');
            } else {
                showNotification('Error: ' + data.error, 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showNotification('An error occurred. Please try again.', 'error');
        });
    });
    
    // Handle edit button clicks
    document.addEventListener('click', function(e) {
        if (e.target.closest('.edit-btn')) {
            const button = e.target.closest('.edit-btn');
            const itemId = button.getAttribute('data-id');
            
            // Fetch item details
            fetch(`/inventory_item/${itemId}`, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // Populate the form
                        const item = data.item;
                        document.getElementById('itemId').value = item.raw_id;
                        document.getElementById('itemName').value = item.name;
                        document.getElementById('itemType').value = item.type;
                        document.getElementById('itemQuantity').value = item.quantity;
                        document.getElementById('itemRemarks').value = item.remarks;
                        
                        if (item.expiry_date) {
                            document.getElementById('itemExpiry').value = item.expiry_date;
                        } else {
                            document.getElementById('itemExpiry').value = '';
                        }
                        
                        // Update modal title and show
                        modalTitle.textContent = 'Edit Item';
                        itemModal.style.display = 'block';
                    } else {
                        showNotification('Error fetching item details', 'error');
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    showNotification('An error occurred. Please try again.', 'error');
                });
        }
    });
    
    // Handle delete button clicks
    document.addEventListener('click', function(e) {
        if (e.target.closest('.delete-btn')) {
            const button = e.target.closest('.delete-btn');
            currentItemId = button.getAttribute('data-id');
            
            // Show confirmation modal
            confirmationModal.style.display = 'block';
        }
    });
    
    // Cancel delete
    cancelDeleteBtn.addEventListener('click', function() {
        confirmationModal.style.display = 'none';
        currentItemId = null;
    });
    
    // Confirm delete
    confirmDeleteBtn.addEventListener('click', function() {
        if (currentItemId) {
            // Send delete request with full path
            fetch(`/delete_inventory/${currentItemId}`, {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Close the modal
                    confirmationModal.style.display = 'none';
                    
                    // Remove the row from the table
                    const row = document.querySelector(`tr[data-id="${currentItemId}"]`);
                    if (row) {
                        row.remove();
                    }
                    
                    // Update stats
                    updateInventoryStats(data.stats);
                    
                    // Show success message
                    showNotification('Item deleted successfully!', 'success');
                    
                    // Reset currentItemId
                    currentItemId = null;
                } else {
                    showNotification('Error: ' + data.error, 'error');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showNotification('An error occurred. Please try again.', 'error');
            });
        }
    });
    
    // Handle view button clicks
    document.addEventListener('click', function(e) {
        if (e.target.closest('.view-btn')) {
            const button = e.target.closest('.view-btn');
            const itemId = button.getAttribute('data-id');
            
            // Fetch item details for viewing
            fetch(`/inventory_item/${itemId}`, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // Show item details (could be a modal or other UI)
                        // For now, we'll just populate the form in read-only mode
                        const item = data.item;
                        document.getElementById('itemId').value = item.raw_id;
                        document.getElementById('itemName').value = item.name;
                        document.getElementById('itemType').value = item.type;
                        document.getElementById('itemQuantity').value = item.quantity;
                        document.getElementById('itemRemarks').value = item.remarks;
                        
                        if (item.expiry_date) {
                            document.getElementById('itemExpiry').value = item.expiry_date;
                        } else {
                            document.getElementById('itemExpiry').value = '';
                        }
                        
                        // Update modal title and show
                        modalTitle.textContent = 'View Item Details';
                        
                        // Make form read-only
                        const formElements = inventoryForm.elements;
                        for (let i = 0; i < formElements.length; i++) {
                            if (formElements[i].type !== 'button' && formElements[i].type !== 'submit') {
                                formElements[i].readOnly = true;
                            }
                        }
                        
                        // Show modal
                        itemModal.style.display = 'block';
                    } else {
                        showNotification('Error fetching item details', 'error');
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    showNotification('An error occurred. Please try again.', 'error');
                });
        }
    });
    
    // Handle filter buttons
    filterBtns.forEach(function(btn) {
        btn.addEventListener('click', function() {
            // Remove active class from all buttons
            filterBtns.forEach(b => b.classList.remove('active'));
            
            // Add active class to clicked button
            this.classList.add('active');
            
            const filterType = this.getAttribute('data-filter');
            
            // Send filter request
            fetch(`/filter_inventory/${filterType}`, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // Update table with filtered items
                        updateTableWithItems(data.items);
                    } else {
                        showNotification('Error filtering items', 'error');
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    showNotification('An error occurred. Please try again.', 'error');
                });
        });
    });
    
    // Search functionality
    searchInput.addEventListener('keyup', function() {
        const searchTerm = this.value.toLowerCase();
        const rows = inventoryTable.querySelectorAll('tbody tr');
        
        rows.forEach(function(row) {
            const itemName = row.querySelector('td:nth-child(2)').textContent.toLowerCase();
            const itemCategory = row.querySelector('td:nth-child(3)').textContent.toLowerCase();
            
            if (itemName.includes(searchTerm) || itemCategory.includes(searchTerm)) {
                row.style.display = '';
            } else {
                row.style.display = 'none';
            }
        });
    });
    
    // Helper function to update stats
    function updateInventoryStats(stats) {
        document.querySelector('.total-items .card-info h3').textContent = stats.total_items;
        document.querySelector('.low-stock .card-info h3').textContent = stats.low_stock;
        document.querySelector('.expired .card-info h3').textContent = stats.expired;
        document.querySelector('.value .card-info h3').textContent = '$' + stats.total_value;
    }
    
    // Helper function to add a new row to the table
    function addTableRow(item) {
        const tbody = inventoryTable.querySelector('tbody');
        const newRow = document.createElement('tr');
        newRow.setAttribute('data-id', item.raw_id);
        newRow.setAttribute('data-type', item.type.toLowerCase());
        
        if (item.status === 'Low') {
            newRow.classList.add('low-stock');
        }
        
        if (item.expiry && new Date(item.expiry) < new Date()) {
            newRow.classList.add('expired');
        }
        
        newRow.innerHTML = `
            <td>${item.id}</td>
            <td>${item.name}</td>
            <td>${item.type}</td>
            <td>${item.quantity}</td>
            <td>${item.expiry}</td>
            <td>
                <span class="status-badge ${item.status === 'Low' ? 'low-stock' : 'in-stock'}">${item.status}</span>
            </td>
            <td>
                <div class="actions">
                    <button class="view-btn" title="View Details" data-id="${item.raw_id}"><i class="fas fa-eye"></i></button>
                    <button class="edit-btn" title="Edit Item" data-id="${item.raw_id}"><i class="fas fa-edit"></i></button>
                    <button class="delete-btn" title="Delete Item" data-id="${item.raw_id}"><i class="fas fa-trash"></i></button>
                </div>
            </td>
        `;
        
        tbody.appendChild(newRow);
    }
    
    // Helper function to update an existing row
    function updateTableRow(item) {
        const row = document.querySelector(`tr[data-id="${item.raw_id}"]`);
        if (row) {
            row.setAttribute('data-type', item.type.toLowerCase());
            
            // Update class based on status
            row.classList.remove('low-stock', 'expired');
            if (item.status === 'Low') {
                row.classList.add('low-stock');
            }
            if (item.expiry && new Date(item.expiry) < new Date()) {
                row.classList.add('expired');
            }
            
            // Update row content
            row.cells[1].textContent = item.name;
            row.cells[2].textContent = item.type;
            row.cells[3].textContent = item.quantity;
            row.cells[4].textContent = item.expiry;
            
            // Update status badge
            const statusBadge = row.cells[5].querySelector('.status-badge');
            statusBadge.className = 'status-badge';
            statusBadge.classList.add(item.status === 'Low' ? 'low-stock' : 'in-stock');
            statusBadge.textContent = item.status;
        }
    }
    
    // Helper function to update the table with filtered items
    function updateTableWithItems(items) {
        const tbody = inventoryTable.querySelector('tbody');
        tbody.innerHTML = '';
        
        items.forEach(function(item) {
            const newRow = document.createElement('tr');
            newRow.setAttribute('data-id', item.raw_id);
            newRow.setAttribute('data-type', item.type.toLowerCase());
            
            if (item.status === 'Low') {
                newRow.classList.add('low-stock');
            }
            
            if (item.expiry && new Date(item.expiry) < new Date()) {
                newRow.classList.add('expired');
            }
            
            newRow.innerHTML = `
                <td>${item.id}</td>
                <td>${item.name}</td>
                <td>${item.type}</td>
                <td>${item.quantity}</td>
                <td>${item.expiry}</td>
                <td>
                    <span class="status-badge ${item.status === 'Low' ? 'low-stock' : 'in-stock'}">${item.status}</span>
                </td>
                <td>
                    <div class="actions">
                        <button class="view-btn" title="View Details" data-id="${item.raw_id}"><i class="fas fa-eye"></i></button>
                        <button class="edit-btn" title="Edit Item" data-id="${item.raw_id}"><i class="fas fa-edit"></i></button>
                        <button class="delete-btn" title="Delete Item" data-id="${item.raw_id}"><i class="fas fa-trash"></i></button>
                    </div>
                </td>
            `;
            
            tbody.appendChild(newRow);
        });
    }
    
    // Helper function to show notifications
    function showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        
        // Append to body
        document.body.appendChild(notification);
        
        // Show notification
        setTimeout(() => {
            notification.classList.add('show');
        }, 10);
        
        // Remove after 3 seconds
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => {
                document.body.removeChild(notification);
            }, 300);
        }, 3000);
    }
    
    // Add notification styles dynamically
    const notificationStyles = document.createElement('style');
    notificationStyles.textContent = `
        .notification {
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 15px 20px;
            border-radius: 5px;
            color: white;
            font-weight: 500;
            max-width: 300px;
            z-index: 1100;
            opacity: 0;
            transform: translateY(-20px);
            transition: opacity 0.3s, transform 0.3s;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        }
        
        .notification.show {
            opacity: 1;
            transform: translateY(0);
        }
        
        .notification.success {
            background-color: #48bb78;
        }
        
        .notification.error {
            background-color: #f56565;
        }
        
        .notification.info {
            background-color: #4299e1;
        }
    `;
    document.head.appendChild(notificationStyles);
});