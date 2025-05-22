# app.py - Fixed version with DNS resolution handling + User Logs System
from flask import Flask, render_template, request, jsonify, redirect, url_for, send_file, session, make_response
from db_connector import app as db_app, db, Patient, Appointment, DentalChart, Inventory, RescheduleAppointment, Report, User, UserLog, log_user_action
from datetime import datetime, date
import os
import time
import subprocess
import json
import pymysql
import re
import socket
import csv
from io import StringIO
from functools import wraps

# Use the Flask app instance from the connector
app = db_app

# Add this near the top of app.py, after the Flask app is created
app.secret_key = 'pullandentalclinic2025'  # Change this to a secure random value in production

# Set template folder
app.template_folder = 'templates'
app.static_folder = 'static'

# Decorator to check admin access
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('access_level') != 'admin':
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# DNS Resolution fix for backup functionality
def resolve_host(host):
    """Resolve hostname issues for backup functionality"""
    try:
        # Test if the host can be resolved
        socket.gethostbyname(host)
        return host
    except socket.gaierror:
        # If localhost fails, try 127.0.0.1
        if host == 'localhost':
            try:
                socket.gethostbyname('127.0.0.1')
                return '127.0.0.1'
            except socket.gaierror:
                pass
        # If 127.0.0.1 fails, try localhost
        elif host == '127.0.0.1':
            try:
                socket.gethostbyname('localhost')
                return 'localhost'
            except socket.gaierror:
                pass
    
    # Return original host if nothing works
    return host

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
            session['user_id'] = user.usersid
            session['username'] = user.usersusername
            session['access_level'] = user.usersaccess
            session['real_name'] = user.usersrealname
            
            # Log the login action
            log_user_action(user.usersid, 'Login', f'User {username} logged in successfully')
            
            return redirect(url_for('dashboard'))
        
        return render_template('login.html', error="Invalid username or password")

    # Check for success message from registration
    registration_success = request.args.get('registration_success')
    
    return render_template('login.html', 
                          registration_success=registration_success)

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/logout')
def logout():
    """Log out the current user"""
    user_id = session.get('user_id')
    username = session.get('username')
    
    if user_id:
        # Log the logout action
        log_user_action(user_id, 'Logout', f'User {username} logged out')
    
    # Clear the session
    session.clear()
    return redirect(url_for('login'))

#___________________________________________________________________________________________
# USER LOGS ROUTES - ADMIN ONLY
@app.route('/user_logs')
@admin_required
def user_logs():
    """Display user activity logs - Admin only"""
    try:
        # Get filter parameters
        user_id = request.args.get('user_id')
        action = request.args.get('action')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        page = int(request.args.get('page', 1))
        per_page = 50  # Number of logs per page
        
        # Build query
        query = db.session.query(
            UserLog.log_id,
            UserLog.user_id,
            UserLog.action,
            UserLog.timestamp,
            UserLog.details,
            User.usersrealname.label('user_name'),
            User.usersusername.label('username')
        ).outerjoin(User, UserLog.user_id == User.usersid)
        
        # Apply filters
        if user_id:
            query = query.filter(UserLog.user_id == user_id)
        if action:
            query = query.filter(UserLog.action == action)
        if date_from:
            query = query.filter(UserLog.timestamp >= datetime.strptime(date_from, '%Y-%m-%d'))
        if date_to:
            query = query.filter(UserLog.timestamp <= datetime.strptime(date_to + ' 23:59:59', '%Y-%m-%d %H:%M:%S'))
        
        # Order by timestamp (newest first)
        query = query.order_by(UserLog.timestamp.desc())
        
        # Get total count for pagination
        total_logs = query.count()
        
        # Get paginated results
        logs = query.offset((page - 1) * per_page).limit(per_page).all()
        
        # Format logs for display
        formatted_logs = []
        for log in logs:
            formatted_logs.append({
                'log_id': log.log_id,
                'user_id': log.user_id,
                'user_name': log.user_name,
                'username': log.username,
                'action': log.action,
                'timestamp': log.timestamp,
                'formatted_timestamp': log.timestamp.strftime('%Y-%m-%d %H:%M:%S') if log.timestamp else 'N/A',
                'details': log.details
            })
        
        # Calculate pagination
        total_pages = (total_logs + per_page - 1) // per_page
        
        # Get statistics
        total_logs_count = UserLog.query.count()
        today_logs = UserLog.query.filter(
            UserLog.timestamp >= datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        ).count()
        active_users = db.session.query(UserLog.user_id).distinct().count()
        critical_actions = UserLog.query.filter(
            UserLog.action.in_(['Delete Patient', 'Delete Appointment', 'Database Backup', 'Database Restore'])
        ).count()
        
        # Get all users for filter dropdown
        all_users = User.query.order_by(User.usersrealname).all()
        
        return render_template('user_logs.html',
                               logs=formatted_logs,
                               total_logs=total_logs_count,
                               today_logs=today_logs,
                               active_users=active_users,
                               critical_actions=critical_actions,
                               all_users=all_users,
                               page=page,
                               total_pages=total_pages,
                               current_date=datetime.now().strftime('%B %d, %Y'))
    
    except Exception as e:
        print(f"Error in user_logs route: {e}")
        return f"Error loading user logs: {e}", 500

