# app.py
from flask import Flask, render_template, request, jsonify, redirect, url_for
from db_connector import app as db_app, db, Patient, Appointment, DentalChart, Inventory, RescheduleAppointment, Report, User
from datetime import datetime
# Use the Flask app instance from the connector
app = db_app

# Add this near the top of app.py, after the Flask app is created
app.secret_key = 'pullandentalclinic2025'  # Change this to a secure random value in production

# Set template folder
app.template_folder = 'templates'
app.static_folder = 'static'


@app.route('/')
def index():
    """Redirect to the patients page"""
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Check credentials against database
        user = User.query.filter_by(usersusername=username).first()
        
        if user and user.userspassword == password:
            # In a real application, you should use a secure password hashing method
            # instead of storing/comparing plain text passwords
            
            # Set up a session to keep the user logged in
            from flask import session
            session['user_id'] = user.usersid
            session['username'] = user.usersusername
            session['access_level'] = user.usersaccess
            
            return redirect(url_for('dashboard'))
        
        return render_template('login.html', error="Invalid username or password")

    # Check for success message from registration
    registration_success = request.args.get('registration_success')
    
    return render_template('login.html', 
                          registration_success=registration_success)

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')


@app.route('/patients')
def patients():
    """Render the patients page with data from the database"""
    try:
        # Get patients from the database (exclude deleted ones)
        patients_list = Patient.query.filter_by(is_deleted=False).all()
        print(f"Found {len(patients_list)} patients")
        
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
                'last_visit': last_visit,
                'raw_id': patient.patId  # Add the raw ID for use in URLs
            })
        
        # Get current date for the page
        current_date = datetime.now().strftime("%A, %B %d, %Y")
        
        # Render the template with the data
        return render_template('patients/patients.html', 
                              patients=formatted_patients, 
                              current_date=current_date)
    except Exception as e:
        print(f"Error in patients route: {e}")
        return f"Error loading patients: {e}", 500

@app.route('/patient/<int:patient_id>')
def patient_details(patient_id):
    """View details of a specific patient"""
    try:
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
        
        return render_template('patients/patient_details.html', 
                              patient=patient, 
                              formatted_patient_id=formatted_patient_id,
                              appointments=appointments)
    except Exception as e:
        print(f"Error in patient_details route: {e}")
        return f"Error loading patient details: {e}", 500

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
        print(f"Error in add_patient route: {e}")
        return jsonify({"success": False, "error": str(e)})


@app.route('/delete_patient/<int:patient_id>', methods=['POST'])
def delete_patient(patient_id):
    """Soft delete a patient"""
    try:
        patient = Patient.query.get_or_404(patient_id)
        patient.is_deleted = True
        
        db.session.commit()
        return jsonify({"success": True})
    except Exception as e:
        db.session.rollback()
        print(f"Error in delete_patient route: {e}")
        return jsonify({"success": False, "error": str(e)})

@app.route('/edit_patient/<int:patient_id>')
def edit_patient(patient_id):
    """Render edit patient page"""
    try:
        # Get patient from database
        patient = Patient.query.get_or_404(patient_id)
        
        # Format date of birth for HTML date input
        if patient.patdob:
            patient.patdob = patient.patdob.strftime('%Y-%m-%d')
        
        return render_template('patients/patient_edit.html', patient=patient)
    except Exception as e:
        print(f"Error in edit_patient route: {e}")
        return f"Error loading patient edit form: {e}", 500

