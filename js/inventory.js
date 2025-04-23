// inventory.js - Client-side logic for inventory management

document.addEventListener('DOMContentLoaded', function() {
    // Elements
    const addItemBtn = document.getElementById('addItemBtn');
    const itemModal = document.getElementById('itemModal');
    const confirmationModal = document.getElementById('confirmationModal');
    const modalTitle = document.getElementById('modalTitle');
    const inventoryForm = document.getElementById('inventoryForm');
    const cancelBtn = document.getElementById('cancelBtn');
    const closeModalButtons = document.querySelectorAll('.close-modal');
    const inventoryTable = document.getElementById('inventoryTable');
    const inventorySearch = document.getElementById('inventorySearch');
    const filterButtons = document.querySelectorAll('.filter-btn');
    
    // Item being deleted (for confirmation)
    let itemToDelete = null;
    
    // Event listeners
    addItemBtn.addEventListener('click', openAddModal);
    cancelBtn.addEventListener('click', closeModals);
    closeModalButtons.forEach(btn => btn.addEventListener('click', closeModals));
    inventoryForm.addEventListener('submit', handleFormSubmit);
    
    // Filter buttons
    filterButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            // Remove active class from all buttons
            filterButtons.forEach(b => b.classList.remove('active'));
            
            // Add active class to clicked button
            this.classList.add('active');
            
            // Apply filter
            const filter = this.getAttribute('data-filter');
            filterInventoryItems(filter);
        });
    });
    
    // Search functionality
    inventorySearch.addEventListener('input', function() {
        const searchTerm = this.value.toLowerCase();
        searchInventoryItems(searchTerm);
    });
    
    // Table action buttons
    document.querySelectorAll('.view-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const itemId = this.getAttribute('data-id');
            viewItem(itemId);
        });
    });
    
    document.querySelectorAll('.edit-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const itemId = this.getAttribute('data-id');
            editItem(itemId);
        });
    });
    
    document.querySelectorAll('.delete-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const itemId = this.getAttribute('data-id');
            showDeleteConfirmation(itemId);
        });
    });
    
    // Delete confirmation buttons
    document.getElementById('cancelDeleteBtn').addEventListener('click', closeModals);
    document.getElementById('confirmDeleteBtn').addEventListener('click', confirmDelete);
    
    // Functions
    function openAddModal() {
        modalTitle.textContent = 'Add New Item';
        inventoryForm.reset();
        document.getElementById('itemId').value = '';
        itemModal.style.display = 'block';
    }
    
    function closeModals() {
        itemModal.style.display = 'none';
        confirmationModal.style.display = 'none';
    }
    
    function handleFormSubmit(e) {
        e.preventDefault();
        
        const itemId = document.getElementById('itemId').value;
        const isEditing = itemId !== '';
        
        // Form data
        const formData = {
            name: document.getElementById('itemName').value,
            type: document.getElementById('itemType').value,
            quantity: document.getElementById('itemQuantity').value,
            expiry: document.getElementById('itemExpiry').value,
            minQuantity: document.getElementById('minQuantity').value,
            remarks: document.getElementById('itemRemarks').value
        };
        
        // Add or update the item
        if (isEditing) {
            updateInventoryItem(itemId, formData);
        } else {
            addInventoryItem(formData);
        }
    }
    
    function addInventoryItem(formData) {
        // Send AJAX request to add item
        fetch('/add_inventory', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: new URLSearchParams({
                'name': formData.name,
                'type': formData.type,
                'quantity': formData.quantity,
                'expiry_date': formData.expiry,
                'min_quantity': formData.minQuantity,
                'remarks': formData.remarks
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Close modal
                closeModals();
                
                // Add new row to table
                const newRow = createTableRow(data.item);
                document.querySelector('#inventoryTable tbody').insertAdjacentHTML('afterbegin', newRow);
                
                // Update event listeners for new row
                attachEventListeners();
                
                // Show success message
                showNotification('Item added successfully!', 'success');
                
                // Update stats
                updateStats(data.stats);
            } else {
                showNotification('Error: ' + data.error, 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showNotification('An error occurred. Please try again.', 'error');
        });
    }
    
    function updateInventoryItem(itemId, formData) {
        // Send AJAX request to update item
        fetch(`/update_inventory/${itemId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: new URLSearchParams({
                'name': formData.name,
                'type': formData.type,
                'quantity': formData.quantity,
                'expiry_date': formData.expiry,
                'min_quantity': formData.minQuantity,
                'remarks': formData.remarks
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Close modal
                closeModals();
                
                // Update row in table
                const row = document.querySelector(`tr[data-id="${itemId}"]`);
                const updatedRow = createTableRow(data.item);
                row.outerHTML = updatedRow;
                
                // Update event listeners
                attachEventListeners();
                
                // Show success message
                showNotification('Item updated successfully!', 'success');
                
                // Update stats
                updateStats(data.stats);
            } else {
                showNotification('Error: ' + data.error, 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showNotification('An error occurred. Please try again.', 'error');
        });
    }
    
    function viewItem(itemId) {
        // Fetch item details
        fetch(`/inventory_item/${itemId}`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Show item details in a modal or dedicated view
                    modalTitle.textContent = 'Item Details: ' + data.item.name;
                    
                    // Populate form fields but disable them
                    document.getElementById('itemId').value = data.item.raw_id;
                    document.getElementById('itemName').value = data.item.name;
                    document.getElementById('itemName').disabled = true;
                    document.getElementById('itemType').value = data.item.type;
                    document.getElementById('itemType').disabled = true;
                    document.getElementById('itemQuantity').value = data.item