@app.route('/export_logs')
@admin_required
def export_logs():
    """Export user logs to CSV - Admin only"""
    try:
        # Get filter parameters (same as user_logs route)
        user_id = request.args.get('user_id')
        action = request.args.get('action')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        
        # Build query
        query = db.session.query(
            UserLog.log_id,
            UserLog.user_id,
            UserLog.action,
            UserLog.timestamp,
            UserLog.details,
            User.usersrealname.label('user_name'),
            User.usersusername.label('username')
        ).outerjoin(User, UserLog.user_id == User.usersid)
        
        # Apply filters
        if user_id:
            query = query.filter(UserLog.user_id == user_id)
        if action:
            query = query.filter(UserLog.action == action)
        if date_from:
            query = query.filter(UserLog.timestamp >= datetime.strptime(date_from, '%Y-%m-%d'))
        if date_to:
            query = query.filter(UserLog.timestamp <= datetime.strptime(date_to + ' 23:59:59', '%Y-%m-%d %H:%M:%S'))
        
        # Order by timestamp (newest first)
        logs = query.order_by(UserLog.timestamp.desc()).all()
        
        # Create CSV content
        output = StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(['Log ID', 'User ID', 'User Name', 'Username', 'Action', 'Timestamp', 'Details'])
        
        # Write data
        for log in logs:
            writer.writerow([
                log.log_id,
                log.user_id or 'N/A',
                log.user_name or 'N/A',
                log.username or 'N/A',
                log.action or 'N/A',
                log.timestamp.strftime('%Y-%m-%d %H:%M:%S') if log.timestamp else 'N/A',
                log.details or 'N/A'
            ])
        
        # Create response
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename=user_logs_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        
        # Log the export action
        log_user_action(session.get('user_id'), 'Export Logs', f'User exported {len(logs)} log entries')
        
        return response
    
    except Exception as e:
        print(f"Error exporting logs: {e}")
        return jsonify({"success": False, "error": str(e)})

#___________________________________________________________________________________________
#Patient Routes
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
        
        # Log the action
        log_user_action(
            session.get('user_id'),
            'Create Patient',
            f'Created new patient: {new_patient.patname} (ID: PAT-{new_patient.patId:03d})'
        )
        
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
        
        # Log the action
        log_user_action(
            session.get('user_id'),
            'Delete Patient',
            f'Soft deleted patient: {patient.patname} (ID: PAT-{patient.patId:03d})'
        )
        
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
        
        # Store old values for logging
        old_name = patient.patname
        
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
        
        # Log the action
        log_user_action(
            session.get('user_id'),
            'Update Patient',
            f'Updated patient: {old_name} -> {patient.patname} (ID: PAT-{patient.patId:03d})'
        )
        
        # Return success response for AJAX request
        return jsonify({'success': True})
    
    except Exception as e:
        # Return error response for AJAX request
        db.session.rollback()
        print(f"Error in update_patient route: {e}")
        return jsonify({'success': False, 'error': str(e)})

# ______________________________________________________________________________________________________
# Appointments management routes
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
        
        # Log the action
        log_user_action(
            session.get('user_id'),
            'Create Appointment',
            f'Created appointment for {patient_name} on {new_appointment.appdate} at {new_appointment.apptime}'
        )
        
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

@app.route('/cancel_appointment', methods=['POST'])
def cancel_appointment():
    """Cancel an appointment - since we don't have a status field, we'll just delete it"""
    try:
        appointment_id = request.form.get('appointment_id')
        if not appointment_id:
            return jsonify({"success": False, "error": "No appointment ID provided"})
            
        appointment = Appointment.query.get_or_404(int(appointment_id))
        
        # Log the action before deleting
        log_user_action(
            session.get('user_id'),
            'Delete Appointment',
            f'Cancelled/deleted appointment for {appointment.apppatient} on {appointment.appdate} at {appointment.apptime}'
        )
        
        db.session.delete(appointment)
        db.session.commit()
        
        return jsonify({"success": True})
    except Exception as e:
        db.session.rollback()
        print(f"Error in cancel_appointment route: {e}")
        return jsonify({"success": False, "error": str(e)})