@app.route('/update_patient/<int:patient_id>', methods=['POST'])
def update_patient(patient_id):
    """Update patient information"""
    try:
        patient = Patient.query.get_or_404(patient_id)
        
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
        print(f"Error in update_patient route: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/appointments')
def appointments():
    """Render the appointments page with data from the database"""
    try:
        # Get appointments from the database
        appointments_list = Appointment.query.order_by(Appointment.appdate.desc()).all()
        
        # Get all patients for the "Add Appointment" form
        all_patients = Patient.query.filter_by(is_deleted=False).all()
        
        # Format the appointments for display
        formatted_appointments = []
        for appointment in appointments_list:
            # Format appointment data based on the existing fields
            formatted_appointments.append({
                'id': f"APT-{appointment.appid:03d}",
                'patient_name': appointment.apppatient,
                'doctor_name': "Dr. Andrews",  # Default doctor since not in your schema
                'treatment': "General Checkup",  # Default treatment since not in your schema
                'date': appointment.appdate.strftime('%B %d, %Y') if appointment.appdate else "N/A",
                'time': appointment.apptime,
                'duration': "30 min",  # Default duration since not in your schema
                'status': "Scheduled",  # Default status since not in your schema
                'raw_id': appointment.appid
            })
        
        # Get current date for the page
        current_date = datetime.now().strftime("%A, %B %d, %Y")
        today_date = datetime.now().strftime("%Y-%m-%d")
        
        # Render the template with the data
        return render_template('appointments/appointments.html', 
                              appointments=formatted_appointments, 
                              all_patients=all_patients,
                              current_date=current_date,
                              today_date=today_date)
    except Exception as e:
        print(f"Error in appointments route: {e}")
        return f"Error loading appointments: {e}", 500

@app.route('/add_appointment', methods=['POST'])
def add_appointment():
    """Add a new appointment"""
    try:
        # Get patient name from the patient ID
        patient_id = request.form.get('patient_id')
        patient = Patient.query.get(patient_id)
        patient_name = patient.patname if patient else "Unknown Patient"
        
        # Create new appointment using the simple schema
        new_appointment = Appointment(
            apppatient=patient_name,
            apptime=request.form.get('time'),
            appdate=datetime.strptime(request.form.get('date'), '%Y-%m-%d').date()
        )
        
        db.session.add(new_appointment)
        db.session.commit()
        
        # Return success response
        return jsonify({
            "success": True,
            "appointment": {
                "id": f"APT-{new_appointment.appid:03d}",
                "patient_name": new_appointment.apppatient,
                "date": new_appointment.appdate.strftime('%B %d, %Y'),
                "time": new_appointment.apptime,
                "raw_id": new_appointment.appid
            }
        })
    except Exception as e:
        db.session.rollback()
        print(f"Error in add_appointment route: {e}")
        return jsonify({"success": False, "error": str(e)})

@app.route('/cancel_appointment/<int:appointment_id>', methods=['POST'])
def cancel_appointment(appointment_id):
    """Cancel an appointment - since we don't have a status field, we'll just delete it"""
    try:
        appointment = Appointment.query.get_or_404(appointment_id)
        db.session.delete(appointment)
        db.session.commit()
        return jsonify({"success": True})
    except Exception as e:
        db.session.rollback()
        print(f"Error in cancel_appointment route: {e}")
        return jsonify({"success": False, "error": str(e)})

# Placeholder routes to prevent template errors
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

@app.route('/appointment_details/<int:appointment_id>')
def appointment_details(appointment_id):
    """View details of a specific appointment"""
    try:
        appointment = Appointment.query.get_or_404(appointment_id)
        
        # Format the appointment details
        formatted_appointment = {
            'id': f"APT-{appointment.appid:03d}",
            'patient_name': appointment.apppatient,
            'doctor_name': "Dr. Andrews",  # Default value since not in schema
            'treatment': "General Checkup",  # Default value since not in schema
            'date': appointment.appdate.strftime('%B %d, %Y') if appointment.appdate else "N/A",
            'time': appointment.apptime,
            'duration': "30 min",  # Default value since not in schema
            'status': "Scheduled",  # Default value since not in schema
            'notes': "No notes available"  # Default value since not in schema
        }
        
        return render_template('appointment_details.html', appointment=formatted_appointment)
    except Exception as e:
        print(f"Error in appointment_details route: {e}")
        return f"Error loading appointment details: {e}", 500

@app.route('/edit_appointment/<int:appointment_id>')
def edit_appointment(appointment_id):
    """Render edit appointment page"""
    try:
        appointment = Appointment.query.get_or_404(appointment_id)
        all_patients = Patient.query.filter_by(is_deleted=False).all()
        
        return render_template('edit_appointment.html', 
                            appointment=appointment,
                            all_patients=all_patients)
    except Exception as e:
        print(f"Error in edit_appointment route: {e}")
        return f"Error loading appointment edit form: {e}", 500
    


@app.route('/staff')
def staff():
    """Render the staff management page"""
    try:
        # Get all users from the database
        staff_members = User.query.all()
        
        # Format the data for display
        formatted_staff = []
        for staff in staff_members:
            formatted_staff.append({
                'id': f"STF-{staff.usersid:03d}",
                'raw_id': staff.usersid,
                'name': staff.usersrealname or staff.usersusername,
                'email': staff.usersemail or "N/A",
                'contact': staff.userscontact or "N/A",
                'role': staff.usersoccupation or "Staff",
                'access_level': staff.usersaccess or "User",
                'join_date': staff.usersdob or datetime.utcnow(),
                'appointment_count': Appointment.query.filter_by(apppatient=staff.usersrealname).count(),
                'patient_count': Patient.query.filter_by(patname=staff.usersrealname).count()
            })
        
        # Get current date for the page
        current_date = datetime.now().strftime("%A, %B %d, %Y")
        
        return render_template('staff.html', 
                             staff_members=formatted_staff, 
                             current_date=current_date)
    except Exception as e:
        print(f"Error in staff route: {e}")
        return f"Error loading staff page: {e}", 500    

@app.route('/add_staff', methods=['POST'])
def add_staff():
    """Add a new staff member"""
    try:
        # Create new user with staff details
        new_staff = User(
            usersusername=request.form.get('username'),
            userspassword=request.form.get('password'),  # In production, use password hashing
            usersrealname=request.form.get('name'),
            usersemail=request.form.get('email'),
            usershomeaddress=request.form.get('address'),
            userscityzipcode=request.form.get('cityzipcode'),
            userscontact=request.form.get('contact'),
            usersreligion=request.form.get('religion'),
            usersgender=request.form.get('gender'),
            # Only allow 'admin' or default to 'user'
            usersaccess='admin' if request.form.get('access') == 'admin' else 'user'
        )
        
        # Process date of birth if provided
        dob_str = request.form.get('dob')
        if dob_str:
            new_staff.usersdob = datetime.strptime(dob_str, '%Y-%m-%d').date()
        
        # Process age if provided
        age_str = request.form.get('age')
        if age_str and age_str.isdigit():
            new_staff.usersage = int(age_str)
        
        db.session.add(new_staff)
        db.session.commit()
        
        # Return success response
        return jsonify({
            "success": True,
            "staff": {
                "id": f"STF-{new_staff.usersid:03d}",
                "name": new_staff.usersrealname,
                "role": "Staff",  # Default role
                "access_level": new_staff.usersaccess,
                "raw_id": new_staff.usersid
            }
        })
    except Exception as e:
        db.session.rollback()
        print(f"Error in add_staff route: {e}")
        return jsonify({"success": False, "error": str(e)})
    
@app.route('/delete_staff/<int:staff_id>', methods=['POST'])
def delete_staff(staff_id):
    """Delete a staff member"""
    try:
        staff = User.query.get_or_404(staff_id)
        
        # Don't allow deleting self
        from flask import session
        if session.get('user_id') == staff_id:
            return jsonify({"success": False, "error": "Cannot delete your own account"})
        
        # Delete the user
        db.session.delete(staff)
        db.session.commit()
        
        return jsonify({"success": True})
    except Exception as e:
        db.session.rollback()
        print(f"Error in delete_staff route: {e}")
        return jsonify({"success": False, "error": str(e)})

@app.route('/staff_details/<int:staff_id>')
def staff_details(staff_id):
    """View details of a specific staff member"""
    try:
        staff = User.query.get_or_404(staff_id)
        
        return render_template('staff_details.html', staff=staff)
    except Exception as e:
        print(f"Error in staff_details route: {e}")
        return f"Error loading staff details: {e}", 500

@app.route('/edit_staff/<int:staff_id>')
def edit_staff(staff_id):
    """Render edit staff page"""
    try:
        staff = User.query.get_or_404(staff_id)
        
        # Format date of birth for HTML date input
        if staff.usersdob:
            staff.usersdob_formatted = staff.usersdob.strftime('%Y-%m-%d')
        
        return render_template('edit_staff.html', staff=staff)
    except Exception as e:
        print(f"Error in edit_staff route: {e}")
        return f"Error loading staff edit form: {e}", 500

@app.route('/update_staff/<int:staff_id>', methods=['POST'])
def update_staff(staff_id):
    """Update staff information"""
    try:
        staff = User.query.get_or_404(staff_id)
        
        # Update staff information from form
        staff.usersrealname = request.form.get('name')
        staff.usersemail = request.form.get('email')
        staff.userscontact = request.form.get('contact')
        staff.usershomeaddress = request.form.get('address')
        staff.userscityzipcode = request.form.get('cityzipcode')
        staff.usersreligion = request.form.get('religion')
        staff.usersgender = request.form.get('gender')
        # Only allow 'admin' or default to 'user'
        staff.usersaccess = 'admin' if request.form.get('access') == 'admin' else 'user'
        
        # Process date of birth if provided
        dob_str = request.form.get('dob')
        if dob_str:
            staff.usersdob = datetime.strptime(dob_str, '%Y-%m-%d').date()
        
        # Process age if provided
        age_str = request.form.get('age')
        if age_str and age_str.isdigit():
            staff.usersage = int(age_str)
        
        # Update password if provided
        new_password = request.form.get('password')
        if new_password:
            staff.userspassword = new_password  # In production, use password hashing
        
        # Save changes to database
        db.session.commit()
        
        # Return success response for AJAX request
        return jsonify({'success': True})
    
    except Exception as e:
        # Return error response for AJAX request
        db.session.rollback()
        print(f"Error in update_staff route: {e}")
        return jsonify({'success': False, 'error': str(e)})
        
# Add these inventory routes to app.py, after the existing routes

@app.route('/inventory')
def inventory():
    """Render the inventory management page with data from database"""
    try:
        # Get inventory items from the database
        inventory_items = Inventory.query.all()
        
        # Format the data for display
        formatted_items = []
        for item in inventory_items:
            formatted_items.append({
                'id': f"INV-{item.invid:03d}",  # Changed from itemId to invid
                'name': item.invname,           # Changed from name to invname
                'type': item.invtype,           # Changed from type to invtype
                'quantity': item.invquantity,   # Changed from quantity to invquantity
                'expiry': item.invdoe.strftime('%Y-%m-%d') if item.invdoe else "N/A",  # Changed from expiry_date to invdoe
                'min_quantity': 5,              # This field doesn't exist in your model, so using a default value
                'status': "Low" if item.invquantity < 5 else "OK",  # Using default minimum quantity of 5
                'remarks': item.invremarks or "",  # Changed from remarks to invremarks
                'raw_id': item.invid           # Changed from itemId to invid
            })
        
        # Get current date for the page
        current_date = datetime.now().strftime("%A, %B %d, %Y")
        
        # Get stats for dashboard
        total_items = len(inventory_items)
        low_stock = sum(1 for item in inventory_items if item.invquantity < 5)  # Using default min of 5
        expired = sum(1 for item in inventory_items if item.invdoe and item.invdoe < datetime.now().date())
        
        # Calculate rough total value (just for display purposes)
        total_value = sum(item.invquantity * 10 for item in inventory_items)  # Rough estimate of $10 per item
        
        # Render the template with the data
        return render_template('inventory.html', 
                              inventory_items=formatted_items,
                              total_items=total_items,
                              low_stock_count=low_stock,
                              expired_count=expired,
                              total_value=total_value,
                              current_date=current_date)
    except Exception as e:
        print(f"Error in inventory route: {e}")
        return f"Error loading inventory: {e}", 500
    
@app.route('/inventory_item/<int:item_id>')
def get_inventory_item(item_id):
    """Get details of a specific inventory item"""
    try:
        item = Inventory.query.get_or_404(item_id)
        
        # Format the item for JSON response
        formatted_item = {
            'id': f"INV-{item.invid:03d}",
            'name': item.invname, 
            'type': item.invtype,
            'quantity': item.invquantity,
            'expiry_date': item.invdoe.strftime('%Y-%m-%d') if item.invdoe else "",
            'min_quantity': 5,  # Default value
            'remarks': item.invremarks or "",
            'raw_id': item.invid
        }
        
        return jsonify({"success": True, "item": formatted_item})
    except Exception as e:
        print(f"Error in get_inventory_item route: {e}")
        return jsonify({"success": False, "error": str(e)})

@app.route('/add_inventory', methods=['POST'])
def add_inventory():
    """Add a new inventory item"""
    try:
        # Create new inventory item
        new_item = Inventory(
            invname=request.form.get('name'),
            invtype=request.form.get('type'),
            invquantity=int(request.form.get('quantity', 0)),
            invremarks=request.form.get('remarks', '')
        )
        
        # Process expiry date if provided
        expiry_date = request.form.get('expiry_date')
        if expiry_date:
            new_item.invdoe = datetime.strptime(expiry_date, '%Y-%m-%d').date()
        
        db.session.add(new_item)
        db.session.commit()
        
        # Get updated stats
        total_items = Inventory.query.count()
        low_stock = Inventory.query.filter(Inventory.invquantity < 5).count()
        expired = Inventory.query.filter(
            Inventory.invdoe.isnot(None), 
            Inventory.invdoe < datetime.now().date()
        ).count()
        
        # Format the item for JSON response
        formatted_item = {
            'id': f"INV-{new_item.invid:03d}",
            'name': new_item.invname,
            'type': new_item.invtype,
            'quantity': new_item.invquantity,
            'expiry': new_item.invdoe.strftime('%Y-%m-%d') if new_item.invdoe else "N/A",
            'min_quantity': 5,  # Default value
            'status': "Low" if new_item.invquantity < 5 else "OK",
            'remarks': new_item.invremarks or "",
            'raw_id': new_item.invid
        }
        
        # Stats for the dashboard
        inventory_stats = {
            'total_items': total_items,
            'low_stock': low_stock,
            'expired': expired,
            'total_value': total_items * 10  # Rough estimate
        }
        
        return jsonify({
            "success": True, 
            "item": formatted_item,
            "stats": inventory_stats
        })
    except Exception as e:
        db.session.rollback()
        print(f"Error in add_inventory route: {e}")
        return jsonify({"success": False, "error": str(e)})

@app.route('/update_inventory/<int:item_id>', methods=['POST'])
def update_inventory(item_id):
    """Update an inventory item"""
    try:
        item = Inventory.query.get_or_404(item_id)
        
        # Update item details
        item.invname = request.form.get('name')
        item.invtype = request.form.get('type')
        item.invquantity = int(request.form.get('quantity', 0))
        item.invremarks = request.form.get('remarks', '')
        
        # Process expiry date if provided
        expiry_date = request.form.get('expiry_date')
        if expiry_date:
            item.invdoe = datetime.strptime(expiry_date, '%Y-%m-%d').date()
        else:
            item.invdoe = None
        
        db.session.commit()
        
        # Get updated stats
        total_items = Inventory.query.count()
        low_stock = Inventory.query.filter(Inventory.invquantity < 5).count()
        expired = Inventory.query.filter(
            Inventory.invdoe.isnot(None), 
            Inventory.invdoe < datetime.now().date()
        ).count()
        
        # Format the item for JSON response
        formatted_item = {
            'id': f"INV-{item.invid:03d}",
            'name': item.invname,
            'type': item.invtype,
            'quantity': item.invquantity,
            'expiry': item.invdoe.strftime('%Y-%m-%d') if item.invdoe else "N/A",
            'min_quantity': 5,  # Default value
            'status': "Low" if item.invquantity < 5 else "OK",
            'remarks': item.invremarks or "",
            'raw_id': item.invid
        }
        
        # Stats for the dashboard
        inventory_stats = {
            'total_items': total_items,
            'low_stock': low_stock,
            'expired': expired,
            'total_value': total_items * 10  # Rough estimate
        }
        
        return jsonify({
            "success": True, 
            "item": formatted_item,
            "stats": inventory_stats
        })
    except Exception as e:
        db.session.rollback()
        print(f"Error in update_inventory route: {e}")
        return jsonify({"success": False, "error": str(e)})

@app.route('/delete_inventory/<int:item_id>', methods=['POST'])
def delete_inventory(item_id):
    """Delete an inventory item"""
    try:
        item = Inventory.query.get_or_404(item_id)
        db.session.delete(item)
        db.session.commit()
        
        # Get updated stats
        total_items = Inventory.query.count()
        low_stock = Inventory.query.filter(Inventory.invquantity < 5).count()
        expired = Inventory.query.filter(
            Inventory.invdoe.isnot(None), 
            Inventory.invdoe < datetime.now().date()
        ).count()
        
        # Stats for the dashboard
        inventory_stats = {
            'total_items': total_items,
            'low_stock': low_stock,
            'expired': expired,
            'total_value': total_items * 10  # Rough estimate
        }
        
        return jsonify({"success": True, "stats": inventory_stats})
    except Exception as e:
        db.session.rollback()
        print(f"Error in delete_inventory route: {e}")
        return jsonify({"success": False, "error": str(e)})

@app.route('/filter_inventory/<filter_type>')
def filter_inventory(filter_type):
    """Filter inventory items by type"""
    try:
        query = Inventory.query
        
        # Apply filter
        if filter_type == 'low_stock':
            query = query.filter(Inventory.invquantity < 5)
        elif filter_type == 'expired':
            query = query.filter(
                Inventory.invdoe.isnot(None), 
                Inventory.invdoe < datetime.now().date()
            )
        elif filter_type != 'all':
            # If filter is not 'all', assume it's a type filter
            query = query.filter_by(invtype=filter_type)
        
        # Get filtered items
        inventory_items = query.all()
        
        # Format the data for response
        formatted_items = []
        for item in inventory_items:
            formatted_items.append({
                'id': f"INV-{item.invid:03d}",
                'name': item.invname,
                'type': item.invtype,
                'quantity': item.invquantity,
                'expiry': item.invdoe.strftime('%Y-%m-%d') if item.invdoe else "N/A",
                'min_quantity': 5,  # Default value
                'status': "Low" if item.invquantity < 5 else "OK",
                'remarks': item.invremarks or "",
                'raw_id': item.invid
            })
        
        return jsonify({"success": True, "items": formatted_items})
    except Exception as e:
        print(f"Error in filter_inventory route: {e}")
        return jsonify({"success": False, "error": str(e)})
    
@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/register_process', methods=['POST'])
def register_process():
    """Process new user registration"""
    try:
        # Get form data
        username = request.form.get('usersusername')
        password = request.form.get('userspassword')
        confirm_password = request.form.get('confirm_password')
        realname = request.form.get('usersrealname')
        email = request.form.get('usersemail')
        home_address = request.form.get('usershomeaddress')
        city_zipcode = request.form.get('userscityzipcode')
        contact = request.form.get('userscontact')
        religion = request.form.get('usersreligion')
        gender = request.form.get('usersgender')
        occupation = request.form.get('usersoccupation')
        
        # Validate passwords match
        if password != confirm_password:
            return render_template('register.html', error="Passwords do not match")
        
        # Check if username already exists
        existing_user = User.query.filter_by(usersusername=username).first()
        if existing_user:
            return render_template('register.html', error="Username already exists")
        
        # Create new user with default access level
        new_user = User(
            usersusername=username,
            userspassword=password,  # In production, you should hash this password
            usersrealname=realname,
            usersemail=email,
            usershomeaddress=home_address,
            userscityzipcode=city_zipcode,
            userscontact=contact,
            usersreligion=religion,
            usersgender=gender,
            usersoccupation=occupation,
            usersaccess='user'  # Default access level
        )
        
        # Process date of birth if provided
        dob_str = request.form.get('usersdob')
        if dob_str:
            new_user.usersdob = datetime.strptime(dob_str, '%Y-%m-%d').date()
        
        # Process age if provided
        age_str = request.form.get('usersage')
        if age_str and age_str.isdigit():
            new_user.usersage = int(age_str)
        
        # Save user to database
        db.session.add(new_user)
        db.session.commit()
        
        # Redirect to login page with success message
        return redirect(url_for('login', registration_success=True))
    
    except Exception as e:
        # If any error occurs, rollback the session
        db.session.rollback()
        print(f"Error in register_process route: {e}")
        return render_template('register.html', error=f"Registration failed: {str(e)}")
    
if __name__ == '__main__':
    app.run(debug=True)