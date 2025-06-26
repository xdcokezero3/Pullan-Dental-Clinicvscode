# app.py - Fixed version with DNS resolution handling + User Logs System + Hardcoded Admin + Enhanced Dental Charts
from flask import Flask, render_template, request, jsonify, redirect, url_for, send_file, session, make_response
from db_connector import app as db_app, db, Patient, Appointment, DentalChart, Inventory, RescheduleAppointment, Report, User, UserLog, Teeth, log_user_action
from datetime import datetime, date, timedelta
import os
import time
from sqlalchemy import text
import subprocess
import json
import pymysql
import re
import socket
import csv
from io import StringIO
from functools import wraps
import traceback

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

        # Check for hardcoded admin account FIRST
        if username == 'admin' and password == 'admin':
            # Set up session for hardcoded admin
            session['user_id'] = 0  # Special ID for hardcoded admin
            session['username'] = 'admin'
            session['access_level'] = 'admin'
            session['real_name'] = 'System Administrator'
            
            # Log the login action (use user_id = 0 for hardcoded admin)
            log_user_action(0, 'Login', 'Hardcoded admin logged in successfully')
            
            return redirect(url_for('dashboard'))

        # Check credentials against database (existing code)
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

# Replace the existing dashboard route in your app.py with this updated version

@app.route('/dashboard')
def dashboard():
    """Dashboard with real data from database"""
    try:
        # Get current date
        today = datetime.now().date()
        current_month_start = today.replace(day=1)
        last_month_start = (current_month_start - timedelta(days=1)).replace(day=1)
        last_month_end = current_month_start - timedelta(days=1)
        
        # Calculate yesterday for comparisons
        yesterday = today - timedelta(days=1)
        week_start = today - timedelta(days=today.weekday())  # Monday of current week
        last_week_start = week_start - timedelta(weeks=1)
        last_week_end = week_start - timedelta(days=1)
        
        # 1. PATIENT STATISTICS
        total_patients = Patient.query.filter_by(is_deleted=False).count()
        last_month_patients = Patient.query.filter_by(is_deleted=False).count()  # You might want to add created_date field
        
        # Calculate patient growth (mock calculation since we don't have creation dates)
        patient_growth = 12  # Default positive growth
        
        # 2. TODAY'S APPOINTMENTS
        todays_appointments = Appointment.query.filter_by(appdate=today).all()
        todays_appointment_count = len(todays_appointments)
        
        # Yesterday's appointments for comparison
        yesterday_appointments = Appointment.query.filter_by(appdate=yesterday).count()
        appointment_growth = 0
        if yesterday_appointments > 0:
            appointment_growth = ((todays_appointment_count - yesterday_appointments) / yesterday_appointments) * 100
        elif todays_appointment_count > 0:
            appointment_growth = 100
        
        # 3. TODAY'S REVENUE (calculated from procedures)
        todays_procedures = Report.query.filter_by(repdate=today).all()
        todays_revenue = 0
        
        # Calculate revenue based on procedures (you can adjust these rates)
        procedure_rates = {
            'cleaning': 80,
            'extraction': 150,
            'root_canal': 300,
            'braces': 2000,
            'dentures': 800
        }
        
        for procedure in todays_procedures:
            if procedure.repcleaning: todays_revenue += procedure_rates['cleaning']
            if procedure.repextraction: todays_revenue += procedure_rates['extraction']
            if procedure.reprootcanal: todays_revenue += procedure_rates['root_canal']
            if procedure.repbraces: todays_revenue += procedure_rates['braces']
            if procedure.repdentures: todays_revenue += procedure_rates['dentures']
        
        # Yesterday's revenue for comparison
        yesterday_procedures = Report.query.filter_by(repdate=yesterday).all()
        yesterday_revenue = 0
        for procedure in yesterday_procedures:
            if procedure.repcleaning: yesterday_revenue += procedure_rates['cleaning']
            if procedure.repextraction: yesterday_revenue += procedure_rates['extraction']
            if procedure.reprootcanal: yesterday_revenue += procedure_rates['root_canal']
            if procedure.repbraces: yesterday_revenue += procedure_rates['braces']
            if procedure.repdentures: yesterday_revenue += procedure_rates['dentures']
        
        revenue_growth = 0
        if yesterday_revenue > 0:
            revenue_growth = ((todays_revenue - yesterday_revenue) / yesterday_revenue) * 100
        elif todays_revenue > 0:
            revenue_growth = 100
        
        # 4. THIS WEEK'S TREATMENTS
        this_week_treatments = Report.query.filter(
            Report.repdate >= week_start,
            Report.repdate <= today
        ).count()
        
        last_week_treatments = Report.query.filter(
            Report.repdate >= last_week_start,
            Report.repdate <= last_week_end
        ).count()
        
        treatment_growth = 0
        if last_week_treatments > 0:
            treatment_growth = ((this_week_treatments - last_week_treatments) / last_week_treatments) * 100
        elif this_week_treatments > 0:
            treatment_growth = 100
        
        # 5. FORMAT TODAY'S APPOINTMENTS FOR TABLE
        formatted_appointments = []
        for appointment in todays_appointments:
            # Get patient details
            patient = Patient.query.filter_by(patname=appointment.apppatient).first()
            patient_id = f"PAT-{patient.patId:03d}" if patient else "N/A"
            
            # Determine status based on time (this is a simple logic, you can enhance it)
            appointment_time = appointment.apptime
            current_time = datetime.now().time()
            
            if appointment_time:
                # Convert time string to time object for comparison
                try:
                    apt_time_obj = datetime.strptime(appointment_time, '%H:%M').time()
                    if apt_time_obj < current_time:
                        status = 'completed'
                    else:
                        status = 'pending'
                except:
                    status = 'pending'
            else:
                status = 'pending'
            
            formatted_appointments.append({
                'id': f"APT-{appointment.appid:03d}",
                'patient_name': appointment.apppatient,
                'patient_id': patient_id,
                'time': appointment.apptime or "N/A",
                'treatment': "General Checkup",  # Default since not in schema
                'doctor': "Dr. Andrews",  # Default since not in schema
                'status': status,
                'raw_id': appointment.appid,
                'patient_phone': patient.patcontact if patient else "N/A"
            })
        
        # Sort appointments by time
        formatted_appointments.sort(key=lambda x: x['time'] if x['time'] != "N/A" else "00:00")
        
        # 6. RECENT PATIENTS (last 3 patients who had procedures)
        recent_procedures = Report.query.order_by(Report.repdate.desc()).limit(3).all()
        recent_patients = []
        
        for procedure in recent_procedures:
            patient = Patient.query.filter_by(patname=procedure.reppatient).first()
            if patient:
                # Build procedure list
                procedures_done = []
                if procedure.repcleaning: procedures_done.append("Cleaning")
                if procedure.repextraction: procedures_done.append("Extraction")
                if procedure.reprootcanal: procedures_done.append("Root Canal")
                if procedure.repbraces: procedures_done.append("Braces")
                if procedure.repdentures: procedures_done.append("Dentures")
                if procedure.repothers: procedures_done.append(procedure.repothers)
                
                recent_patients.append({
                    'id': f"PAT-{patient.patId:03d}",
                    'name': patient.patname,
                    'last_visit': procedure.repdate.strftime('%b %d, %Y') if procedure.repdate else "N/A",
                    'treatment': ", ".join(procedures_done) if procedures_done else "General Visit",
                    'raw_id': patient.patId
                })
        
        # 7. UPCOMING EVENTS (you can customize this based on your needs)
        upcoming_events = [
            {
                'title': 'Staff Meeting',
                'date': (today + timedelta(days=1)).strftime('%b %d'),
                'time': '9:00 AM',
                'type': 'staff-meeting'
            },
            {
                'title': 'Inventory Check',
                'date': (today + timedelta(days=3)).strftime('%b %d'),
                'time': '2:00 PM',
                'type': 'inventory'
            },
            {
                'title': 'Equipment Maintenance',
                'date': (today + timedelta(days=5)).strftime('%b %d'),
                'time': '10:00 AM',
                'type': 'training'
            }
        ]
        
        # 8. INVENTORY ALERTS
        low_stock_items = Inventory.query.filter(Inventory.invquantity < 5).count()
        expired_items = Inventory.query.filter(
            Inventory.invdoe.isnot(None),
            Inventory.invdoe < today
        ).count()
        
        # Prepare all data for template
        dashboard_data = {
            'stats': {
                'total_patients': total_patients,
                'patient_growth': patient_growth,
                'todays_appointments': todays_appointment_count,
                'appointment_growth': appointment_growth,
                'todays_revenue': todays_revenue,
                'revenue_growth': revenue_growth,
                'this_week_treatments': this_week_treatments,
                'treatment_growth': treatment_growth
            },
            'appointments': formatted_appointments,
            'recent_patients': recent_patients,
            'upcoming_events': upcoming_events,
            'alerts': {
                'low_stock': low_stock_items,
                'expired_items': expired_items
            },
            'current_date': datetime.now().strftime("%A, %B %d, %Y")
        }
        
        return render_template('dashboard.html', **dashboard_data)
        
    except Exception as e:
        print(f"Error in dashboard route: {e}")
        # Return basic template with proper error handling and correct structure
        return render_template('dashboard.html', 
                             stats={
                                 'total_patients': 0, 
                                 'patient_growth': 0,
                                 'todays_appointments': 0, 
                                 'appointment_growth': 0,
                                 'todays_revenue': 0,
                                 'revenue_growth': 0,
                                 'this_week_treatments': 0,
                                 'treatment_growth': 0
                             },
                             appointments=[], 
                             recent_patients=[], 
                             upcoming_events=[],
                             alerts={'low_stock': 0, 'expired_items': 0},
                             current_date=datetime.now().strftime("%A, %B %d, %Y"),
                             error=f"Dashboard error: {e}")