@app.route('/appointment_details/<int:appointment_id>')
def appointment_details(appointment_id):
    """View details of a specific appointment"""
    try:
        appointment = Appointment.query.get_or_404(appointment_id)
        
        # Let's assume you need to look up the patient based on the name
        patient = Patient.query.filter_by(patname=appointment.apppatient).first()
        patient_id = patient.patId if patient else None
        
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
            'notes': "No notes available",  # Default value since not in schema
            'raw_id': appointment.appid,  # Add the raw ID for use in forms and links
            'patient_id': f"PAT-{patient.patId:03d}" if patient else "Unknown",  # Formatted patient ID
            'raw_patient_id': patient_id,  # <-- Add this raw patient ID
            'patient_phone': patient.patcontact if patient else "N/A",
            'patient_email': patient.patemail if patient else "N/A"
        }
        
        # Get current date for the page
        current_date = datetime.now().strftime("%A, %B %d, %Y")
        
        return render_template('appointments/appointment_details.html', 
                             appointment=formatted_appointment,
                             current_date=current_date)
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
    
@app.route('/reschedule_appointment', methods=['POST'])
def reschedule_appointment():
    """Reschedule an existing appointment and record the change"""
    try:
        appointment_id = request.form.get('appointment_id')
        new_date = request.form.get('date')
        new_time = request.form.get('time')
        reason = request.form.get('reason', '')
        
        # Input validation
        if not appointment_id or not new_date or not new_time:
            return jsonify({"success": False, "error": "Missing required fields"})
        
        # Get the appointment
        appointment = Appointment.query.get_or_404(int(appointment_id))
        
        # Get the next ID for the reschedule record
        # First try to get the maximum ID from the rappointment table
        max_id_result = db.session.query(db.func.max(RescheduleAppointment.rappid)).first()
        next_id = 1  # Default if table is empty
        if max_id_result[0] is not None:
            next_id = max_id_result[0] + 1
        
        # Record the rescheduling in rappointment table
        reschedule_record = RescheduleAppointment(
            rappid=next_id,  # Set the primary key
            rapppatient=appointment.apppatient,
            rapptime=appointment.apptime,
            rappdate=appointment.appdate,
            rappnewtime=new_time,
            rappnewdate=datetime.strptime(new_date, '%Y-%m-%d').date(),
            rappreason=reason
        )
        
        # Store old values for logging
        old_date = appointment.appdate
        old_time = appointment.apptime
        
        # Update the original appointment
        appointment.appdate = datetime.strptime(new_date, '%Y-%m-%d').date()
        appointment.apptime = new_time
        
        # Save both changes to database
        db.session.add(reschedule_record)
        db.session.commit()
        
        # Log the action
        log_user_action(
            session.get('user_id'),
            'Reschedule Appointment',
            f'Rescheduled appointment for {appointment.apppatient} from {old_date} {old_time} to {appointment.appdate} {appointment.apptime}. Reason: {reason}'
        )
        
        return jsonify({
            "success": True,
            "message": f"Appointment for {appointment.apppatient} rescheduled from {old_date.strftime('%B %d, %Y')} at {old_time} to {appointment.appdate.strftime('%B %d, %Y')} at {appointment.apptime}"
        })
    except Exception as e:
        db.session.rollback()
        print(f"Error in reschedule_appointment route: {e}")
        return jsonify({"success": False, "error": str(e)})
        
@app.route('/mark_appointment_completed/<int:appointment_id>', methods=['POST'])
def mark_appointment_completed(appointment_id):
    """Mark an appointment as completed
    
    Note: Since our schema doesn't have a status field, we'll just pretend to update it
    In a real application, you would add a status field to the Appointment model
    """
    try:
        # Get the appointment to make sure it exists
        appointment = Appointment.query.get_or_404(appointment_id)
        
        # Log the action
        log_user_action(
            session.get('user_id'),
            'Complete Appointment',
            f'Marked appointment as completed for {appointment.apppatient} on {appointment.appdate} at {appointment.apptime}'
        )
        
        # Since we don't have a status field, we'll just return success
        # In a real application, you would update the status field here
        
        return jsonify({"success": True})
    except Exception as e:
        print(f"Error in mark_appointment_completed route: {e}")
        return jsonify({"success": False, "error": str(e)})
    
