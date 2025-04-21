# app.py
from flask import Flask, render_template, request, jsonify, redirect, url_for
from db_connector import app as db_app, db, Patient
from datetime import datetime

# Use the Flask app instance from the connector
app = db_app

# Set template folder
app.template_folder = 'templates'
app.static_folder = 'static'

@app.route('/')
def index():
    """Redirect to the patients page"""
    return redirect(url_for('patients'))

@app.route('/patients')
def patients():
    """Render the patients page with data from the database"""
    # Get patients from the database (exclude deleted ones)
    patients_list = Patient.query.filter_by(is_deleted=False).all()
    
    # Format the data for display
    formatted_patients = []
    for patient in patients_list:
        # Format date if it exists
        last_visit = "N/A"  # Default if no visit data
        
        formatted_patients.append({
            'id': f"PAT-{patient.patId:03d}",
            'name': patient.patname,
            'contact': patient.patcontact or "N/A",
            'gender': patient.patgender or "N/A",
            'age': patient.patage or "N/A",
            'address': patient.pataddress or "N/A",
            'last_visit': last_visit
        })
    
    # Get current date for the page
    current_date = datetime.now().strftime("%A, %B %d, %Y")
    
    # Render the template with the data
    return render_template('patients.html', 
                          patients=formatted_patients, 
                          current_date=current_date)

@app.route('/patient/<int:patient_id>')
def patient_details(patient_id):
    """View details of a specific patient"""
    patient = Patient.query.get_or_404(patient_id)
    
    # Format the patient ID with leading zeros
    formatted_patient_id = f"PAT-{patient.patId:03d}"
    
    # Add some example appointments (later you would query these from a database)
    appointments = [
        {
            'date': 'April 15, 2025',
            'time': '09:30 AM',
            'treatment': 'Teeth Cleaning',
            'doctor': 'Dr. Andrews',
            'status': 'completed'
        },
        {
            'date': 'May 10, 2025',
            'time': '11:00 AM',
            'treatment': 'Follow-up',
            'doctor': 'Dr. Andrews',
            'status': 'upcoming'
        }
    ]
    
    return render_template('patient_details.html', 
                          patient=patient, 
                          formatted_patient_id=formatted_patient_id,
                          appointments=appointments)

@app.route('/add_patient', methods=['POST'])
def add_patient():
    """Add a new patient via AJAX"""
    try:
        # Get form data and create a new patient
        new_patient = Patient(
            patname=request.form.get('name'),
            patemail=request.form.get('email'),
            pataddress=request.form.get('address'),
            patcityzipcode=request.form.get('cityzipcode'),
            patcontact=request.form.get('contact'),
            patreligion=request.form.get('religion'),
            patgender=request.form.get('gender'),
            patage=request.form.get('age', type=int),
            patoccupation=request.form.get('occupation'),
            patallergies=request.form.get('allergies'),
            is_deleted=False
        )
        
        if request.form.get('dob'):
            try:
                new_patient.patdob = datetime.strptime(request.form.get('dob'), '%Y-%m-%d').date()
            except ValueError:
                return jsonify({"success": False, "error": "Invalid date format"})
                
        db.session.add(new_patient)
        db.session.commit()
        
        # Return the new patient data for dynamic addition to the table
        return jsonify({
            "success": True,
            "patient": {
                "id": f"PAT-{new_patient.patId:03d}",
                "name": new_patient.patname,
                "contact": new_patient.patcontact or "N/A",
                "gender": new_patient.patgender or "N/A",
                "age": new_patient.patage or "N/A",
                "address": new_patient.pataddress or "N/A",
                "last_visit": "N/A",
                "raw_id": new_patient.patId
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)})


@app.route('/delete_patient/<int:patient_id>', methods=['POST'])
def delete_patient(patient_id):
    """Soft delete a patient"""
    patient = Patient.query.get_or_404(patient_id)
    patient.is_deleted = True
    
    try:
        db.session.commit()
        return jsonify({"success": True})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)})

# Placeholder routes to prevent template errors
@app.route('/appointments')
def appointments():
    """Placeholder for appointments page"""
    return "Appointments page - Coming soon!"

@app.route('/doctors')
def doctors():
    """Placeholder for doctors page"""
    return "Doctors page - Coming soon!"

@app.route('/treatments')
def treatments():
    """Placeholder for treatments page"""
    return "Treatments page - Coming soon!"

@app.route('/billing')
def billing():
    """Placeholder for billing page"""
    return "Billing page - Coming soon!"

@app.route('/settings')
def settings():
    """Placeholder for settings page"""
    return "Settings page - Coming soon!"

@app.route('/logout')
def logout():
    """Placeholder for logout functionality"""
    return redirect(url_for('index'))


# Add these routes to your Flask application

from flask import render_template, request, redirect, url_for, jsonify, flash
from datetime import datetime

@app.route('/edit_patient/<int:patient_id>')
def edit_patient(patient_id):
    """Render edit patient page"""
    # Get patient from database
    patient = Patient.query.get_or_404(patient_id)
    
    # Format date of birth for HTML date input
    if patient.patdob:
        patient.patdob = patient.patdob.strftime('%Y-%m-%d')
    
    return render_template('patient_edit.html', patient=patient)

@app.route('/update_patient/<int:patient_id>', methods=['POST'])
def update_patient(patient_id):
    """Update patient information"""
    patient = Patient.query.get_or_404(patient_id)
    
    try:
        # Update patient information from form
        patient.patname = request.form.get('name')
        patient.patemail = request.form.get('email')
        patient.patcontact = request.form.get('contact')
        
        # Process date of birth if provided
        dob_str = request.form.get('dob')
        if dob_str:
            patient.patdob = datetime.strptime(dob_str, '%Y-%m-%d').date()
        
        patient.patgender = request.form.get('gender')
        
        # Process age if provided
        age_str = request.form.get('age')
        if age_str and age_str.isdigit():
            patient.patage = int(age_str)
        
        patient.pataddress = request.form.get('address')
        patient.patcityzipcode = request.form.get('cityzipcode')
        patient.patoccupation = request.form.get('occupation')
        patient.patreligion = request.form.get('religion')
        patient.patallergies = request.form.get('allergies')
        
        # Save changes to database
        db.session.commit()
        
        # Return success response for AJAX request
        return jsonify({'success': True})
    
    except Exception as e:
        # Return error response for AJAX request
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True)