@app.route('/logout')
def logout():
    """Log out the current user"""
    user_id = session.get('user_id')
    username = session.get('username')
    
    if user_id is not None:  # Changed from 'if user_id:' to handle user_id = 0
        # Log the logout action
        if user_id == 0:
            log_user_action(0, 'Logout', 'Hardcoded admin logged out')
        else:
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
            # Handle hardcoded admin (user_id = 0)
            if log.user_id == 0:
                user_name = "System Administrator"
                username = "admin"
            else:
                user_name = log.user_name
                username = log.username
            
            formatted_logs.append({
                'log_id': log.log_id,
                'user_id': log.user_id,
                'user_name': user_name,
                'username': username,
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
            # Handle hardcoded admin (user_id = 0)
            if log.user_id == 0:
                user_name = "System Administrator"
                username = "admin"
            else:
                user_name = log.user_name or 'N/A'
                username = log.username or 'N/A'
            
            writer.writerow([
                log.log_id,
                log.user_id or 'N/A',
                user_name,
                username,
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
        # Get status filter from query parameter (default to 'active')
        status_filter = request.args.get('status', 'active')
        
        # Build query based on status filter
        if status_filter == 'active':
            patients_list = Patient.query.filter_by(is_deleted=False).all()
        elif status_filter == 'inactive':
            patients_list = Patient.query.filter_by(is_deleted=True).all()
        else:  # 'all'
            patients_list = Patient.query.all()
        
        print(f"Found {len(patients_list)} patients with status: {status_filter}")
        
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
                'status': 'Inactive' if patient.is_deleted else 'Active',
                'is_active': not patient.is_deleted,
                'raw_id': patient.patId  # Add the raw ID for use in URLs
            })
        
        # Get current date for the page
        current_date = datetime.now().strftime("%A, %B %d, %Y")
        
        # Get counts for status badges
        active_count = Patient.query.filter_by(is_deleted=False).count()
        inactive_count = Patient.query.filter_by(is_deleted=True).count()
        total_count = active_count + inactive_count
        
        # Render the template with the data
        return render_template('patients/patients.html', 
                              patients=formatted_patients, 
                              current_date=current_date,
                              status_filter=status_filter,
                              active_count=active_count,
                              inactive_count=inactive_count,
                              total_count=total_count)
    except Exception as e:
        print(f"Error in patients route: {e}")
        return f"Error loading patients: {e}", 500

@app.route('/patient/<int:patient_id>')
def patient_details(patient_id):
    """View details of a specific patient with real database data"""
    try:
        patient = Patient.query.get_or_404(patient_id)
        
        # Format the patient ID with leading zeros
        formatted_patient_id = f"PAT-{patient.patId:03d}"
        
        # Get real appointments for this patient
        real_appointments = Appointment.query.filter_by(apppatient=patient.patname).order_by(Appointment.appdate.desc()).all()
        
        # Format appointments for display
        formatted_appointments = []
        for appointment in real_appointments:
            # Determine status based on date (you can modify this logic)
            appointment_date = appointment.appdate
            current_date = datetime.now().date()
            
            if appointment_date < current_date:
                status = 'completed'
            elif appointment_date == current_date:
                status = 'today'
            else:
                status = 'upcoming'
            
            formatted_appointments.append({
                'id': f"APT-{appointment.appid:03d}",
                'date': appointment.appdate.strftime('%B %d, %Y') if appointment.appdate else "N/A",
                'time': appointment.apptime or "N/A",
                'treatment': "General Checkup",  # Default since not in your schema
                'doctor': "Dr. Andrews",  # Default since not in your schema
                'status': status,
                'raw_id': appointment.appid
            })
        
        # Check if patient has dental chart
        dental_chart = DentalChart.query.filter_by(dcpatname=patient.patname, is_deleted=False).first()
        has_dental_chart = dental_chart is not None
        
        # Get teeth chart data if it exists
        teeth_chart = Teeth.query.filter_by(tpatname=patient.patname, is_deleted=False).first()
        teeth_data = []
        
        if teeth_chart:
            for i in range(1, 33):  # Teeth 1-32
                tooth_condition = getattr(teeth_chart, f'l{i}', 'healthy')
                teeth_data.append({
                    'number': i,
                    'condition': tooth_condition or 'healthy'
                })
        
        # Get recent procedures for this patient
        recent_procedures = Report.query.filter_by(reppatient=patient.patname).order_by(Report.repdate.desc()).limit(5).all()
        
        # Format procedures for display
        formatted_procedures = []
        for proc in recent_procedures:
            # Build procedure list
            procedures_done = []
            if proc.repcleaning: procedures_done.append("Cleaning")
            if proc.repextraction: procedures_done.append("Extraction")
            if proc.reprootcanal: procedures_done.append("Root Canal")
            if proc.repbraces: procedures_done.append("Braces")
            if proc.repdentures: procedures_done.append("Dentures")
            if proc.repothers: procedures_done.append(proc.repothers)
            
            formatted_procedures.append({
                'id': f"PROC-{proc.repid:03d}",
                'date': proc.repdate.strftime('%B %d, %Y') if proc.repdate else "N/A",
                'procedures': ", ".join(procedures_done) if procedures_done else "General Visit",
                'dentist': proc.repdentist or "Dr. Andrews",
                'prescription': proc.repprescription or "None",
                'status': 'completed',  # All procedures in history are completed
                'raw_id': proc.repid
            })
        
        return render_template('patients/patient_details.html', 
                              patient=patient, 
                              formatted_patient_id=formatted_patient_id,
                              appointments=formatted_appointments,
                              has_dental_chart=has_dental_chart,
                              teeth_data=teeth_data,
                              recent_procedures=formatted_procedures)
                              
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
    """Deactivate a patient (soft delete) - maintained for backward compatibility"""
    try:
        patient = Patient.query.get_or_404(patient_id)
        patient.is_deleted = True
        
        db.session.commit()
        
        # Log the action
        log_user_action(
            session.get('user_id'),
            'Deactivate Patient',
            f'Deactivated patient: {patient.patname} (ID: PAT-{patient.patId:03d})'
        )
        
        return jsonify({"success": True, "message": "Patient deactivated successfully"})
    except Exception as e:
        db.session.rollback()
        print(f"Error in delete_patient route: {e}")
        return jsonify({"success": False, "error": str(e)})
    
@app.route('/deactivate_patient/<int:patient_id>', methods=['POST'])
def deactivate_patient(patient_id):
    """Deactivate a patient (soft delete)"""
    try:
        patient = Patient.query.get_or_404(patient_id)
        patient.is_deleted = True
        
        db.session.commit()
        
        # Log the action
        log_user_action(
            session.get('user_id'),
            'Deactivate Patient',
            f'Deactivated patient: {patient.patname} (ID: PAT-{patient.patId:03d})'
        )
        
        return jsonify({"success": True, "message": "Patient deactivated successfully"})
    except Exception as e:
        db.session.rollback()
        print(f"Error in deactivate_patient route: {e}")
        return jsonify({"success": False, "error": str(e)})

@app.route('/reactivate_appointment/<int:appointment_id>', methods=['POST'])
def reactivate_appointment(appointment_id):
    """Reactivate a cancelled appointment"""
    try:
        appointment = Appointment.query.get_or_404(appointment_id)
        
        # Set status back to active
        if hasattr(appointment, 'status'):
            appointment.status = 'active'
        
        db.session.commit()
        
        # Log the action
        log_user_action(
            session.get('user_id'),
            'Reactivate Appointment',
            f'Reactivated appointment for {appointment.apppatient} on {appointment.appdate} at {appointment.apptime}'
        )
        
        return jsonify({"success": True, "message": "Appointment reactivated successfully"})
    except Exception as e:
        db.session.rollback()
        print(f"Error in reactivate_appointment route: {e}")
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
    """Render the appointments page with status filtering"""
    try:
        # Get status filter from query parameter (default to 'all')
        status_filter = request.args.get('status', 'all')
        
        # Build query based on status filter
        if status_filter == 'active':
            appointments_list = Appointment.query.filter_by(status='active').order_by(Appointment.appdate.desc()).all()
        elif status_filter == 'completed':
            appointments_list = Appointment.query.filter_by(status='completed').order_by(Appointment.appdate.desc()).all()
        elif status_filter == 'cancelled':
            appointments_list = Appointment.query.filter_by(status='cancelled').order_by(Appointment.appdate.desc()).all()
        else:  # 'all'
            appointments_list = Appointment.query.order_by(Appointment.appdate.desc()).all()
        
        # Get only ACTIVE patients for the "Add Appointment" form
        all_patients = Patient.query.filter_by(is_deleted=False).all()
        
        # Format the appointments for display
        formatted_appointments = []
        for appointment in appointments_list:
            # Determine status display and styling
            status = getattr(appointment, 'status', 'active')  # Default to active if no status field
            
            # Auto-determine status if not set based on date
            if not hasattr(appointment, 'status') or not appointment.status:
                current_date = datetime.now().date()
                if appointment.appdate < current_date:
                    status = 'completed'
                elif appointment.appdate == current_date:
                    status = 'active'
                else:
                    status = 'active'
            
            # Format appointment data
            formatted_appointments.append({
                'id': f"APT-{appointment.appid:03d}",
                'patient_name': appointment.apppatient,
                'doctor_name': "Dr. Andrews",
                'treatment': "General Checkup",
                'date': appointment.appdate.strftime('%B %d, %Y') if appointment.appdate else "N/A",
                'time': appointment.apptime,
                'duration': "30 min",
                'status': status,
                'status_class': f"status-{status}",
                'raw_id': appointment.appid
            })
        
        # Get counts for status badges
        active_count = Appointment.query.filter_by(status='active').count() if hasattr(Appointment, 'status') else 0
        completed_count = Appointment.query.filter_by(status='completed').count() if hasattr(Appointment, 'status') else 0
        cancelled_count = Appointment.query.filter_by(status='cancelled').count() if hasattr(Appointment, 'status') else 0
        total_count = Appointment.query.count()
        
        # If no status field exists, calculate based on dates
        if not hasattr(Appointment, 'status'):
            current_date = datetime.now().date()
            all_appointments = Appointment.query.all()
            active_count = sum(1 for apt in all_appointments if apt.appdate >= current_date)
            completed_count = sum(1 for apt in all_appointments if apt.appdate < current_date)
            cancelled_count = 0
        
        # Get current date for the page
        current_date = datetime.now().strftime("%A, %B %d, %Y")
        today_date = datetime.now().strftime("%Y-%m-%d")
        
        # Render the template with the data
        return render_template('appointments/appointments.html', 
                              appointments=formatted_appointments, 
                              all_patients=all_patients,
                              current_date=current_date,
                              today_date=today_date,
                              status_filter=status_filter,
                              active_count=active_count,
                              completed_count=completed_count,
                              cancelled_count=cancelled_count,
                              total_count=total_count)
    except Exception as e:
        print(f"Error in appointments route: {e}")
        return f"Error loading appointments: {e}", 500
    
@app.route('/print_patients_report')
def print_patients_report():
    """Generate a printable patients report with filters - Updated to match appointments styling"""
    try:
        # Get filter parameters
        status_filter = request.args.get('status', 'all')
        search_filter = request.args.get('search', '')
        
        print(f"Print request - Status: {status_filter}, Search: {search_filter}")
        
        # Build query based on status filter
        if status_filter == 'active':
            patients_list = Patient.query.filter_by(is_deleted=False).all()
        elif status_filter == 'inactive':
            patients_list = Patient.query.filter_by(is_deleted=True).all()
        else:  # 'all'
            patients_list = Patient.query.all()
        
        # Apply search filter if provided
        if search_filter:
            filtered_patients = []
            for patient in patients_list:
                if (search_filter.lower() in patient.patname.lower() or 
                    search_filter.lower() in (patient.patcontact or '').lower() or
                    search_filter.lower() in (patient.patemail or '').lower()):
                    filtered_patients.append(patient)
            patients_list = filtered_patients
        
        # Separate active and inactive patients for display
        active_patients = []
        inactive_patients = []
        
        for patient in patients_list:
            # Get latest appointment/visit
            latest_appointment = Appointment.query.filter_by(apppatient=patient.patname).order_by(Appointment.appdate.desc()).first()
            last_visit = latest_appointment.appdate.strftime('%m/%d/%Y') if latest_appointment and latest_appointment.appdate else "No visits"
            
            # Get latest procedure
            latest_procedure = Report.query.filter_by(reppatient=patient.patname).order_by(Report.repdate.desc()).first()
            last_procedure = latest_procedure.repdate.strftime('%m/%d/%Y') if latest_procedure and latest_procedure.repdate else "No procedures"
            
            patient_data = {
                'id': f"PAT-{patient.patId:03d}",
                'name': patient.patname,
                'contact': patient.patcontact or "N/A",
                'gender': patient.patgender or "N/A",
                'age': patient.patage or "N/A",
                'address': patient.pataddress or "N/A",
                'email': patient.patemail or "N/A",
                'last_visit': last_visit,
                'last_procedure': last_procedure,
                'registration_date': patient.patdob.strftime('%m/%d/%Y') if patient.patdob else "N/A",
                'is_active': not patient.is_deleted
            }
            
            if patient.is_deleted:
                inactive_patients.append(patient_data)
            else:
                active_patients.append(patient_data)
        
        # Prepare filter information for display (matching appointments style)
        status_labels = {
            'all': 'All Patients',
            'active': 'Active Patients Only',
            'inactive': 'Inactive Patients Only'
        }
        
        filter_info = {
            'status': status_labels.get(status_filter, status_filter.title()),
            'search': search_filter if search_filter else 'No search filter',
            'has_filters': status_filter != 'all' or search_filter,
            'status_filter': status_filter,  # Keep raw status for conditional display
            'has_status_filter': status_filter != 'all'
        }
        
        # Get statistics based on current filter
        if status_filter == 'active':
            total_patients = len(active_patients)
            active_count = len(active_patients)
            inactive_count = 0
            filtered_patients = active_patients
        elif status_filter == 'inactive':
            total_patients = len(inactive_patients)
            active_count = 0
            inactive_count = len(inactive_patients)
            filtered_patients = inactive_patients
        else:  # 'all'
            total_patients = len(patients_list)
            active_count = len(active_patients)
            inactive_count = len(inactive_patients)
            filtered_patients = active_patients + inactive_patients
        
        # Get current user information
        current_user = session.get('real_name', session.get('username', 'Unknown User'))
        user_id = session.get('user_id')
        
        # Generate print timestamp
        print_date = datetime.now().strftime('%B %d, %Y')
        print_time = datetime.now().strftime('%I:%M %p')
        print_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Log the print action
        filter_description = []
        filter_description.append(f"Status: {status_labels.get(status_filter, status_filter)}")
        if search_filter:
            filter_description.append(f"Search: {search_filter}")
        
        filter_text = ", ".join(filter_description)
        
        log_user_action(
            user_id,
            'Print Patients Report',
            f'Generated patients report: {total_patients} patients ({filter_text})'
        )
        
        return render_template('patients/print_patients_report.html',
                              active_patients=active_patients if status_filter != 'inactive' else [],
                              inactive_patients=inactive_patients if status_filter != 'active' else [],
                              filtered_patients=filtered_patients,
                              filter_info=filter_info,
                              status_filter=status_filter,
                              total_patients=total_patients,
                              active_count=active_count,
                              inactive_count=inactive_count,
                              current_user=current_user,
                              print_date=print_date,
                              print_time=print_time,
                              print_datetime=print_datetime)
    
    except Exception as e:
        print(f"Error generating patients report: {e}")
        return f"Error generating patients report: {e}", 500
    


@app.route('/add_appointment', methods=['POST'])
def add_appointment():
    """Add a new appointment with active status"""
    try:
        # Get patient name from the patient ID
        patient_id = request.form.get('patient_id')
        patient = Patient.query.get(patient_id)
        patient_name = patient.patname if patient else "Unknown Patient"
        
        # Create new appointment with active status
        appointment_data = {
            'apppatient': patient_name,
            'apptime': request.form.get('time'),
            'appdate': datetime.strptime(request.form.get('date'), '%Y-%m-%d').date()
        }
        
        # Add status if the field exists
        if hasattr(Appointment, 'status'):
            appointment_data['status'] = 'active'
        
        new_appointment = Appointment(**appointment_data)
        
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
                "status": getattr(new_appointment, 'status', 'active'),
                "raw_id": new_appointment.appid
            }
        })
    except Exception as e:
        db.session.rollback()
        print(f"Error in add_appointment route: {e}")
        return jsonify({"success": False, "error": str(e)})
    