@app.route('/rescheduled_appointments')
def rescheduled_appointments():
    """Render the rescheduled appointments page with data from the database"""
    try:
        # Get rescheduled appointments from the database
        rescheduled_list = RescheduleAppointment.query.order_by(RescheduleAppointment.rappnewdate.desc()).all()
        
        # Format the rescheduled appointments for display
        formatted_rescheduled = []
        for reschedule in rescheduled_list:
            # Format appointment data based on the existing fields
            formatted_rescheduled.append({
                'id': f"RSC-{reschedule.rappid:03d}",
                'patient_name': reschedule.rapppatient,
                'original_date': reschedule.rappdate.strftime('%B %d, %Y') if reschedule.rappdate else "N/A",
                'original_time': reschedule.rapptime or "N/A",
                'new_date': reschedule.rappnewdate.strftime('%B %d, %Y') if reschedule.rappnewdate else "N/A",
                'new_time': reschedule.rappnewtime or "N/A",
                'reason': reschedule.rappreason or "No reason provided",
                'raw_id': reschedule.rappid
            })
        
        # Get current date for the page
        current_date = datetime.now().strftime("%A, %B %d, %Y")
        today_date = datetime.now().strftime("%Y-%m-%d")
        
        # Render the template with the data
        return render_template('appointments/rescheduled_appointments.html', 
                                rescheduled_appointments=formatted_rescheduled,
                                current_date=current_date,
                                today_date=today_date)
    except Exception as e:
        print(f"Error in rescheduled_appointments route: {e}")
        return f"Error loading rescheduled appointments: {e}", 500

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

