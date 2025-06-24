// Patient Details JavaScript - Updated with real data handling
document.addEventListener("DOMContentLoaded", function() {
    // Tab switching functionality
    const tabButtons = document.querySelectorAll(".tab-button");
    const tabContents = document.querySelectorAll(".tab-content");
    
    tabButtons.forEach(button => {
        button.addEventListener("click", function() {
            // Remove active class from all buttons and contents
            tabButtons.forEach(btn => btn.classList.remove("active"));
            tabContents.forEach(content => content.classList.remove("active"));
            
            // Add active class to clicked button
            this.classList.add("active");
            
            // Show the selected tab content
            const tabId = this.getAttribute("data-tab") + "-tab";
            const targetContent = document.getElementById(tabId);
            if (targetContent) {
                targetContent.classList.add("active");
            }
        });
    });
    
    // Add tooltips for teeth conditions
    const teeth = document.querySelectorAll('.tooth');
    teeth.forEach(tooth => {
        tooth.addEventListener('mouseenter', function() {
            const condition = this.className.split(' ')[1]; // Get the condition class
            const toothNumber = this.textContent;
            this.title = `Tooth ${toothNumber}: ${condition.charAt(0).toUpperCase() + condition.slice(1)}`;
        });
    });
    
    // Handle appointment status styling
    const appointmentItems = document.querySelectorAll('.appointment-item');
    appointmentItems.forEach(item => {
        const statusElement = item.querySelector('.status');
        if (statusElement) {
            const status = statusElement.textContent.toLowerCase().trim();
            
            // Add appropriate styling based on status
            if (status === 'today') {
                item.style.borderLeftColor = '#ffc107';
            } else if (status === 'upcoming') {
                item.style.borderLeftColor = '#17a2b8';
            } else if (status === 'completed') {
                item.style.borderLeftColor = '#28a745';
            }
        }
    });
});

function deletePatient(patientId) {
    if (confirm('Are you sure you want to delete this patient record? This action cannot be undone.')) {
        // Show loading state
        const deleteBtn = document.querySelector('.delete-btn');
        const originalText = deleteBtn.innerHTML;
        deleteBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Deleting...';
        deleteBtn.disabled = true;
        
        fetch(`/delete_patient/${patientId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Show success message briefly before redirect
                deleteBtn.innerHTML = '<i class="fas fa-check"></i> Deleted';
                deleteBtn.style.backgroundColor = '#28a745';
                
                setTimeout(() => {
                    window.location.href = '/patients';
                }, 1000);
            } else {
                // Restore button state
                deleteBtn.innerHTML = originalText;
                deleteBtn.disabled = false;
                alert('Error deleting patient: ' + data.error);
            }
        })
        .catch(error => {
            // Restore button state
            deleteBtn.innerHTML = originalText;
            deleteBtn.disabled = false;
            alert('An error occurred: ' + error);
        });
    }
}

function printChart() {
    // Extract patient ID from the current URL or from a data attribute
    const patientId = window.location.pathname.split('/').pop();
    window.open(`/print_dental_chart/${patientId}`, '_blank');
}

function addNewProcedure() {
    // Redirect to the full dental chart page where procedures can be added
    const patientId = window.location.pathname.split('/').pop();
    window.location.href = `/patient_dental_chart/${patientId}`;
}

// Function to refresh appointment data (useful for real-time updates)
function refreshAppointments() {
    const patientId = window.location.pathname.split('/').pop();
    
    fetch(`/patient/${patientId}/appointments`)
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            updateAppointmentsList(data.appointments);
        }
    })
    .catch(error => {
        console.error('Error refreshing appointments:', error);
    });
}

// Function to update appointments list dynamically
function updateAppointmentsList(appointments) {
    const appointmentsTab = document.getElementById('appointments-tab');
    const appointmentsList = appointmentsTab.querySelector('.appointments-list');
    
    if (appointmentsList) {
        // Clear existing appointments
        appointmentsList.innerHTML = '';
        
        // Add updated appointments
        appointments.forEach(appointment => {
            const appointmentHTML = `
                <div class="appointment-item">
                    <div>
                        <div class="appointment-date">${appointment.date} - ${appointment.time}</div>
                        <div class="appointment-info">
                            Appointment ID: ${appointment.id}
                        </div>
                    </div>
                    <span class="status ${appointment.status}">${appointment.status.charAt(0).toUpperCase() + appointment.status.slice(1)}</span>
                </div>
            `;
            appointmentsList.innerHTML += appointmentHTML;
        });
    }
}

// Auto-refresh appointments every 30 seconds (optional)
setInterval(refreshAppointments, 30000);