@app.route('/cancel_appointment', methods=['POST'])
def cancel_appointment():
    """Cancel an appointment by setting status to cancelled"""
    try:
        appointment_id = request.form.get('appointment_id')
        if not appointment_id:
            return jsonify({"success": False, "error": "No appointment ID provided"})
            
        appointment = Appointment.query.get_or_404(int(appointment_id))
        
        # Set status to cancelled instead of deleting
        if hasattr(appointment, 'status'):
            appointment.status = 'cancelled'
        else:
            # If no status field exists, you can still delete the appointment
            # or add a different approach to mark it as cancelled
            return jsonify({"success": False, "error": "Status field not available. Please add status column to appointment table."})
        
        db.session.commit()
        
        # Log the action
        log_user_action(
            session.get('user_id'),
            'Cancel Appointment',
            f'Cancelled appointment for {appointment.apppatient} on {appointment.appdate} at {appointment.apptime}'
        )
        
        return jsonify({"success": True, "message": "Appointment cancelled successfully"})
    except Exception as e:
        db.session.rollback()
        print(f"Error in cancel_appointment route: {e}")
        return jsonify({"success": False, "error": str(e)})

@app.route('/complete_appointment/<int:appointment_id>', methods=['POST'])
def complete_appointment(appointment_id):
    """Mark an appointment as completed"""
    try:
        appointment = Appointment.query.get_or_404(appointment_id)
        
        # Set status to completed
        if hasattr(appointment, 'status'):
            appointment.status = 'completed'
        
        db.session.commit()
        
        # Log the action
        log_user_action(
            session.get('user_id'),
            'Complete Appointment',
            f'Marked appointment as completed for {appointment.apppatient} on {appointment.appdate} at {appointment.apptime}'
        )
        
        return jsonify({"success": True, "message": "Appointment marked as completed"})
    except Exception as e:
        db.session.rollback()
        print(f"Error in complete_appointment route: {e}")
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