#_______________________________________________________________________
#Staff Management Routes
@app.route('/staff')
def staff():
    """Staff management page"""
    try:
        # Get all staff members (users with admin or user access)
        staff_users = User.query.filter(User.usersaccess.in_(['admin', 'user'])).all()
        
        # Format staff data for the template
        staff_members = []
        for user in staff_users:
            # Determine role based on some attribute or default to "Staff"
            # You might want to add a dedicated role field to your User model
            role = "Staff"  # Default
            if hasattr(user, 'usersrole') and user.usersrole:
                role = user.usersrole
            
            staff_members.append({
                'id': f"STF-{user.usersid:03d}",
                'raw_id': user.usersid,
                'name': user.usersrealname,
                'email': user.usersemail,
                'contact': user.userscontact,
                'role': role,  # Keep this for filtering functionality
                'occupation': user.usersoccupation if hasattr(user, 'usersoccupation') and user.usersoccupation else "Staff",
                'access_level': user.usersaccess.capitalize(),
                'join_date': user.userscreatedat if hasattr(user, 'userscreatedat') else datetime.now(),
                'appointment_count': 0,
                'patient_count': 0,
            })

        
        return render_template('staff.html', 
                              staff_members=staff_members,
                              current_date=datetime.now().strftime('%B %d, %Y'))
    
    except Exception as e:
        print(f"Error loading staff page: {e}")
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
            usersaccess=request.form.get('access'),
            # Store in occupation field
            usersoccupation=request.form.get('occupation')
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
        
        # Log the action
        log_user_action(
            session.get('user_id'),
            'Create Staff',
            f'Added new staff member: {new_staff.usersrealname} ({new_staff.usersusername})'
        )
        
        # Return success response
        return jsonify({
            "success": True,
            "staff": {
                "id": f"STF-{new_staff.usersid:03d}",
                "name": new_staff.usersrealname,
                "role": request.form.get('role', 'Staff'),
                "access_level": new_staff.usersaccess.capitalize(),
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
        if session.get('user_id') == staff_id:
            return jsonify({"success": False, "error": "Cannot delete your own account"})
        
        # Log the action before deleting
        log_user_action(
            session.get('user_id'),
            'Delete Staff',
            f'Deleted staff member: {staff.usersrealname} ({staff.usersusername})'
        )
        
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
        
        # Check if JSON format is requested (for AJAX)
        if request.args.get('format') == 'json':
            # For API requests, return JSON data
            staff_data = {
                'usersid': staff.usersid,
                'usersusername': staff.usersusername,
                'usersrealname': staff.usersrealname,
                'usersemail': staff.usersemail,
                'userscontact': staff.userscontact,
                'usershomeaddress': staff.usershomeaddress,
                'userscityzipcode': staff.userscityzipcode,
                'usersreligion': staff.usersreligion,
                'usersgender': staff.usersgender,
                'usersaccess': staff.usersaccess,
                'usersoccupation': staff.usersoccupation if hasattr(staff, 'usersoccupation') else 'Staff'
            }
            
            # Add date of birth if available
            if hasattr(staff, 'usersdob') and staff.usersdob:
                staff_data['usersdob_formatted'] = staff.usersdob.strftime('%Y-%m-%d')
            
            # Add age if available
            if hasattr(staff, 'usersage') and staff.usersage:
                staff_data['usersage'] = staff.usersage
                
            return jsonify(staff_data)
        
        # Get current date for the page
        current_date = datetime.now().strftime("%B %d, %Y")
        
        # For browser requests, render HTML template
        return render_template('staff_details.html', 
                              staff=staff,
                              current_date=current_date)
    except Exception as e:
        print(f"Error in staff_details route: {e}")
        return jsonify({"success": False, "error": str(e)}) if request.args.get('format') == 'json' else f"Error loading staff details: {e}", 500
    
@app.route('/edit_staff/<int:staff_id>')
def edit_staff(staff_id):
    """Render edit staff page"""
    try:
        staff = User.query.get_or_404(staff_id)
        
        # Format date of birth for HTML date input
        if hasattr(staff, 'usersdob') and staff.usersdob:
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
        
        # Store old values for logging
        old_name = staff.usersrealname
        
        # Update staff information from form
        staff.usersrealname = request.form.get('name')
        staff.usersemail = request.form.get('email')
        staff.userscontact = request.form.get('contact')
        staff.usershomeaddress = request.form.get('address')
        staff.userscityzipcode = request.form.get('cityzipcode')
        staff.usersreligion = request.form.get('religion')
        staff.usersgender = request.form.get('gender')
        staff.usersaccess = request.form.get('access')

        
        # Update occupation field
        staff.usersoccupation = request.form.get('occupation')
        
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
        
        # Log the action
        log_user_action(
            session.get('user_id'),
            'Update Staff',
            f'Updated staff member: {old_name} -> {staff.usersrealname} ({staff.usersusername})'
        )
        
        # Return success response for AJAX request
        return jsonify({'success': True})
    
    except Exception as e:
        # Return error response for AJAX request
        db.session.rollback()
        print(f"Error in update_staff route: {e}")
        return jsonify({'success': False, 'error': str(e)})
            
# Add these inventory routes to app.py, after the existing routes
#Inventory Management Routes
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
        
        # Log the action
        log_user_action(
            session.get('user_id'),
            'Create Inventory',
            f'Added new inventory item: {new_item.invname} (Quantity: {new_item.invquantity})'
        )
        
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
        
        # Store old values for logging
        old_name = item.invname
        old_quantity = item.invquantity
        
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
        
        # Log the action
        log_user_action(
            session.get('user_id'),
            'Update Inventory',
            f'Updated inventory item: {old_name} -> {item.invname} (Quantity: {old_quantity} -> {item.invquantity})'
        )
        
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
        
        # Log the action before deleting
        log_user_action(
            session.get('user_id'),
            'Delete Inventory',
            f'Deleted inventory item: {item.invname} (Quantity: {item.invquantity})'
        )
        
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
    
#_____________________________
# User Registration
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
        
        # Log the registration
        log_user_action(
            new_user.usersid,
            'User Registration',
            f'New user registered: {realname} ({username})'
        )
        
        # Redirect to login page with success message
        return redirect(url_for('login', registration_success=True))
    
    except Exception as e:
        # If any error occurs, rollback the session
        db.session.rollback()
        print(f"Error in register_process route: {e}")
        return render_template('register.html', error=f"Registration failed: {str(e)}")

# Add this to app.py - Configuration for backup directory
BACKUP_DIRECTORY = 'database_backups'
# Create the backup directory if it doesn't exist
if not os.path.exists(BACKUP_DIRECTORY):
    os.makedirs(BACKUP_DIRECTORY)

@app.route('/backup_restore')
def backup_restore():
    """Render the backup and restore page"""
    # Get list of existing backups
    backups = []
    try:
        if os.path.exists(BACKUP_DIRECTORY):
            backup_files = [f for f in os.listdir(BACKUP_DIRECTORY) if f.endswith('.sql')]
            for backup_file in backup_files:
                # Extract the timestamp from the filename
                timestamp_str = backup_file.split('_')[1].split('.')[0]
                backup_time = datetime.strptime(timestamp_str, '%Y%m%d%H%M%S')
                
                # Get file size in MB
                file_path = os.path.join(BACKUP_DIRECTORY, backup_file)
                file_size = os.path.getsize(file_path) / (1024 * 1024)  # Convert bytes to MB
                
                backups.append({
                    'filename': backup_file,
                    'timestamp': backup_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'size': f"{file_size:.2f} MB"
                })
                
            # Sort backups by timestamp (newest first)
            backups.sort(key=lambda x: x['timestamp'], reverse=True)
    except Exception as e:
        print(f"Error listing backups: {e}")
    
    # Get current date for the page
    current_date = datetime.now().strftime("%A, %B %d, %Y")
    
    return render_template('backup_restore.html', 
                          backups=backups,
                          current_date=current_date)

@app.route('/create_backup', methods=['POST'])
def create_backup():
    """Create a backup of the database with DNS resolution fix"""
    try:
        # Check if the user has admin access
        if session.get('access_level') != 'admin':
            return jsonify({"success": False, "error": "You don't have permission to perform this action"})
        
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        backup_filename = f"backup_{timestamp}.sql"
        backup_path = os.path.join(BACKUP_DIRECTORY, backup_filename)
        
        # Get database credentials from app config
        db_uri = app.config['SQLALCHEMY_DATABASE_URI']
        
        # Parse the database URI more carefully
        if 'mysql+pymysql://' in db_uri:
            parts = db_uri.replace('mysql+pymysql://', '').split('@')
        else:
            parts = db_uri.replace('mysql://', '').split('@')
            
        user_pass = parts[0].split(':')
        host_db = parts[1].split('/')
        
        username = user_pass[0]
        password = user_pass[1]
        original_host = host_db[0].split(':')[0]  # Remove port if present
        port = int(host_db[0].split(':')[1]) if ':' in host_db[0] else 3306
        database = host_db[1]
        
        # Resolve host DNS issues
        resolved_host = resolve_host(original_host)
        print(f"Original host: {original_host}, Resolved host: {resolved_host}")
        
        # Test the connection first with resolved host
        try:
            connection = pymysql.connect(
                host=resolved_host,
                user=username,
                password=password,
                database=database,
                port=port,
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor,
                connect_timeout=10
            )
            connection.close()
            print("Database connection successful for backup")
        except Exception as e:
            return jsonify({
                "success": False, 
                "error": f"Cannot connect to MySQL server: {str(e)}. Please check that your MySQL server is running and your connection details are correct."
            })
            
        # Now proceed with the backup using the resolved host
        try:
            create_direct_backup(username, password, resolved_host, database, backup_path, port)
            
            # Get backup file size
            file_size = os.path.getsize(backup_path) / (1024 * 1024)  # Convert bytes to MB
            
            # Log the backup action
            log_user_action(
                session.get('user_id'),
                'Database Backup',
                f'Created database backup: {backup_filename} ({file_size:.2f} MB)'
            )
            
            return jsonify({
                "success": True, 
                "message": "Backup created successfully",
                "backup": {
                    "filename": backup_filename,
                    "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    "size": f"{file_size:.2f} MB"
                }
            })
        except Exception as e:
            return jsonify({
                "success": False, 
                "error": f"Error creating backup: {str(e)}"
            })
            
    except Exception as e:
        print(f"Error in create_backup route: {e}")
        return jsonify({
            "success": False, 
            "error": f"Error processing backup request: {str(e)}"
        })

def create_direct_backup(username, password, host, database_name, backup_path, port=3306):
    """Create a database backup directly using PyMySQL without external tools - with DNS fix"""
    connection = None
    try:
        # Connect to the database with improved error handling and resolved host
        try:
            connection = pymysql.connect(
                host=host,
                user=username,
                password=password,
                database=database_name,
                port=port,
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor,
                connect_timeout=10
            )
            print(f"Successfully connected to MySQL at {host}:{port}")
        except pymysql.err.OperationalError as e:
            if e.args[0] == 2003:  # Connection refused error
                raise Exception(f"Cannot connect to MySQL server at {host}:{port}. Is MySQL running? Error: {e}")
            elif e.args[0] == 1045:  # Access denied error
                raise Exception(f"Access denied. Please check your username and password. Error: {e}")
            else:
                raise Exception(f"Database connection failed: {e}")
        
        with open(backup_path, 'w', encoding='utf8') as f:
            # Write backup header
            f.write(f"-- Database Backup for: {database_name}\n")
            f.write(f"-- Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("-- By: Pullan Dental Clinic Management System\n\n")
            
            f.write("SET FOREIGN_KEY_CHECKS=0;\n\n")
            
            # Add DROP DATABASE and CREATE DATABASE statements
            f.write(f"DROP DATABASE IF EXISTS `{database_name}`;\n")
            f.write(f"CREATE DATABASE `{database_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;\n")
            f.write(f"USE `{database_name}`;\n\n")
            
            # Get all tables
            with connection.cursor() as cursor:
                cursor.execute("SHOW TABLES")
                tables = cursor.fetchall()
                
                if not tables:
                    f.write("-- No tables found in database\n")
                
                # For each table, get CREATE TABLE statement and data
                for table in tables:
                    table_name = list(table.values())[0]
                    
                    # Get the CREATE TABLE statement
                    cursor.execute(f"SHOW CREATE TABLE `{table_name}`")
                    create_table = cursor.fetchone()
                    create_table_sql = list(create_table.values())[1]
                    
                    # Write the DROP TABLE and CREATE TABLE statements
                    f.write(f"DROP TABLE IF EXISTS `{table_name}`;\n")
                    f.write(f"{create_table_sql};\n\n")
                    
                    # Get table data
                    cursor.execute(f"SELECT * FROM `{table_name}`")
                    rows = cursor.fetchall()
                    
                    if rows:
                        # Get column names
                        columns = list(rows[0].keys())
                        
                        # Write INSERT statements in batches
                        batch_size = 100
                        for i in range(0, len(rows), batch_size):
                            batch = rows[i:i+batch_size]
                            
                            # Generate INSERT statement header
                            insert_header = f"INSERT INTO `{table_name}` (`{'`, `'.join(columns)}`) VALUES\n"
                            f.write(insert_header)
                            
                            # Generate values for each row
                            values_list = []
                            for row in batch:
                                values = []
                                for column in columns:
                                    value = row[column]
                                    if value is None:
                                        values.append("NULL")
                                    elif isinstance(value, (int, float)):
                                        values.append(str(value))
                                    elif isinstance(value, (datetime, date)):
                                        values.append(f"'{value.strftime('%Y-%m-%d %H:%M:%S')}'")
                                    else:
                                        # Escape string values
                                        escaped_value = str(value).replace("'", "''")
                                        values.append(f"'{escaped_value}'")
                                            
                                values_list.append(f"({', '.join(values)})")
                            
                            # Write values with commas and semicolon
                            f.write(',\n'.join(values_list))
                            f.write(';\n\n')
            
            f.write("SET FOREIGN_KEY_CHECKS=1;\n")
            
        print(f"Database backup completed successfully: {backup_path}")
        
    except Exception as e:
        raise Exception(f"Direct database backup failed: {str(e)}")
    finally:
        # Make sure to close the connection even if an error occurs
        if connection:
            connection.close()

@app.route('/restore_backup/<filename>', methods=['POST'])
def restore_backup(filename):
    """Restore the database from a backup file with DNS resolution fix"""
    try:
        # Check if the user has admin access
        if session.get('access_level') != 'admin':
            return jsonify({"success": False, "error": "You don't have permission to perform this action"})
            
        backup_path = os.path.join(BACKUP_DIRECTORY, filename)
        
        if not os.path.exists(backup_path):
            return jsonify({"success": False, "error": "Backup file not found"})
            
        # Get database credentials from app config with DNS resolution
        db_uri = app.config['SQLALCHEMY_DATABASE_URI']
        
        if 'mysql+pymysql://' in db_uri:
            parts = db_uri.replace('mysql+pymysql://', '').split('@')
        else:
            parts = db_uri.replace('mysql://', '').split('@')
            
        user_pass = parts[0].split(':')
        host_db = parts[1].split('/')
        
        username = user_pass[0]
        password = user_pass[1]
        original_host = host_db[0].split(':')[0]
        port = int(host_db[0].split(':')[1]) if ':' in host_db[0] else 3306
        
        # Resolve DNS issues
        resolved_host = resolve_host(original_host)

        # Try using mysql client external command first
        try:
            # Determine the correct path to mysql client based on the OS
            if os.name == 'nt':  # Windows
                # Try common MySQL installation paths on Windows
                possible_paths = [
                    r'C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe',
                    r'C:\Program Files\MySQL\MySQL Server 5.7\bin\mysql.exe',
                    r'C:\xampp\mysql\bin\mysql.exe',
                    r'C:\wamp64\bin\mysql\mysql8.0.31\bin\mysql.exe',
                    r'C:\wamp64\bin\mysql\mysql5.7.36\bin\mysql.exe',
                    r'C:\laragon\bin\mysql\mysql-8.0.30-winx64\bin\mysql.exe'
                ]
                
                mysql_path = 'mysql'  # Default fallback
                for path in possible_paths:
                    if os.path.exists(path):
                        mysql_path = path
                        break
            else:
                # On Unix-like systems, assume mysql is in PATH
                mysql_path = 'mysql'
            
            # Restore the backup using mysql client with resolved host
            cmd = [
                mysql_path,
                f'--user={username}',
                f'--password={password}',
                f'--host={resolved_host}',
                f'--port={port}'
            ]
            
            with open(backup_path, 'r') as backup_file:
                process = subprocess.Popen(
                    cmd,
                    stdin=backup_file,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                stdout, stderr = process.communicate()
                
            if process.returncode != 0:
                raise Exception(f"mysql restore failed: {stderr.decode('utf-8')}")
                
        except Exception as e:
            print(f"External mysql restore failed: {e}")
            print("Falling back to direct database restore method...")
            
            # Fallback to direct database connection and script execution
            restore_direct_backup(username, password, resolved_host, backup_path, port)
        
        # Log the restore action
        log_user_action(
            session.get('user_id'),
            'Database Restore',
            f'Restored database from backup: {filename}'
        )
            
        return jsonify({
            "success": True,
            "message": "Database restored successfully from backup"
        })
    except Exception as e:
        print(f"Error restoring backup: {e}")
        return jsonify({"success": False, "error": str(e)})

def restore_direct_backup(username, password, host, backup_path, port=3306):
    """Restore a database backup directly using PyMySQL without external tools - with DNS fix"""
    try:
        # Read the backup file
        with open(backup_path, 'r', encoding='utf8') as f:
            backup_content = f.read()
        
        # Extract the database name from the backup content
        database_pattern = re.search(r'CREATE DATABASE `([^`]+)`', backup_content)
        if not database_pattern:
            raise Exception("Could not find database name in backup file")
            
        database_name = database_pattern.group(1)
        
        # Connect to MySQL server (without specifying database) with resolved host
        connection = pymysql.connect(
            host=host,
            user=username,
            password=password,
            port=port,
            charset='utf8mb4',
            connect_timeout=10
        )
        
        # Split the backup file into individual SQL statements
        statements = re.split(r';\s*\n', backup_content)
        
        with connection.cursor() as cursor:
            for statement in statements:
                statement = statement.strip()
                if statement:
                    try:
                        cursor.execute(statement)
                    except Exception as e:
                        print(f"Warning: Error executing statement: {e}")
                        print(f"Statement: {statement[:100]}...")
                        # Continue with next statement instead of failing completely
                        continue
            
            connection.commit()
            
        connection.close()
        print(f"Database restore completed successfully from: {backup_path}")
        
    except Exception as e:
        raise Exception(f"Direct database restore failed: {str(e)}")

@app.route('/download_backup/<filename>')
def download_backup(filename):
    """Download a backup file"""
    try:
        backup_path = os.path.join(BACKUP_DIRECTORY, filename)
        
        if not os.path.exists(backup_path):
            return "Backup file not found", 404
        
        # Log the download action
        log_user_action(
            session.get('user_id'),
            'Download Backup',
            f'Downloaded backup file: {filename}'
        )
            
        return send_file(
            backup_path,
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        print(f"Error downloading backup: {e}")
        return f"Error downloading backup: {e}", 500

@app.route('/delete_backup/<filename>', methods=['POST'])
def delete_backup(filename):
    """Delete a backup file"""
    try:
        # Check if the user has admin access
        if session.get('access_level') != 'admin':
            return jsonify({"success": False, "error": "You don't have permission to perform this action"})
            
        backup_path = os.path.join(BACKUP_DIRECTORY, filename)
        
        if not os.path.exists(backup_path):
            return jsonify({"success": False, "error": "Backup file not found"})
            
        os.remove(backup_path)
        
        # Log the deletion action
        log_user_action(
            session.get('user_id'),
            'Delete Backup',
            f'Deleted backup file: {filename}'
        )
        
        return jsonify({
            "success": True,
            "message": "Backup deleted successfully"
        })
    except Exception as e:
        print(f"Error deleting backup: {e}")
        return jsonify({"success": False, "error": str(e)})

if __name__ == '__main__':
    app.run(debug=True)