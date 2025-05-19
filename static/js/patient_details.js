// Patient Details JavaScript
document.addEventListener("DOMContentLoaded", function() {
    // Tab switching functionality
    const tabButtons = document.querySelectorAll(".tab-button");
    const tabContents = document.querySelectorAll(".tab-content");
    
    tabButtons.forEach(button => {
        button.addEventListener("click", function() {
            // Remove active class from all buttons
            tabButtons.forEach(btn => btn.classList.remove("active"));
            
            // Add active class to clicked button
            this.classList.add("active");
            
            // Hide all tab contents
            tabContents.forEach(content => content.style.display = "none");
            
            // Show the selected tab content
            const tabId = this.getAttribute("data-tab") + "-tab";
            document.getElementById(tabId).style.display = "block";
        });
    });
});

function deletePatient(patientId) {
    if (confirm('Are you sure you want to delete this patient record?')) {
        fetch(`/delete_patient/${patientId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                window.location.href = '/patients';
            } else {
                alert('Error deleting patient: ' + data.error);
            }
        })
        .catch(error => {
            alert('An error occurred: ' + error);
        });
    }
}