# Add this simple test route to your app.py to isolate the issue

@app.route('/test_cancel/<int:appointment_id>')
def test_cancel_appointment(appointment_id):
    """Simple test route to check appointment cancellation without AJAX"""
    try:
        print(f"Testing cancellation for appointment {appointment_id}")
        
        # Get the appointment
        appointment = Appointment.query.get(appointment_id)
        if not appointment:
            return f"ERROR: Appointment {appointment_id} not found"
        
        print(f"Found appointment: {appointment.apppatient} on {appointment.appdate}")
        
        # Check current status
        try:
            current_status = appointment.status
            print(f"Current status: {current_status}")
        except AttributeError as e:
            return f"ERROR: Cannot access status field: {e}. You need to restart Flask!"
        
        # Try to update status
        try:
            appointment.status = 'cancelled'
            db.session.commit()
            print("Status updated successfully")
            
            # Verify the update
            updated_appointment = Appointment.query.get(appointment_id)
            new_status = updated_appointment.status
            
            if new_status == 'cancelled':
                return f"""
                <h2>✅ SUCCESS!</h2>
                <p><strong>Appointment ID:</strong> {appointment_id}</p>
                <p><strong>Patient:</strong> {appointment.apppatient}</p>
                <p><strong>Date:</strong> {appointment.appdate}</p>
                <p><strong>Status changed to:</strong> {new_status}</p>
                <hr>
                <p><a href="/appointments">← Back to Appointments</a></p>
                <p><a href="/test_reactivate/{appointment_id}">🔄 Test Reactivate</a></p>
                """
            else:
                return f"ERROR: Status update failed. Expected 'cancelled', got '{new_status}'"
                
        except Exception as update_error:
            db.session.rollback()
            return f"ERROR during status update: {update_error}"
            
    except Exception as e:
        import traceback
        return f"""
        <h2>❌ ERROR</h2>
        <p><strong>Error:</strong> {e}</p>
        <p><strong>Type:</strong> {type(e)}</p>
        <pre>{traceback.format_exc()}</pre>
        <hr>
        <p><a href="/appointments">← Back to Appointments</a></p>
        """

@app.route('/test_reactivate/<int:appointment_id>')
def test_reactivate_appointment(appointment_id):
    """Simple test route to reactivate an appointment"""
    try:
        appointment = Appointment.query.get(appointment_id)
        if not appointment:
            return f"ERROR: Appointment {appointment_id} not found"
        
        appointment.status = 'active'
        db.session.commit()
        
        return f"""
        <h2>✅ REACTIVATED!</h2>
        <p><strong>Appointment ID:</strong> {appointment_id}</p>
        <p><strong>Patient:</strong> {appointment.apppatient}</p>
        <p><strong>Status:</strong> {appointment.status}</p>
        <hr>
        <p><a href="/appointments">← Back to Appointments</a></p>
        <p><a href="/test_cancel/{appointment_id}">❌ Test Cancel Again</a></p>
        """
        
    except Exception as e:
        db.session.rollback()
        return f"ERROR reactivating: {e}"

@app.route('/check_appointment_model')
def check_appointment_model():
    """Check if the Appointment model is properly configured"""
    try:
        # Get the model's table information
        columns = Appointment.__table__.columns.keys()
        
        result = f"""
        <h2>Appointment Model Debug Info</h2>
        <p><strong>Table name:</strong> {Appointment.__tablename__}</p>
        <p><strong>Columns:</strong> {', '.join(columns)}</p>
        
        <h3>Status Column Details:</h3>
        """
        
        if 'status' in columns:
            status_col = Appointment.__table__.columns['status']
            result += f"""
            <p>✅ Status column exists in model</p>
            <p><strong>Type:</strong> {status_col.type}</p>
            <p><strong>Default:</strong> {status_col.default}</p>
            <p><strong>Nullable:</strong> {status_col.nullable}</p>
            """
        else:
            result += "<p>❌ Status column missing from model</p>"
        
        # Test creating an appointment instance
        try:
            test_apt = Appointment()
            test_apt.status = 'test'
            result += "<p>✅ Can set status on model instance</p>"
        except AttributeError as e:
            result += f"<p>❌ Cannot set status: {e}</p>"
        
        # Check database table structure
        from sqlalchemy import text
        db_columns = db.session.execute(text("DESCRIBE appointment")).fetchall()
        
        result += "<h3>Database Table Structure:</h3><ul>"
        for col in db_columns:
            result += f"<li><strong>{col[0]}</strong>: {col[1]} (Default: {col[4]})</li>"
        result += "</ul>"
        
        result += '<hr><p><a href="/appointments">← Back to Appointments</a></p>'
        
        return result
        
    except Exception as e:
        import traceback
        return f"""
        <h2>Error checking model:</h2>
        <p>{e}</p>
        <pre>{traceback.format_exc()}</pre>
        """
    
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
    
@app.route('/print_appointments_report')
def print_appointments_report():
    """Generate a printable appointments report with improved status filters"""
    try:
        # Get filter parameters
        status_filter = request.args.get('status', 'all')
        date_filter = request.args.get('date', '')
        patient_filter = request.args.get('patient', '')
        
        print(f"Print request - Status: {status_filter}, Date: {date_filter}, Patient: {patient_filter}")
        
        # Build query based on status filter with improved logic
        query = Appointment.query
        
        # Apply status filter
        if status_filter == 'active':
            # Check if status field exists, if not use date-based logic
            if hasattr(Appointment, 'status'):
                query = query.filter_by(status='active')
            else:
                # Fallback: consider future/today dates as active
                current_date = datetime.now().date()
                query = query.filter(Appointment.appdate >= current_date)
        elif status_filter == 'completed':
            if hasattr(Appointment, 'status'):
                query = query.filter_by(status='completed')
            else:
                # Fallback: consider past dates as completed
                current_date = datetime.now().date()
                query = query.filter(Appointment.appdate < current_date)
        elif status_filter == 'cancelled':
            if hasattr(Appointment, 'status'):
                query = query.filter_by(status='cancelled')
            else:
                # If no status field, we can't determine cancelled appointments
                query = query.filter(False)  # Return no results
        # For 'all', no status filter is applied
        
        appointments_list = query.order_by(Appointment.appdate.desc()).all()
        
        # Format appointments for display with proper status detection
        formatted_appointments = []
        for appointment in appointments_list:
            # Determine status display
            if hasattr(appointment, 'status') and appointment.status:
                status = appointment.status
            else:
                # Fallback status determination based on date
                current_date = datetime.now().date()
                if appointment.appdate < current_date:
                    status = 'completed'
                elif appointment.appdate == current_date:
                    status = 'active'
                else:
                    status = 'active'
            
            # Apply additional filters
            include_appointment = True
            
            # Date filter
            if date_filter:
                try:
                    filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
                    if appointment.appdate != filter_date:
                        include_appointment = False
                except ValueError:
                    pass
            
            # Patient filter
            if patient_filter and include_appointment:
                if patient_filter.lower() not in appointment.apppatient.lower():
                    include_appointment = False
            
            if include_appointment:
                # Get patient details
                patient = Patient.query.filter_by(patname=appointment.apppatient).first()
                
                formatted_appointments.append({
                    'id': f"APT-{appointment.appid:03d}",
                    'patient_name': appointment.apppatient,
                    'patient_contact': patient.patcontact if patient else "N/A",
                    'patient_id': f"PAT-{patient.patId:03d}" if patient else "N/A",
                    'date': appointment.appdate.strftime('%B %d, %Y') if appointment.appdate else "N/A",
                    'time': appointment.apptime or "N/A",
                    'status': status.capitalize(),
                    'doctor': "Dr. Andrews",  # Default since not in schema
                    'treatment': "General Checkup",  # Default since not in schema
                    'raw_date': appointment.appdate.strftime('%Y-%m-%d') if appointment.appdate else "",
                    'raw_time': appointment.apptime or ""
                })
        
        # Sort appointments by date and time
        formatted_appointments.sort(key=lambda x: (x['raw_date'], x['raw_time']))
        
        # Prepare IMPROVED filter information for display
        status_labels = {
            'all': 'All Appointments',
            'active': 'Active Appointments Only',
            'completed': 'Completed Appointments Only',
            'cancelled': 'Cancelled Appointments Only'
        }
        
        filter_info = {
            'status': status_labels.get(status_filter, status_filter.title()),
            'date': datetime.strptime(date_filter, '%Y-%m-%d').strftime('%B %d, %Y') if date_filter else 'All Dates',
            'patient': patient_filter.title() if patient_filter else 'All Patients',
            'has_filters': status_filter != 'all' or date_filter or patient_filter,
            'status_filter': status_filter,  # Keep raw status for conditional display
            'has_status_filter': status_filter != 'all'
        }
        
        # Get statistics based on current filter
        total_appointments = len(formatted_appointments)
        status_counts = {
            'active': len([a for a in formatted_appointments if a['status'].lower() == 'active']),
            'completed': len([a for a in formatted_appointments if a['status'].lower() == 'completed']),
            'cancelled': len([a for a in formatted_appointments if a['status'].lower() == 'cancelled'])
        }
        
        # Get current user information
        current_user = session.get('real_name', session.get('username', 'Unknown User'))
        user_id = session.get('user_id')
        
        # Generate print timestamp
        print_date = datetime.now().strftime('%B %d, %Y')
        print_time = datetime.now().strftime('%I:%M %p')
        print_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Log the print action with improved detail
        filter_description = []
        filter_description.append(f"Status: {status_labels.get(status_filter, status_filter)}")
        if date_filter:
            filter_description.append(f"Date: {filter_info['date']}")
        if patient_filter:
            filter_description.append(f"Patient: {patient_filter}")
        
        filter_text = ", ".join(filter_description)
        
        log_user_action(
            user_id,
            'Print Appointments Report',
            f'Generated appointments report: {total_appointments} appointments ({filter_text})'
        )
        
        return render_template('appointments/print_appointments_report.html',
                              appointments=formatted_appointments,
                              filter_info=filter_info,
                              total_appointments=total_appointments,
                              status_counts=status_counts,
                              current_user=current_user,
                              print_date=print_date,
                              print_time=print_time,
                              print_datetime=print_datetime)
    
    except Exception as e:
        print(f"Error generating appointments report: {e}")
        return f"Error generating appointments report: {e}", 500

@app.route('/treatments')
def treatments():
    """Redirect to procedures page"""
    return render_template('procedures.html')

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

@app.route('/edit_staff/<int:staff_id>')
def edit_staff(staff_id):
    """Render edit staff page"""
    try:
        staff = User.query.get_or_404(staff_id)
        
        # Add is_active attribute for template
        staff.is_active = True
        if hasattr(staff, 'is_deleted'):
            staff.is_active = not staff.is_deleted
        
        # Format date of birth for HTML date input
        if hasattr(staff, 'usersdob') and staff.usersdob:
            staff.usersdob_formatted = staff.usersdob.strftime('%Y-%m-%d')
        
        # For now, redirect back to staff details since we don't have an edit template
        # You can create a proper edit template later
        return redirect(url_for('staff_details', staff_id=staff_id))
        
    except Exception as e:
        print(f"Error in edit_staff route: {e}")
        return f"Error loading staff edit form: {e}", 500

@app.route('/staff')
def staff():
    """Staff management page with status filtering"""
    try:
        # Get status filter from query parameter (default to 'active')
        status_filter = request.args.get('status', 'active')
        
        # Build query based on status filter - check if User model has is_deleted field
        base_query = User.query.filter(User.usersaccess.in_(['admin', 'user']))
        
        if status_filter == 'active':
            # Check if User model has is_deleted field
            if hasattr(User, 'is_deleted'):
                staff_users = base_query.filter_by(is_deleted=False).all()
            else:
                # Fallback: assume all users are active if no is_deleted field
                staff_users = base_query.all()
        elif status_filter == 'inactive':
            if hasattr(User, 'is_deleted'):
                staff_users = base_query.filter_by(is_deleted=True).all()
            else:
                staff_users = []  # No inactive users if no is_deleted field
        else:  # 'all'
            staff_users = base_query.all()
        
        # Format staff data for the template
        staff_members = []
        for user in staff_users:
            # Determine role based on some attribute or default to "Staff"
            role = "Staff"  # Default
            if hasattr(user, 'usersrole') and user.usersrole:
                role = user.usersrole
            
            # Check if user is active
            is_active = True
            if hasattr(user, 'is_deleted'):
                is_active = not user.is_deleted
            
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
                'is_active': is_active,  # Add this for template filtering
                'appointment_count': 0,
                'patient_count': 0,
            })
        
        # Get counts for status badges
        if hasattr(User, 'is_deleted'):
            active_count = User.query.filter(
                User.usersaccess.in_(['admin', 'user']),
                User.is_deleted == False
            ).count()
            inactive_count = User.query.filter(
                User.usersaccess.in_(['admin', 'user']),
                User.is_deleted == True
            ).count()
        else:
            # Fallback counts if no is_deleted field
            total_count = User.query.filter(User.usersaccess.in_(['admin', 'user'])).count()
            active_count = total_count
            inactive_count = 0
        
        total_count = active_count + inactive_count
        
        return render_template('staff.html', 
                              staff_members=staff_members,
                              current_date=datetime.now().strftime('%B %d, %Y'),
                              status_filter=status_filter,
                              active_count=active_count,
                              inactive_count=inactive_count,
                              total_count=total_count)
    
    except Exception as e:
        print(f"Error loading staff page: {e}")
        return f"Error loading staff page: {e}", 500

@app.route('/deactivate_staff/<int:staff_id>', methods=['POST'])
def deactivate_staff(staff_id):
    """Deactivate a staff member (soft delete)"""
    try:
        staff = User.query.get_or_404(staff_id)
        
        # Don't allow deactivating self
        if session.get('user_id') == staff_id:
            return jsonify({"success": False, "error": "Cannot deactivate your own account"})
        
        # Check if User model has is_deleted field
        if hasattr(staff, 'is_deleted'):
            staff.is_deleted = True
        else:
            # If no is_deleted field exists, we need to add it to the model first
            return jsonify({
                "success": False, 
                "error": "User model does not have is_deleted field. Please add it to the database schema first."
            })
        
        db.session.commit()
        
        # Log the action
        log_user_action(
            session.get('user_id'),
            'Deactivate Staff',
            f'Deactivated staff member: {staff.usersrealname} ({staff.usersusername})'
        )
        
        return jsonify({"success": True, "message": "Staff member deactivated successfully"})
    except Exception as e:
        db.session.rollback()
        print(f"Error in deactivate_staff route: {e}")
        return jsonify({"success": False, "error": str(e)})

@app.route('/reactivate_staff/<int:staff_id>', methods=['POST'])  
def reactivate_staff(staff_id):
    """Reactivate a staff member (restore from soft delete)"""
    try:
        staff = User.query.get_or_404(staff_id)
        
        # Check if User model has is_deleted field
        if hasattr(staff, 'is_deleted'):
            staff.is_deleted = False
        else:
            # If no is_deleted field exists, we need to add it to the model first
            return jsonify({
                "success": False, 
                "error": "User model does not have is_deleted field. Please add it to the database schema first."
            })
        
        db.session.commit()
        
        # Log the action
        log_user_action(
            session.get('user_id'),
            'Reactivate Staff',
            f'Reactivated staff member: {staff.usersrealname} ({staff.usersusername})'
        )
        
        return jsonify({"success": True, "message": "Staff member reactivated successfully"})
    except Exception as e:
        db.session.rollback()
        print(f"Error in reactivate_staff route: {e}")
        return jsonify({"success": False, "error": str(e)})

@app.route('/staff_details/<int:staff_id>')
def staff_details(staff_id):
    """View details of a specific staff member with status information"""
    try:
        staff = User.query.get_or_404(staff_id)
        
        # Add is_active attribute for template
        staff.is_active = True
        if hasattr(staff, 'is_deleted'):
            staff.is_active = not staff.is_deleted
        
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
                'usersoccupation': staff.usersoccupation if hasattr(staff, 'usersoccupation') else 'Staff',
                'is_active': staff.is_active
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
        
        # For browser requests, try to render the template, but handle if it doesn't exist
        try:
            return render_template('staff_details.html', 
                                  staff=staff,
                                  current_date=current_date)
        except Exception as template_error:
            # If template doesn't exist, show a simple page with staff info
            return f"""
            <html>
            <head><title>Staff Details - {staff.usersrealname}</title></head>
            <body style="font-family: Arial, sans-serif; padding: 20px;">
                <h1>Staff Details</h1>
                <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h2>{staff.usersrealname}</h2>
                    <p><strong>Username:</strong> {staff.usersusername}</p>
                    <p><strong>Email:</strong> {staff.usersemail or 'N/A'}</p>
                    <p><strong>Contact:</strong> {staff.userscontact or 'N/A'}</p>
                    <p><strong>Occupation:</strong> {getattr(staff, 'usersoccupation', 'Staff')}</p>
                    <p><strong>Access Level:</strong> {staff.usersaccess.capitalize()}</p>
                    <p><strong>Status:</strong> {'Active' if staff.is_active else 'Inactive'}</p>
                    <p><strong>Address:</strong> {staff.usershomeaddress or 'N/A'}</p>
                    <p><strong>City/Zip:</strong> {staff.userscityzipcode or 'N/A'}</p>
                    <p><strong>Religion:</strong> {staff.usersreligion or 'N/A'}</p>
                    <p><strong>Gender:</strong> {staff.usersgender or 'N/A'}</p>
                </div>
                <div style="margin-top: 20px;">
                    <a href="/staff" style="background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px;">← Back to Staff Directory</a>
                    <button onclick="editStaff({staff_id})" style="background: #28a745; color: white; padding: 10px 20px; border: none; border-radius: 4px; margin-left: 10px; cursor: pointer;">Edit Staff</button>
                    {'<button onclick="deactivateStaff(' + str(staff_id) + ')" style="background: #dc3545; color: white; padding: 10px 20px; border: none; border-radius: 4px; margin-left: 10px; cursor: pointer;">Deactivate</button>' if staff.is_active else '<button onclick="reactivateStaff(' + str(staff_id) + ')" style="background: #28a745; color: white; padding: 10px 20px; border: none; border-radius: 4px; margin-left: 10px; cursor: pointer;">Reactivate</button>'}
                </div>
                <script>
                function editStaff(staffId) {{
                    // Redirect to staff list and trigger edit modal
                    window.location.href = '/staff#edit-' + staffId;
                }}
                function deactivateStaff(staffId) {{
                    if (confirm('Are you sure you want to deactivate this staff member?')) {{
                        fetch('/deactivate_staff/' + staffId, {{method: 'POST'}})
                        .then(response => response.json())
                        .then(data => {{
                            if (data.success) {{
                                alert('Staff member deactivated successfully');
                                location.reload();
                            }} else {{
                                alert('Error: ' + data.error);
                            }}
                        }});
                    }}
                }}
                function reactivateStaff(staffId) {{
                    if (confirm('Are you sure you want to reactivate this staff member?')) {{
                        fetch('/reactivate_staff/' + staffId, {{method: 'POST'}})
                        .then(response => response.json())
                        .then(data => {{
                            if (data.success) {{
                                alert('Staff member reactivated successfully');
                                location.reload();
                            }} else {{
                                alert('Error: ' + data.error);
                            }}
                        }});
                    }}
                }}
                </script>
            </body>
            </html>
            """
    except Exception as e:
        print(f"Error in staff_details route: {e}")
        return f"Error loading staff details: {e}", 500
    
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
                cursor.execute(text("SHOW TABLES"))
                tables = cursor.fetchall()
                
                if not tables:
                    f.write("-- No tables found in database\n")
                
                # For each table, get CREATE TABLE statement and data
                for table in tables:
                    table_name = list(table.values())[0]
                    
                    # Get the CREATE TABLE statement
                    cursor.execute(text(f"SHOW CREATE TABLE `{table_name}`"))
                    create_table = cursor.fetchone()
                    create_table_sql = list(create_table.values())[1]
                    
                    # Write the DROP TABLE and CREATE TABLE statements
                    f.write(f"DROP TABLE IF EXISTS `{table_name}`;\n")
                    f.write(f"{create_table_sql};\n\n")
                    
                    # Get table data
                    cursor.execute(text(f"SELECT * FROM `{table_name}`"))
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

# =============================================================================
# ENHANCED DENTAL CHART ROUTES - WORKING CREATE CHART FUNCTIONALITY
# =============================================================================

# PROCEDURE MANAGEMENT ROUTES
@app.route('/procedures')
def procedures():
    """Main procedures page showing all patients and recent procedures"""
    try:
        # Get all active patients
        patients_list = Patient.query.filter_by(is_deleted=False).all()
        
        # Get recent reports/procedures
        recent_procedures = db.session.query(
            Report.repid,
            Report.reppatient,
            Report.repdate,
            Report.repdentist,
            Report.repprescription,
            Report.repcleaning,
            Report.repextraction,
            Report.reprootcanal,
            Report.repbraces,
            Report.repdentures,
            Report.repothers
        ).order_by(Report.repdate.desc()).limit(10).all()
        
        # Format patients for display
        formatted_patients = []
        for patient in patients_list:
            # Check if patient has dental chart
            dental_chart = DentalChart.query.filter_by(dcpatname=patient.patname, is_deleted=False).first()
            teeth_chart = Teeth.query.filter_by(tpatname=patient.patname, is_deleted=False).first()
            
            formatted_patients.append({
                'id': f"PAT-{patient.patId:03d}",
                'name': patient.patname,
                'contact': patient.patcontact or "N/A",
                'age': patient.patage or "N/A",
                'gender': patient.patgender or "N/A",
                'has_dental_chart': dental_chart is not None,
                'has_teeth_chart': teeth_chart is not None,
                'raw_id': patient.patId
            })
        
        # Format recent procedures
        formatted_procedures = []
        for proc in recent_procedures:
            # Build procedure list
            procedures_done = []
            if proc.repcleaning: procedures_done.append("Cleaning")
            if proc.repextraction: procedures_done.append("Extraction")
            if proc.reprootcanal: procedures_done.append("Root Canal")
            if proc.repbraces: procedures_done.append("Braces")
            if proc.repdentures: procedures_done.append("Dentures")
            if proc.repothers: procedures_done.append(proc.repothers)
            
            formatted_procedures.append({
                'id': f"PROC-{proc.repid:03d}",
                'patient_name': proc.reppatient,
                'date': proc.repdate.strftime('%B %d, %Y') if proc.repdate else "N/A",
                'dentist': proc.repdentist or "N/A",
                'procedures': ", ".join(procedures_done) if procedures_done else "General Visit",
                'prescription': proc.repprescription or "None",
                'raw_id': proc.repid
            })
        
        # Get statistics
        total_patients = len(patients_list)
        patients_with_charts = sum(1 for p in formatted_patients if p['has_dental_chart'])
        today_procedures = Report.query.filter_by(repdate=date.today()).count()
        
        current_date = datetime.now().strftime("%A, %B %d, %Y")
        
        return render_template('procedures/procedures.html',
                              patients=formatted_patients,
                              recent_procedures=formatted_procedures,
                              total_patients=total_patients,
                              patients_with_charts=patients_with_charts,
                              today_procedures=today_procedures,
                              current_date=current_date)
    
    except Exception as e:
        print(f"Error in procedures route: {e}")
        return f"Error loading procedures: {e}", 500

@app.route('/create_dental_chart_now/<int:patient_id>')
def create_dental_chart_now(patient_id):
    """
    Robust dental chart creation with comprehensive error handling
    This route handles all edge cases and provides clear feedback
    """
    try:
        print(f"=== CREATE CHART DEBUG START for Patient ID: {patient_id} ===")
        
        # Step 1: Validate patient exists
        patient = Patient.query.get(patient_id)
        if not patient:
            print(f"ERROR: Patient {patient_id} not found")
            return f"Error: Patient with ID {patient_id} not found", 404
            
        print(f"SUCCESS: Found patient {patient.patname}")
        
        # Step 2: Check if dental chart already exists
        existing_dental_chart = DentalChart.query.filter_by(
            dcpatname=patient.patname, 
            is_deleted=False
        ).first()
        
        if existing_dental_chart:
            print(f"INFO: Dental chart already exists, redirecting to edit")
            return redirect(f"/patient_dental_chart/{patient_id}?message=Chart already exists")
        
        # Step 3: Get next available IDs
        try:
            max_dental_id = db.session.query(db.func.max(DentalChart.dcID)).scalar() or 0
            next_dental_id = max_dental_id + 1
            print(f"Next dental chart ID: {next_dental_id}")
            
            max_teeth_id = db.session.query(db.func.max(Teeth.tID)).scalar() or 0
            next_teeth_id = max_teeth_id + 1
            print(f"Next teeth chart ID: {next_teeth_id}")
            
        except Exception as id_error:
            print(f"ERROR getting next IDs: {str(id_error)}")
            return f"Database ID Error: {str(id_error)}", 500
        
        # Step 4: Create dental chart
        try:
            dental_chart = DentalChart(
                dcID=next_dental_id,
                dcpatname=patient.patname,
                dcpcontact=patient.patcontact or "",
                dcdoctor="",
                dcdentist="",
                dcdcontact="",
                dcvisit="",
                dcq1="",
                dcq2="",
                dcqe2="",
                dcq3="",
                dcqe3="",
                dcq4="",
                dcqe4="",
                dcq5="",
                dcqe5="",
                dcq6="",
                dcq7="",
                dcqe7="",
                dcq8="",
                dcqe8="",
                dcq9="",
                dcqe9="",
                is_deleted=False
            )
            
            db.session.add(dental_chart)
            print(f"SUCCESS: Created dental chart object")
            
        except Exception as chart_error:
            print(f"ERROR creating dental chart: {str(chart_error)}")
            return f"Dental Chart Creation Error: {str(chart_error)}", 500
        
        # Step 5: Create teeth chart with all teeth healthy
        try:
            teeth_data = {}
            for i in range(1, 33):  # Teeth 1-32
                teeth_data[f'l{i}'] = 'healthy'
            
            teeth_chart = Teeth(
                tID=next_teeth_id,
                tpatname=patient.patname,
                is_deleted=False,
                **teeth_data
            )
            
            db.session.add(teeth_chart)
            print(f"SUCCESS: Created teeth chart object")
            
        except Exception as teeth_error:
            print(f"ERROR creating teeth chart: {str(teeth_error)}")
            db.session.rollback()
            return f"Teeth Chart Creation Error: {str(teeth_error)}", 500
        
        # Step 6: Commit to database
        try:
            db.session.commit()
            print(f"SUCCESS: Committed both charts to database")
            
        except Exception as commit_error:
            print(f"ERROR committing to database: {str(commit_error)}")
            db.session.rollback()
            return f"Database Commit Error: {str(commit_error)}", 500
        
        # Step 7: Log the action
        try:
            log_user_action(
                session.get('user_id', 0),
                'Create Dental Chart',
                f'Created dental chart for {patient.patname} (ID: PAT-{patient.patId:03d})'
            )
            print(f"SUCCESS: Logged user action")
            
        except Exception as log_error:
            print(f"WARNING: Failed to log action: {str(log_error)}")
            # Don't fail the whole operation for logging issues
        
        print(f"=== CREATE CHART DEBUG SUCCESS ===")
        
        # Step 8: Redirect with success message
        return redirect(f"/patient_dental_chart/{patient_id}?created=success")
        
    except Exception as e:
        print(f"=== CREATE CHART CRITICAL ERROR ===")
        print(f"Error: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        db.session.rollback()
        
        # Return user-friendly error message
        return f"""
        <h2>Chart Creation Failed</h2>
        <p><strong>Error:</strong> {str(e)}</p>
        <p><strong>Patient ID:</strong> {patient_id}</p>
        <p><a href="/dental_charts">← Back to Dental Charts</a></p>
        <hr>
        <details>
            <summary>Technical Details (for debugging)</summary>
            <pre>{traceback.format_exc()}</pre>
        </details>
        """, 500

@app.route('/test_chart_creation/<int:patient_id>')
def test_chart_creation(patient_id):
    """
    Test route to verify chart creation capability
    Use this to diagnose issues before actual creation
    """
    try:
        results = []
        
        # Test 1: Patient exists
        patient = Patient.query.get(patient_id)
        if patient:
            results.append(f"✓ Patient found: {patient.patname}")
        else:
            results.append(f"✗ Patient {patient_id} not found")
            return "<br>".join(results)
        
        # Test 2: Database connection (FIXED with text() wrapper)
        try:
            db.session.execute(text('SELECT 1'))
            results.append("✓ Database connection OK")
        except Exception as db_error:
            results.append(f"✗ Database error: {str(db_error)}")
        
        # Test 3: Check existing charts
        existing_dental = DentalChart.query.filter_by(dcpatname=patient.patname).first()
        if existing_dental:
            results.append(f"! Dental chart already exists (ID: {existing_dental.dcID})")
        else:
            results.append("✓ No existing dental chart")
        
        existing_teeth = Teeth.query.filter_by(tpatname=patient.patname).first()
        if existing_teeth:
            results.append(f"! Teeth chart already exists (ID: {existing_teeth.tID})")
        else:
            results.append("✓ No existing teeth chart")
        
        # Test 4: Check table structure (FIXED with text() wrapper)
        try:
            columns_dental = db.session.execute(text("DESCRIBE dentalchart")).fetchall()
            results.append(f"✓ DentalChart table has {len(columns_dental)} columns")
        except Exception as table_error:
            results.append(f"✗ DentalChart table issue: {str(table_error)}")
        
        try:
            columns_teeth = db.session.execute(text("DESCRIBE teeth")).fetchall()
            results.append(f"✓ Teeth table has {len(columns_teeth)} columns")
        except Exception as table_error:
            results.append(f"✗ Teeth table issue: {str(table_error)}")
        
        # Test 5: Check next available IDs
        try:
            next_dental_id = (db.session.query(db.func.max(DentalChart.dcID)).scalar() or 0) + 1
            next_teeth_id = (db.session.query(db.func.max(Teeth.tID)).scalar() or 0) + 1
            results.append(f"✓ Next IDs: Dental={next_dental_id}, Teeth={next_teeth_id}")
        except Exception as id_error:
            results.append(f"✗ ID generation error: {str(id_error)}")
        
        results.append("")
        results.append(f"<a href='/create_dental_chart_now/{patient_id}'>→ Create Chart Now</a>")
        results.append(f"<a href='/dental_charts'>← Back to Charts List</a>")
        
        return "<br>".join(results)
        
    except Exception as e:
        return f"Test failed: {str(e)}"

@app.route('/patient_dental_chart/<int:patient_id>')
def patient_dental_chart(patient_id):
    """
    Enhanced dental chart display with message handling
    """
    try:
        # Handle URL parameters for messages
        created = request.args.get('created')
        message = request.args.get('message')
        
        patient = Patient.query.get_or_404(patient_id)
        
        # Get dental chart (create if missing)
        dental_chart = DentalChart.query.filter_by(dcpatname=patient.patname, is_deleted=False).first()
        if not dental_chart:
            print(f"No dental chart found for {patient.patname}, creating one...")
            return redirect(f"/create_dental_chart_now/{patient_id}")
        
        # Get teeth chart (create if missing)  
        teeth_chart = Teeth.query.filter_by(tpatname=patient.patname, is_deleted=False).first()
        if not teeth_chart:
            print(f"No teeth chart found for {patient.patname}, creating one...")
            # Create teeth chart
            max_teeth_id = db.session.query(db.func.max(Teeth.tID)).scalar() or 0
            next_teeth_id = max_teeth_id + 1
            
            teeth_data = {f'l{i}': 'healthy' for i in range(1, 33)}
            teeth_chart = Teeth(
                tID=next_teeth_id,
                tpatname=patient.patname,
                is_deleted=False,
                **teeth_data
            )
            db.session.add(teeth_chart)
            db.session.commit()
        
        # Get procedure history
        procedure_history = Report.query.filter_by(reppatient=patient.patname).order_by(Report.repdate.desc()).all()
        
        # Format teeth data
        teeth_data = []
        for i in range(1, 33):
            tooth_condition = getattr(teeth_chart, f'l{i}', 'healthy')
            if i <= 8:
                quadrant = 1
            elif i <= 16:
                quadrant = 2
            elif i <= 24:
                quadrant = 3
            else:
                quadrant = 4
                
            teeth_data.append({
                'number': i,
                'condition': tooth_condition or 'healthy',
                'quadrant': quadrant
            })
        
        # Format procedure history
        formatted_history = []
        for proc in procedure_history:
            procedures_done = []
            if proc.repcleaning: procedures_done.append("Cleaning")
            if proc.repextraction: procedures_done.append("Extraction")
            if proc.reprootcanal: procedures_done.append("Root Canal")
            if proc.repbraces: procedures_done.append("Braces")
            if proc.repdentures: procedures_done.append("Dentures")
            if proc.repothers: procedures_done.append(proc.repothers)
            
            formatted_history.append({
                'date': proc.repdate.strftime('%B %d, %Y') if proc.repdate else "N/A",
                'procedures': ", ".join(procedures_done) if procedures_done else "General Visit",
                'dentist': proc.repdentist or "N/A",
                'prescription': proc.repprescription or "None"
            })
        
        current_date = datetime.now().strftime("%A, %B %d, %Y")
        
        # Prepare success message
        success_message = None
        if created == 'success':
            success_message = "Dental chart created successfully!"
        elif message:
            success_message = message
        
        return render_template('dental_chart.html',
                              patient=patient,
                              dental_chart=dental_chart,
                              teeth_data=teeth_data,
                              procedure_history=formatted_history,
                              current_date=current_date,
                              success_message=success_message)
    
    except Exception as e:
        print(f"Error in dental chart route: {e}")
        return f"Error loading dental chart: {e}", 500

@app.route('/update_tooth_condition', methods=['POST'])
def update_tooth_condition():
    """Update the condition of a specific tooth"""
    try:
        patient_id = request.form.get('patient_id')
        tooth_number = request.form.get('tooth_number')
        condition = request.form.get('condition')
        
        patient = Patient.query.get_or_404(patient_id)
        
        # Get teeth chart
        teeth_chart = Teeth.query.filter_by(tpatname=patient.patname, is_deleted=False).first()
        if not teeth_chart:
            return jsonify({"success": False, "error": "Teeth chart not found"})
        
        # Update the specific tooth condition
        setattr(teeth_chart, f'l{tooth_number}', condition)
        db.session.commit()
        
        # Log the action
        log_user_action(
            session.get('user_id'),
            'Update Tooth Condition',
            f'Updated tooth #{tooth_number} condition to "{condition}" for patient {patient.patname}'
        )
        
        return jsonify({
            "success": True,
            "message": f"Tooth #{tooth_number} condition updated to {condition}"
        })
    
    except Exception as e:
        db.session.rollback()
        print(f"Error in update_tooth_condition route: {e}")
        return jsonify({"success": False, "error": str(e)})

@app.route('/add_procedure', methods=['POST'])
def add_procedure():
    """Add a new procedure/treatment record"""
    try:
        patient_id = request.form.get('patient_id')
        procedure_date = request.form.get('procedure_date')
        dentist = request.form.get('dentist')
        prescription = request.form.get('prescription')
        notes = request.form.get('notes')
        
        # Procedure checkboxes
        cleaning = 1 if request.form.get('cleaning') else 0
        extraction = 1 if request.form.get('extraction') else 0
        root_canal = 1 if request.form.get('root_canal') else 0
        braces = 1 if request.form.get('braces') else 0
        dentures = 1 if request.form.get('dentures') else 0
        
        patient = Patient.query.get_or_404(patient_id)
        
        # Get next report ID
        max_id = db.session.query(db.func.max(Report.repid)).first()[0]
        next_id = 1 if max_id is None else max_id + 1
        
        # Create new report/procedure record
        new_procedure = Report(
            repid=next_id,
            reppatient=patient.patname,
            repdate=datetime.strptime(procedure_date, '%Y-%m-%d').date(),
            repprescription=prescription,
            repcleaning=cleaning,
            repextraction=extraction,
            reprootcanal=root_canal,
            repbraces=braces,
            repdentures=dentures,
            repdentist=dentist,
            repothers=notes
        )
        
        db.session.add(new_procedure)
        db.session.commit()
        
        # Log the action
        procedures_done = []
        if cleaning: procedures_done.append("Cleaning")
        if extraction: procedures_done.append("Extraction")
        if root_canal: procedures_done.append("Root Canal")
        if braces: procedures_done.append("Braces")
        if dentures: procedures_done.append("Dentures")
        if notes: procedures_done.append(notes)
        
        log_user_action(
            session.get('user_id'),
            'Add Procedure',
            f'Added procedure for {patient.patname}: {", ".join(procedures_done) if procedures_done else "General Visit"}'
        )
        
        return jsonify({
            "success": True,
            "message": "Procedure added successfully",
            "procedure": {
                "id": f"PROC-{new_procedure.repid:03d}",
                "patient": patient.patname,
                "date": new_procedure.repdate.strftime('%B %d, %Y'),
                "procedures": ", ".join(procedures_done) if procedures_done else "General Visit"
            }
        })
    
    except Exception as e:
        db.session.rollback()
        print(f"Error in add_procedure route: {e}")
        return jsonify({"success": False, "error": str(e)})

@app.route('/update_dental_chart', methods=['POST'])
def update_dental_chart():
    """Update patient's dental chart information"""
    try:
        patient_id = request.form.get('patient_id')
        patient = Patient.query.get_or_404(patient_id)
        
        # Get dental chart
        dental_chart = DentalChart.query.filter_by(dcpatname=patient.patname, is_deleted=False).first()
        if not dental_chart:
            return jsonify({"success": False, "error": "Dental chart not found"})
        
        # Update dental chart fields
        dental_chart.dcdoctor = request.form.get('doctor')
        dental_chart.dcdentist = request.form.get('dentist')
        dental_chart.dcdcontact = request.form.get('dentist_contact')
        dental_chart.dcvisit = request.form.get('visit_reason')
        
        # Update questionnaire responses
        dental_chart.dcq1 = request.form.get('q1')
        dental_chart.dcq2 = request.form.get('q2')
        dental_chart.dcqe2 = request.form.get('qe2')
        dental_chart.dcq3 = request.form.get('q3')
        dental_chart.dcqe3 = request.form.get('qe3')
        dental_chart.dcq4 = request.form.get('q4')
        dental_chart.dcqe4 = request.form.get('qe4')
        dental_chart.dcq5 = request.form.get('q5')
        dental_chart.dcqe5 = request.form.get('qe5')
        dental_chart.dcq6 = request.form.get('q6')
        dental_chart.dcq7 = request.form.get('q7')
        dental_chart.dcqe7 = request.form.get('qe7')
        dental_chart.dcq8 = request.form.get('q8')
        dental_chart.dcqe8 = request.form.get('qe8')
        dental_chart.dcq9 = request.form.get('q9')
        dental_chart.dcqe9 = request.form.get('qe9')
        
        db.session.commit()
        
        # Log the action
        log_user_action(
            session.get('user_id'),
            'Update Dental Chart',
            f'Updated dental chart for patient {patient.patname}'
        )
        
        return jsonify({
            "success": True,
            "message": "Dental chart updated successfully"
        })
    
    except Exception as e:
        db.session.rollback()
        print(f"Error in update_dental_chart route: {e}")
        return jsonify({"success": False, "error": str(e)})

@app.route('/procedure_history/<int:patient_id>')
def procedure_history(patient_id):
    """View complete procedure history for a patient"""
    try:
        patient = Patient.query.get_or_404(patient_id)
        
        # Get all procedures for this patient
        procedures = Report.query.filter_by(reppatient=patient.patname).order_by(Report.repdate.desc()).all()
        
        # Format procedures for display
        formatted_procedures = []
        for proc in procedures:
            procedures_done = []
            if proc.repcleaning: procedures_done.append("Cleaning")
            if proc.repextraction: procedures_done.append("Extraction")
            if proc.reprootcanal: procedures_done.append("Root Canal")
            if proc.repbraces: procedures_done.append("Braces")
            if proc.repdentures: procedures_done.append("Dentures")
            if proc.repothers: procedures_done.append(proc.repothers)
            
            formatted_procedures.append({
                'id': f"PROC-{proc.repid:03d}",
                'date': proc.repdate.strftime('%B %d, %Y') if proc.repdate else "N/A",
                'dentist': proc.repdentist or "N/A",
                'procedures': ", ".join(procedures_done) if procedures_done else "General Visit",
                'prescription': proc.repprescription or "None",
                'notes': proc.repothers or "None",
                'raw_id': proc.repid
            })
        
        current_date = datetime.now().strftime("%A, %B %d, %Y")
        
        return render_template('procedures/procedure_history.html',
                              patient=patient,
                              procedures=formatted_procedures,
                              current_date=current_date)
    
    except Exception as e:
        print(f"Error in procedure_history route: {e}")
        return f"Error loading procedure history: {e}", 500
    
@app.route('/dental_charts')
def dental_charts():
    """Dental charts overview page showing all patients and their chart status"""
    try:
        # Get all active patients
        patients_list = Patient.query.filter_by(is_deleted=False).all()
        
        # Format patients with dental chart information
        formatted_patients = []
        for patient in patients_list:
            # Check if patient has dental chart and teeth chart
            dental_chart = DentalChart.query.filter_by(dcpatname=patient.patname, is_deleted=False).first()
            teeth_chart = Teeth.query.filter_by(tpatname=patient.patname, is_deleted=False).first()
            
            # Get latest procedure
            latest_procedure = Report.query.filter_by(reppatient=patient.patname).order_by(Report.repdate.desc()).first()
            
            formatted_patients.append({
                'id': f"PAT-{patient.patId:03d}",
                'name': patient.patname,
                'contact': patient.patcontact or "N/A",
                'age': patient.patage or "N/A",
                'gender': patient.patgender or "N/A",
                'has_dental_chart': dental_chart is not None,
                'has_teeth_chart': teeth_chart is not None,
                'chart_complete': dental_chart is not None and teeth_chart is not None,
                'last_procedure_date': latest_procedure.repdate.strftime('%B %d, %Y') if latest_procedure and latest_procedure.repdate else "No procedures",
                'chart_created_date': dental_chart.dcpatname if dental_chart else None,  # You might want to add a created date field
                'raw_id': patient.patId
            })
        
        # Get statistics
        total_patients = len(patients_list)
        patients_with_charts = sum(1 for p in formatted_patients if p['has_dental_chart'])
        complete_charts = sum(1 for p in formatted_patients if p['chart_complete'])
        
        current_date = datetime.now().strftime("%A, %B %d, %Y")
        
        return render_template('dental_chart_overview.html',
                              patients=formatted_patients,
                              total_patients=total_patients,
                              patients_with_charts=patients_with_charts,
                              complete_charts=complete_charts,
                              current_date=current_date)
    
    except Exception as e:
        print(f"Error in dental_charts route: {e}")
        return f"Error loading dental charts: {e}", 500

@app.route('/print_dental_chart/<int:patient_id>')
def print_dental_chart(patient_id):
    """Generate printable dental chart"""
    try:
        patient = Patient.query.get_or_404(patient_id)
        dental_chart = DentalChart.query.filter_by(dcpatname=patient.patname, is_deleted=False).first()
        teeth_chart = Teeth.query.filter_by(tpatname=patient.patname, is_deleted=False).first()
        
        # Format teeth data for printing
        teeth_data = []
        if teeth_chart:
            for i in range(1, 33):
                tooth_condition = getattr(teeth_chart, f'l{i}', 'healthy')
                # Determine quadrant: 1-8=Q1, 9-16=Q2, 17-24=Q3, 25-32=Q4
                if i <= 8:
                    quadrant = 1
                elif i <= 16:
                    quadrant = 2
                elif i <= 24:
                    quadrant = 3
                else:
                    quadrant = 4
                    
                teeth_data.append({
                    'number': i,
                    'condition': tooth_condition or 'healthy',
                    'quadrant': quadrant
                })
        
        return render_template('procedures/print_dental_chart.html',
                              patient=patient,
                              dental_chart=dental_chart,
                              teeth_data=teeth_data,
                              print_date=datetime.now().strftime("%B %d, %Y"))
    
    except Exception as e:
        print(f"Error in print_dental_chart route: {e}")
        return f"Error generating printable chart: {e}", 500

# =============================================================================
# END OF ENHANCED DENTAL CHART ROUTES
# =============================================================================

if __name__ == '__main__':
    app.run(debug=True)