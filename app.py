# app.py - PostgreSQL Ready Fixed Version with Enhanced Features
from flask import Flask, render_template, request, jsonify, redirect, url_for, send_file, session, make_response
from db_connector import app as db_app, db, DatabaseConfig, Patient, Appointment, DentalChart, Inventory, RescheduleAppointment, Report, Payment, ServicePrice, User, UserLog, Teeth, log_user_action
from datetime import datetime, date, timedelta
from decimal import Decimal, InvalidOperation
import os
import time
from sqlalchemy import text, or_, inspect
import subprocess
import json
import psycopg2
import re
import hashlib
import shutil
import socket
import csv
from io import StringIO
from functools import wraps
import traceback
from urllib.parse import urlparse, parse_qs

# Use the Flask app instance from the connector
app = db_app

# Add this near the top of app.py, after the Flask app is created
app.secret_key = 'pullandentalclinic2025'  # Change this to a secure random value in production

# Set template folder
app.template_folder = 'templates'
app.static_folder = 'static'

# Add this constant near the top of app.py, after the Flask app is created
BACKUP_DIRECTORY = os.path.join(os.getcwd(), 'backups')

# Ensure backup directory exists
if not os.path.exists(BACKUP_DIRECTORY):
    os.makedirs(BACKUP_DIRECTORY)
    print(f"Created backup directory: {BACKUP_DIRECTORY}")

# =============================================================================
# LOGIN SECURITY CONFIGURATION
# =============================================================================

# Maximum failed login attempts before redirecting to forgot password
MAX_FAILED_ATTEMPTS = 3

# Countdown time (in seconds) before automatic redirect to forgot password
REDIRECT_COUNTDOWN_SECONDS = 5

# Time (in minutes) after which failed attempts counter resets automatically
FAILED_ATTEMPTS_RESET_MINUTES = 1

# =============================================================================
# FAQ AND SUPPORT ROUTES
# =============================================================================
def parse_database_uri(db_uri):
    """Properly parse PostgreSQL database URI including query parameters"""
    try:
        # Parse the URI using urllib.parse
        parsed = urlparse(db_uri)
        
        return {
            'username': parsed.username,
            'password': parsed.password,
            'host': parsed.hostname,
            'port': parsed.port or 5432,
            'database': parsed.path.lstrip('/'),
            'query_params': parse_qs(parsed.query)
        }
    except Exception as e:
        print(f"Error parsing database URI: {e}")
        return None

def is_sqlite_database():
    """Return True when the app is using the local SQLite database."""
    return DatabaseConfig.is_sqlite_uri(app.config['SQLALCHEMY_DATABASE_URI'])

def get_sqlite_database_path():
    """Return the filesystem path for the configured SQLite database."""
    db_uri = app.config['SQLALCHEMY_DATABASE_URI']
    if not db_uri.startswith('sqlite:///'):
        return None
    return os.path.normpath(db_uri.replace('sqlite:///', '', 1))

def create_sqlite_backup(backup_path):
    """Create a file copy backup of the local SQLite database."""
    sqlite_path = get_sqlite_database_path()
    if not sqlite_path or not os.path.exists(sqlite_path):
        raise Exception("Local SQLite database file was not found")

    db.session.close()
    db.engine.dispose()
    shutil.copy2(sqlite_path, backup_path)

def restore_sqlite_backup(backup_path):
    """Restore the local SQLite database from a file backup."""
    sqlite_path = get_sqlite_database_path()
    if not sqlite_path:
        raise Exception("Local SQLite database path is not configured")

    os.makedirs(os.path.dirname(sqlite_path), exist_ok=True)
    db.session.close()
    db.engine.dispose()
    shutil.copy2(backup_path, sqlite_path)

@app.route('/faq')
def faq():
    """Render the FAQ page with developer contact information"""
    try:
        log_user_action(
            session.get('user_id'),
            'View FAQ Page',
            f'User accessed FAQ and support page'
        )
        
        return render_template('faq.html')
    
    except Exception as e:
        print(f"Error in FAQ route: {e}")
        return f"Error loading FAQ page: {e}", 500

@app.route('/download_user_manual')
def download_user_manual():
    """Download the user manual PDF"""
    try:
        manual_path = os.path.join(app.template_folder, 'User Manual.pdf')
        
        alternative_paths = [
            os.path.join(os.getcwd(), 'User Manual.pdf'),
            os.path.join(app.static_folder, 'User Manual.pdf'),
            os.path.join('templates', 'User Manual.pdf'),
        ]
        
        if not os.path.exists(manual_path):
            print(f"Manual not found in templates folder: {manual_path}")
            
            found_path = None
            for alt_path in alternative_paths:
                if os.path.exists(alt_path):
                    manual_path = alt_path
                    found_path = alt_path
                    print(f"Found manual at: {found_path}")
                    break
            
            if not found_path:
                print("Manual not found in any location")
                return "User manual not found. Please contact the administrator.", 404
        
        log_user_action(
            session.get('user_id'),
            'Download User Manual',
            f'User downloaded the user manual PDF from: {manual_path}'
        )
        
        return send_file(
            manual_path,
            as_attachment=True,
            download_name='Pullan_Dental_Clinic_User_Manual.pdf',
            mimetype='application/pdf'
        )
    
    except Exception as e:
        print(f"Error downloading user manual: {e}")
        return f"Error downloading user manual: {e}", 500
    
def hash_password(password):
    """Hash a password using SHA-256"""
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def verify_password(password, hashed_password):
    """Verify a password against its SHA-256 hash"""
    return hash_password(password) == hashed_password

def validate_password(password):
    """Validate password meets security requirements"""
    import re
    
    if len(password) < 7:
        return False, "Password must be at least 7 characters long"
    
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number"
    
    return True, "Password is valid"

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

def get_failed_attempts_info():
    """Get current failed attempts information"""
    return {
        'failed_attempts': session.get('failed_attempts', 0),
        'max_attempts': MAX_FAILED_ATTEMPTS,
        'attempts_remaining': MAX_FAILED_ATTEMPTS - session.get('failed_attempts', 0),
        'first_attempt_time': session.get('first_failed_attempt_time'),
        'auto_reset_enabled': FAILED_ATTEMPTS_RESET_MINUTES > 0,
        'auto_reset_minutes': FAILED_ATTEMPTS_RESET_MINUTES
    }

def reset_failed_attempts(user_id=None, reason="Manual Reset"):
    """Reset failed attempts counter"""
    session['failed_attempts'] = 0
    session['first_failed_attempt_time'] = None
    
    if user_id:
        log_user_action(user_id, 'Reset Failed Attempts', reason)

@app.route('/')
def index():
    """Redirect to the login page"""
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Initialize failed attempts counter if it doesn't exist
        if 'failed_attempts' not in session:
            session['failed_attempts'] = 0
            session['first_failed_attempt_time'] = None

        # Check if auto-reset time has passed (if configured)
        if (FAILED_ATTEMPTS_RESET_MINUTES > 0 and 
            session.get('first_failed_attempt_time') and 
            session['failed_attempts'] > 0):
            
            time_since_first_attempt = (datetime.now() - 
                datetime.strptime(session['first_failed_attempt_time'], '%Y-%m-%d %H:%M:%S')).total_seconds() / 60
            
            if time_since_first_attempt >= FAILED_ATTEMPTS_RESET_MINUTES:
                session['failed_attempts'] = 0
                session['first_failed_attempt_time'] = None
                log_user_action(
                    0,
                    'Failed Attempts Auto-Reset',
                    f'Failed login attempts auto-reset after {FAILED_ATTEMPTS_RESET_MINUTES} minutes'
                )
        
        # Check if user has exceeded maximum attempts
        if session['failed_attempts'] >= MAX_FAILED_ATTEMPTS:
            log_user_action(
                0,
                'Login Blocked',
                f'Login blocked for username: {username} - Too many failed attempts ({session["failed_attempts"]}/{MAX_FAILED_ATTEMPTS})'
            )
            
            session['failed_attempts'] = 0
            session['first_failed_attempt_time'] = None
            return redirect(url_for('forgot_password', reason='too_many_attempts', username=username))

        # Check for hardcoded admin account FIRST
        if username == 'admin' and password == 'login':
            session['failed_attempts'] = 0
            session['first_failed_attempt_time'] = None
            
            session['user_id'] = 0
            session['username'] = 'admin'
            session['access_level'] = 'admin'
            session['real_name'] = 'System Administrator'
            
            log_user_action(0, 'Login', 'Hardcoded admin logged in successfully')
            
            return redirect(url_for('dashboard'))

        # Check credentials against database with SHA-256 verification
        user = User.query.filter_by(usersusername=username).first()
        
        if user and verify_password(password, user.userspassword):
            session['failed_attempts'] = 0
            session['first_failed_attempt_time'] = None
            
            session['user_id'] = user.usersid
            session['username'] = user.usersusername
            session['access_level'] = user.usersaccess
            session['real_name'] = user.usersrealname
            
            log_user_action(user.usersid, 'Login', f'User {username} logged in successfully')
            
            return redirect(url_for('dashboard'))
        
        # Increment failed attempts counter
        session['failed_attempts'] += 1
        
        if session['failed_attempts'] == 1:
            session['first_failed_attempt_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        attempts_remaining = MAX_FAILED_ATTEMPTS - session['failed_attempts']
        
        log_user_action(
            0,
            'Failed Login',
            f'Failed login attempt for username: {username} (Attempt {session["failed_attempts"]}/{MAX_FAILED_ATTEMPTS})'
        )
        
        if attempts_remaining > 0:
            error_message = f"Invalid username or password. {attempts_remaining} attempt(s) remaining."
        else:
            error_message = "Too many failed attempts. Redirecting to password reset..."
        
        return render_template('login.html', 
                              error=error_message,
                              failed_attempts=session['failed_attempts'],
                              attempts_remaining=attempts_remaining,
                              max_attempts=MAX_FAILED_ATTEMPTS,
                              redirect_countdown=REDIRECT_COUNTDOWN_SECONDS)

    registration_success = request.args.get('registration_success')
    
    reason = request.args.get('reason')
    redirect_message = None
    if reason == 'too_many_attempts':
        redirect_message = f"You have been redirected here due to {MAX_FAILED_ATTEMPTS} failed login attempts. Please reset your password."
    
    if 'failed_attempts' not in session:
        session['failed_attempts'] = 0
        session['first_failed_attempt_time'] = None

    attempts_remaining = MAX_FAILED_ATTEMPTS - session.get('failed_attempts', 0)
    return render_template('login.html', 
                          registration_success=registration_success,
                          redirect_message=redirect_message,
                          failed_attempts=session.get('failed_attempts', 0),
                          max_attempts=MAX_FAILED_ATTEMPTS,
                          redirect_countdown=REDIRECT_COUNTDOWN_SECONDS)

@app.route('/dashboard')
def dashboard():
    """Dashboard with real data from database"""
    try:
        today = datetime.now().date()
        current_month_start = today.replace(day=1)
        last_month_start = (current_month_start - timedelta(days=1)).replace(day=1)
        last_month_end = current_month_start - timedelta(days=1)
        
        yesterday = today - timedelta(days=1)
        
        # 1. PATIENT STATISTICS
        total_patients = Patient.query.filter_by(is_deleted=False).count()
        patient_growth = 12  # Default positive growth
        
        # 2. TODAY'S APPOINTMENTS
        todays_appointments = Appointment.query.filter_by(appdate=today).all()
        todays_appointment_count = len(todays_appointments)
        
        yesterday_appointments = Appointment.query.filter_by(appdate=yesterday).count()
        appointment_growth = 0
        if yesterday_appointments > 0:
            appointment_growth = ((todays_appointment_count - yesterday_appointments) / yesterday_appointments) * 100
        elif todays_appointment_count > 0:
            appointment_growth = 100
        
        # 3. FORMAT TODAY'S APPOINTMENTS FOR TABLE
        formatted_appointments = []
        for appointment in todays_appointments:
            patient = Patient.query.filter_by(patname=appointment.apppatient).first()
            patient_id = f"PAT-{patient.patId:03d}" if patient else "N/A"
            
            appointment_time = appointment.apptime
            current_time = datetime.now().time()
            
            if appointment_time:
                try:
                    apt_start_minutes, _ = _appointment_time_bounds(appointment_time)
                    apt_time_obj = datetime.strptime(_minutes_to_time(apt_start_minutes), '%H:%M').time()
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
                'status': status,
                'raw_id': appointment.appid,
                'patient_phone': patient.patcontact if patient else "N/A"
            })
        
        formatted_appointments.sort(key=lambda x: x['time'] if x['time'] != "N/A" else "00:00")
        
        # 4. ALL PATIENTS WITH COMPLETED APPOINTMENTS
        completed_appointments = Appointment.query.filter(Appointment.appdate < today).all()
        
        if hasattr(Appointment, 'status'):
            completed_status_appointments = Appointment.query.filter_by(status='completed').all()
            all_completed = list({apt.appid: apt for apt in (completed_appointments + completed_status_appointments)}.values())
        else:
            all_completed = completed_appointments
        
        patient_latest_appointments = {}
        for appointment in all_completed:
            patient_name = appointment.apppatient
            if patient_name not in patient_latest_appointments:
                patient_latest_appointments[patient_name] = appointment
            else:
                if appointment.appdate > patient_latest_appointments[patient_name].appdate:
                    patient_latest_appointments[patient_name] = appointment
        
        recent_patients = []
        for patient_name, latest_appointment in patient_latest_appointments.items():
            patient = Patient.query.filter_by(patname=patient_name, is_deleted=False).first()
            if patient:
                latest_procedure = Report.query.filter_by(reppatient=patient_name).order_by(Report.repdate.desc()).first()
                
                treatment = "General Visit"
                if latest_procedure:
                    procedures_done = []
                    if latest_procedure.repcleaning: procedures_done.append("Cleaning")
                    if latest_procedure.repextraction: procedures_done.append("Extraction")
                    if latest_procedure.reprootcanal: procedures_done.append("Root Canal")
                    if latest_procedure.repbraces: procedures_done.append("Braces")
                    if latest_procedure.repdentures: procedures_done.append("Dentures")
                    if latest_procedure.repothers: procedures_done.append(latest_procedure.repothers)
                    
                    if procedures_done:
                        treatment = ", ".join(procedures_done)
                
                recent_patients.append({
                    'id': f"PAT-{patient.patId:03d}",
                    'name': patient.patname,
                    'last_visit': latest_appointment.appdate.strftime('%b %d, %Y'),
                    'treatment': treatment,
                    'appointment_time': latest_appointment.apptime or "N/A",
                    'raw_id': patient.patId
                })
        
        recent_patients.sort(key=lambda x: datetime.strptime(x['last_visit'], '%b %d, %Y'), reverse=True)
        
        # 5. GET APPOINTMENT DATES FOR CALENDAR MARKING
        current_month = today.replace(day=1)
        if today.month == 12:
            next_month = today.replace(year=today.year + 1, month=1, day=1)
        else:
            next_month = today.replace(month=today.month + 1, day=1)
        
        monthly_appointments = Appointment.query.filter(
            Appointment.appdate >= current_month,
            Appointment.appdate < next_month
        ).all()
        
        appointment_dates = []
        for appointment in monthly_appointments:
            if appointment.appdate:
                appointment_dates.append(appointment.appdate.day)
        
        appointment_dates = sorted(list(set(appointment_dates)))
        
        # 6. INVENTORY ALERTS
        low_stock_items = Inventory.query.filter(Inventory.invquantity < 5).count()
        expired_items = Inventory.query.filter(
            Inventory.invdoe.isnot(None),
            Inventory.invdoe < today
        ).count()
        
        dashboard_data = {
            'stats': {
                'total_patients': total_patients,
                'patient_growth': patient_growth,
                'todays_appointments': todays_appointment_count,
                'appointment_growth': appointment_growth
            },
            'appointments': formatted_appointments,
            'recent_patients': recent_patients,
            'appointment_dates': appointment_dates,
            'alerts': {
                'low_stock': low_stock_items,
                'expired_items': expired_items
            },
            'current_date': datetime.now().strftime("%A, %B %d, %Y"),
            'total_completed_patients': len(recent_patients)
        }
        
        return render_template('dashboard.html', **dashboard_data)
        
    except Exception as e:
        print(f"Error in dashboard route: {e}")
        return render_template('dashboard.html', 
                             stats={
                                 'total_patients': 0, 
                                 'patient_growth': 0,
                                 'todays_appointments': 0, 
                                 'appointment_growth': 0
                             },
                             appointments=[], 
                             recent_patients=[], 
                             appointment_dates=[],
                             alerts={'low_stock': 0, 'expired_items': 0},
                             current_date=datetime.now().strftime("%A, %B %d, %Y"),
                             total_completed_patients=0,
                             error=f"Dashboard error: {e}")

@app.route('/logout')
def logout():
    """Log out the current user"""
    user_id = session.get('user_id')
    username = session.get('username')
    
    if user_id is not None:
        if user_id == 0:
            log_user_action(0, 'Logout', 'Hardcoded admin logged out')
        else:
            log_user_action(user_id, 'Logout', f'User {username} logged out')
    
    session.clear()
    return redirect(url_for('login'))

# USER LOGS ROUTES - ADMIN ONLY
@app.route('/user_logs')
@admin_required
def user_logs():
    """Display user activity logs - Admin only"""
    try:
        user_id = request.args.get('user_id')
        action = request.args.get('action')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        page = int(request.args.get('page', 1))
        per_page = 50
        
        query = db.session.query(
            UserLog.log_id,
            UserLog.user_id,
            UserLog.action,
            UserLog.timestamp,
            UserLog.details,
            User.usersrealname.label('user_name'),
            User.usersusername.label('username')
        ).outerjoin(User, UserLog.user_id == User.usersid)
        
        if user_id:
            query = query.filter(UserLog.user_id == user_id)
        if action:
            query = query.filter(UserLog.action == action)
        if date_from:
            query = query.filter(UserLog.timestamp >= datetime.strptime(date_from, '%Y-%m-%d'))
        if date_to:
            query = query.filter(UserLog.timestamp <= datetime.strptime(date_to + ' 23:59:59', '%Y-%m-%d %H:%M:%S'))
        
        query = query.order_by(UserLog.timestamp.desc())
        
        total_logs = query.count()
        
        logs = query.offset((page - 1) * per_page).limit(per_page).all()
        
        formatted_logs = []
        for log in logs:
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
        
        total_pages = (total_logs + per_page - 1) // per_page
        
        total_logs_count = UserLog.query.count()
        active_users = db.session.query(UserLog.user_id).distinct().count()
        
        all_users = User.query.order_by(User.usersrealname).all()
        
        return render_template('user_logs.html',
                               logs=formatted_logs,
                               total_logs=total_logs_count,
                               active_users=active_users,
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
        user_id = request.args.get('user_id')
        action = request.args.get('action')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        
        query = db.session.query(
            UserLog.log_id,
            UserLog.user_id,
            UserLog.action,
            UserLog.timestamp,
            UserLog.details,
            User.usersrealname.label('user_name'),
            User.usersusername.label('username')
        ).outerjoin(User, UserLog.user_id == User.usersid)
        
        if user_id:
            query = query.filter(UserLog.user_id == user_id)
        if action:
            query = query.filter(UserLog.action == action)
        if date_from:
            query = query.filter(UserLog.timestamp >= datetime.strptime(date_from, '%Y-%m-%d'))
        if date_to:
            query = query.filter(UserLog.timestamp <= datetime.strptime(date_to + ' 23:59:59', '%Y-%m-%d %H:%M:%S'))
        
        logs = query.order_by(UserLog.timestamp.desc()).all()
        
        output = StringIO()
        writer = csv.writer(output)
        
        writer.writerow(['Log ID', 'User ID', 'User Name', 'Username', 'Action', 'Timestamp', 'Details'])
        
        for log in logs:
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
        
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename=user_logs_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        
        log_user_action(session.get('user_id'), 'Export Logs', f'User exported {len(logs)} log entries')
        
        return response
    
    except Exception as e:
        print(f"Error exporting logs: {e}")
        return jsonify({"success": False, "error": str(e)})

# Patient Routes (keeping existing code, just showing a few key ones)
@app.route('/patients')
def patients():
    """Render the patients page with data from the database"""
    try:
        status_filter = request.args.get('status', 'active')
        
        if status_filter == 'active':
            patients_list = Patient.query.filter_by(is_deleted=False).all()
        elif status_filter == 'inactive':
            patients_list = Patient.query.filter_by(is_deleted=True).all()
        else:
            patients_list = Patient.query.all()
        
        print(f"Found {len(patients_list)} patients with status: {status_filter}")
        
        formatted_patients = []
        for patient in patients_list:
            last_visit = "N/A"
            
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
                'raw_id': patient.patId
            })
        
        current_date = datetime.now().strftime("%A, %B %d, %Y")
        
        active_count = Patient.query.filter_by(is_deleted=False).count()
        inactive_count = Patient.query.filter_by(is_deleted=True).count()
        total_count = active_count + inactive_count
        
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

def create_postgresql_backup(username, password, host, database_name, backup_path, port=5432):
    """Create a PostgreSQL database backup using pg_dump - IMPROVED VERSION"""
    try:
        # Set password environment variable for pg_dump
        env = os.environ.copy()
        env['PGPASSWORD'] = password
        
        print(f"Creating backup with pg_dump - Database: {database_name}")
        
        # Use pg_dump command with improved options
        cmd = [
            'pg_dump',
            f'--host={host}',
            f'--port={port}',
            f'--username={username}',
            f'--dbname={database_name}',
            '--verbose',
            '--clean',                    # Add DROP statements
            '--if-exists',               # Use IF EXISTS with DROP
            '--create',                  # Include CREATE DATABASE statement
            '--format=plain',            # Plain SQL format
            '--no-owner',               # Don't include ownership commands
            '--no-privileges',          # Don't include privilege commands
            '--schema=pullandentalclinic',  # Only backup our schema
            f'--file={backup_path}'
        ]
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env
        )
        
        stdout, stderr = process.communicate()
        
        if process.returncode != 0:
            # If schema-specific backup fails, try full database backup
            print("Schema-specific backup failed, trying full database backup...")
            cmd_fallback = [
                'pg_dump',
                f'--host={host}',
                f'--port={port}',
                f'--username={username}',
                f'--dbname={database_name}',
                '--verbose',
                '--clean',
                '--if-exists',
                '--create',
                '--format=plain',
                '--no-owner',
                '--no-privileges',
                f'--file={backup_path}'
            ]
            
            process = subprocess.Popen(
                cmd_fallback,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env
            )
            
            stdout, stderr = process.communicate()
            
            if process.returncode != 0:
                error_output = stderr.decode('utf-8')
                print(f"pg_dump stderr: {error_output}")
                raise Exception(f"pg_dump failed: {error_output}")
        
        # Post-process the backup file to fix schema issues
        fix_backup_file(backup_path, database_name)
        
        print(f"PostgreSQL backup completed successfully: {backup_path}")
        
    except Exception as e:
        raise Exception(f"PostgreSQL backup failed: {str(e)}")
    
def fix_backup_file(backup_path, database_name):
    """Post-process backup file to ensure proper restore"""
    try:
        with open(backup_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Add proper database connection and schema setup
        header = f"""--
-- PostgreSQL database dump for {database_name}
-- Fixed for proper restore
--

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

-- Connect to the target database
\\connect {database_name}

-- Create schema if not exists
CREATE SCHEMA IF NOT EXISTS pullandentalclinic;

-- Set search path
SET search_path = pullandentalclinic, public;

"""
        
        # Add footer to reset search path
        footer = """
-- Reset search path
SET search_path = pullandentalclinic, public;

-- End of dump
"""
        
        # Combine header, content, and footer
        fixed_content = header + content + footer
        
        # Write fixed content back to file
        with open(backup_path, 'w', encoding='utf-8') as file:
            file.write(fixed_content)
            
        print(f"Backup file fixed: {backup_path}")
        
    except Exception as e:
        print(f"Warning: Could not fix backup file: {e}")


def restore_postgresql_backup(username, password, host, backup_path, port=5432):
    """Restore a PostgreSQL database backup using psql - IMPROVED VERSION"""
    try:
        # Set password environment variable for psql
        env = os.environ.copy()
        env['PGPASSWORD'] = password
        
        print(f"Restoring backup from: {backup_path}")
        
        # Parse database name from backup file
        db_config = parse_database_uri(app.config['SQLALCHEMY_DATABASE_URI'])
        target_database = db_config['database'] if db_config else 'pullan_dental_db'
        
        # Step 1: Connect to postgres database and run the restore
        cmd = [
            'psql',
            f'--host={host}',
            f'--port={port}',
            f'--username={username}',
            '--dbname=postgres',  # Connect to postgres first
            '--quiet',
            f'--file={backup_path}'
        ]
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env
        )
        
        stdout, stderr = process.communicate()
        
        # Check if restore had any critical errors
        stderr_text = stderr.decode('utf-8')
        if process.returncode != 0 and 'FATAL' in stderr_text:
            print(f"psql stderr: {stderr_text}")
            raise Exception(f"psql restore failed: {stderr_text}")
        
        # Step 2: Verify the restore by connecting to target database
        verify_cmd = [
            'psql',
            f'--host={host}',
            f'--port={port}',
            f'--username={username}',
            f'--dbname={target_database}',
            '--command=SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = \'pullandentalclinic\';'
        ]
        
        verify_process = subprocess.Popen(
            verify_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env
        )
        
        verify_stdout, verify_stderr = verify_process.communicate()
        
        if verify_process.returncode == 0:
            print(f"PostgreSQL restore completed successfully from: {backup_path}")
            print("Database verification: Tables restored successfully")
        else:
            print(f"Restore completed but verification failed: {verify_stderr.decode('utf-8')}")
        
        # Step 3: Update Flask app database connection to refresh schema
        refresh_database_connection()
        
    except Exception as e:
        raise Exception(f"PostgreSQL restore failed: {str(e)}")
    
def refresh_database_connection():
    """Refresh the database connection after restore - FIXED VERSION"""
    try:
        # Close existing connections
        db.session.close()
        db.engine.dispose()
        
        # Recreate engine with fresh connection
        with app.app_context():
            # Test connection with proper SQLAlchemy syntax
            try:
                # For newer SQLAlchemy versions (2.x)
                result = db.session.execute(text("SELECT 1"))
                row = result.fetchone()
                if row and row[0] == 1:
                    print("Database connection refreshed successfully (SQLAlchemy 2.x)")
                else:
                    print("Warning: Database connection refresh may have failed")
            except AttributeError:
                # Fallback for older SQLAlchemy versions (1.x)
                try:
                    result = db.engine.execute(text("SELECT 1"))
                    row = result.fetchone()
                    if row and row[0] == 1:
                        print("Database connection refreshed successfully (SQLAlchemy 1.x)")
                    else:
                        print("Warning: Database connection refresh may have failed")
                except Exception as fallback_error:
                    print(f"Warning: Could not refresh database connection: {fallback_error}")
                
    except Exception as e:
        print(f"Warning: Could not refresh database connection: {e}")



def create_direct_postgresql_backup(username, password, host, database_name, backup_path, port=5432):
    """Create a PostgreSQL database backup directly using psycopg2 with fixed connection"""
    connection = None
    try:
        print(f"Creating direct backup - Database: {database_name}")
        
        # Connect to the database with improved error handling
        try:
            connection = psycopg2.connect(
                host=host,
                user=username,
                password=password,
                database=database_name,
                port=port,
                connect_timeout=10
            )
            print(f"Successfully connected to PostgreSQL at {host}:{port}")
        except psycopg2.OperationalError as e:
            error_str = str(e)
            if "Connection refused" in error_str:
                raise Exception(f"Cannot connect to PostgreSQL server at {host}:{port}. Is PostgreSQL running? Error: {e}")
            elif "authentication failed" in error_str:
                raise Exception(f"Access denied. Please check your username and password. Error: {e}")
            elif "does not exist" in error_str:
                raise Exception(f"Database '{database_name}' does not exist. Error: {e}")
            else:
                raise Exception(f"Database connection failed: {e}")
        
        with open(backup_path, 'w', encoding='utf8') as f:
            # Write backup header with metadata
            f.write(f"-- Database Backup for: {database_name}\n")
            f.write(f"-- Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("-- By: Pullan Dental Clinic Management System\n")
            f.write(f"-- PostgreSQL Version: {connection.server_version}\n")
            f.write(f"-- Host: {host}:{port}\n\n")
            
            f.write("SET statement_timeout = 0;\n")
            f.write("SET lock_timeout = 0;\n")
            f.write("SET idle_in_transaction_session_timeout = 0;\n")
            f.write("SET client_encoding = 'UTF8';\n")
            f.write("SET standard_conforming_strings = on;\n")
            f.write("SET check_function_bodies = false;\n")
            f.write("SET xmloption = content;\n")
            f.write("SET client_min_messages = warning;\n\n")
            
            # Add DROP DATABASE and CREATE DATABASE statements
            f.write(f"DROP DATABASE IF EXISTS {database_name};\n")
            f.write(f"CREATE DATABASE {database_name} WITH TEMPLATE = template0 ENCODING = 'UTF8';\n")
            f.write(f"\\connect {database_name};\n\n")
            
            # Set search path for schema
            f.write("SET search_path = pullandentalclinic, public;\n\n")
            
            # Get all tables from the pullandentalclinic schema
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT tablename FROM pg_tables 
                    WHERE schemaname = 'pullandentalclinic'
                    ORDER BY tablename
                """)
                tables = cursor.fetchall()
                
                if not tables:
                    f.write("-- No tables found in pullandentalclinic schema\n")
                    # Try public schema as fallback
                    cursor.execute("""
                        SELECT tablename FROM pg_tables 
                        WHERE schemaname = 'public'
                        ORDER BY tablename
                    """)
                    tables = cursor.fetchall()
                    if tables:
                        f.write("-- Using tables from public schema as fallback\n")
                
                # For each table, get CREATE TABLE statement and data
                for table_tuple in tables:
                    table_name = table_tuple[0]
                    
                    try:
                        # Get table schema
                        cursor.execute(f"""
                            SELECT column_name, data_type, is_nullable, column_default
                            FROM information_schema.columns
                            WHERE table_name = '{table_name}'
                            AND table_schema IN ('pullandentalclinic', 'public')
                            ORDER BY ordinal_position
                        """)
                        columns = cursor.fetchall()
                        
                        if not columns:
                            continue
                        
                        # Write the DROP TABLE and CREATE TABLE statements
                        f.write(f"-- Table structure for table {table_name}\n")
                        f.write(f"DROP TABLE IF EXISTS pullandentalclinic.{table_name};\n")
                        
                        # Create table statement (simplified)
                        f.write(f"CREATE TABLE pullandentalclinic.{table_name} (\n")
                        col_definitions = []
                        for col in columns:
                            col_name, data_type, is_nullable, default = col
                            col_def = f"    {col_name} {data_type}"
                            if is_nullable == 'NO':
                                col_def += " NOT NULL"
                            if default:
                                col_def += f" DEFAULT {default}"
                            col_definitions.append(col_def)
                        f.write(",\n".join(col_definitions))
                        f.write("\n);\n\n")
                        
                        # Get table data
                        cursor.execute(f"SELECT COUNT(*) FROM pullandentalclinic.{table_name}")
                        row_count = cursor.fetchone()[0]
                        
                        if row_count > 0:
                            f.write(f"-- Dumping data for table {table_name} ({row_count} rows)\n")
                            
                            cursor.execute(f"SELECT * FROM pullandentalclinic.{table_name}")
                            rows = cursor.fetchall()
                            
                            if rows:
                                # Get column names
                                column_names = [desc[0] for desc in cursor.description]
                                
                                # Write INSERT statements in batches
                                batch_size = 100
                                for i in range(0, len(rows), batch_size):
                                    batch = rows[i:i+batch_size]
                                    
                                    # Generate INSERT statement header
                                    insert_header = f"INSERT INTO pullandentalclinic.{table_name} ({', '.join(column_names)}) VALUES\n"
                                    f.write(insert_header)
                                    
                                    # Generate values for each row
                                    values_list = []
                                    for row in batch:
                                        values = []
                                        for value in row:
                                            if value is None:
                                                values.append("NULL")
                                            elif isinstance(value, (int, float)):
                                                values.append(str(value))
                                            elif isinstance(value, (datetime, date)):
                                                values.append(f"'{value}'")
                                            elif isinstance(value, bool):
                                                values.append("TRUE" if value else "FALSE")
                                            else:
                                                # Escape string values
                                                escaped_value = str(value).replace("'", "''")
                                                values.append(f"'{escaped_value}'")
                                                    
                                        values_list.append(f"({', '.join(values)})")
                                    
                                    # Write values with commas and semicolon
                                    f.write(',\n'.join(values_list))
                                    f.write(';\n\n')
                        else:
                            f.write(f"-- No data for table {table_name}\n\n")
                            
                    except Exception as table_error:
                        f.write(f"-- Error backing up table {table_name}: {str(table_error)}\n\n")
                        print(f"Error backing up table {table_name}: {table_error}")
                        continue
            
            f.write(f"-- Backup completed on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            
        print(f"PostgreSQL backup completed successfully: {backup_path}")
        
    except Exception as e:
        raise Exception(f"Direct PostgreSQL backup failed: {str(e)}")
    finally:
        if connection:
            connection.close()

@app.route('/backup_restore')
@admin_required
def backup_restore():
    """Render the backup and restore page - Admin only"""
    try:
        backups = []
        if os.path.exists(BACKUP_DIRECTORY):
            backup_files = [
                f for f in os.listdir(BACKUP_DIRECTORY)
                if f.endswith(('.sql', '.sqlite', '.db'))
            ]
            for backup_file in backup_files:
                try:
                    timestamp_str = backup_file.split('_')[1].split('.')[0]
                    backup_time = datetime.strptime(timestamp_str, '%Y%m%d%H%M%S')
                    
                    file_path = os.path.join(BACKUP_DIRECTORY, backup_file)
                    file_size = os.path.getsize(file_path) / (1024 * 1024)
                    
                    backups.append({
                        'filename': backup_file,
                        'timestamp': backup_time.strftime('%Y-%m-%d %H:%M:%S'),
                        'size': f"{file_size:.2f} MB"
                    })
                except Exception as e:
                    print(f"Error processing backup file {backup_file}: {e}")
                    continue
                    
            backups.sort(key=lambda x: x['timestamp'], reverse=True)
        
        current_date = datetime.now().strftime("%A, %B %d, %Y")
        
        return render_template('backup_restore.html', 
                              backups=backups,
                              current_date=current_date)
    except Exception as e:
        print(f"Error in backup_restore route: {e}")
        return f"Error loading backup page: {e}", 500

@app.route('/create_backup', methods=['POST'])
@admin_required
def create_backup():
    """Create a backup of the PostgreSQL database with improved error handling"""
    try:
        if session.get('access_level') != 'admin':
            return jsonify({"success": False, "error": "You don't have permission to perform this action"})
        
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')

        if is_sqlite_database():
            backup_filename = f"backup_{timestamp}.sqlite"
            backup_path = os.path.join(BACKUP_DIRECTORY, backup_filename)

            try:
                create_sqlite_backup(backup_path)
                file_size = os.path.getsize(backup_path) / (1024 * 1024)

                log_user_action(
                    session.get('user_id'),
                    'Database Backup',
                    f'Created local SQLite database backup: {backup_filename} ({file_size:.2f} MB)'
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
                    "error": f"Error creating local database backup: {str(e)}"
                })

        backup_filename = f"backup_{timestamp}.sql"
        backup_path = os.path.join(BACKUP_DIRECTORY, backup_filename)
        
        # Get database credentials from app config with proper URI parsing
        db_uri = app.config['SQLALCHEMY_DATABASE_URI']
        
        # Parse the PostgreSQL URI properly
        db_config = parse_database_uri(db_uri)
        if not db_config:
            return jsonify({"success": False, "error": "Failed to parse database URI"})
            
        username = db_config['username']
        password = db_config['password']
        host = db_config['host']
        port = db_config['port']
        database = db_config['database']
        
        print(f"Backup Config - Host: {host}, Port: {port}, Database: {database}, User: {username}")
        
        # Resolve host DNS issues
        resolved_host = resolve_host(host)
        
        # Test the connection first
        try:
            connection = psycopg2.connect(
                host=resolved_host,
                user=username,
                password=password,
                database=database,
                port=port,
                connect_timeout=10
            )
            connection.close()
            print("PostgreSQL connection successful for backup")
        except Exception as e:
            error_msg = str(e)
            if "does not exist" in error_msg:
                return jsonify({
                    "success": False, 
                    "error": f"Database '{database}' does not exist. Please check your database configuration."
                })
            else:
                return jsonify({
                    "success": False, 
                    "error": f"Cannot connect to PostgreSQL server: {error_msg}. Please check that your PostgreSQL server is running."
                })
            
        try:
            # Try external pg_dump first
            try:
                create_postgresql_backup(username, password, resolved_host, database, backup_path, port)
            except Exception as pg_dump_error:
                print(f"pg_dump failed: {pg_dump_error}")
                print("Falling back to direct backup method...")
                create_direct_postgresql_backup(username, password, resolved_host, database, backup_path, port)
            
            file_size = os.path.getsize(backup_path) / (1024 * 1024)
            
            log_user_action(
                session.get('user_id'),
                'Database Backup',
                f'Created PostgreSQL database backup: {backup_filename} ({file_size:.2f} MB)'
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

def restore_direct_postgresql_backup(username, password, host, backup_path, port=5432):
    """Direct restore using psycopg2 - Windows fallback method - FIXED VERSION"""
    connection = None
    try:
        print(f"Starting direct restore from: {backup_path}")
        
        # Read the backup file
        with open(backup_path, 'r', encoding='utf-8') as file:
            sql_content = file.read()
        
        if not sql_content.strip():
            raise Exception("Backup file is empty")
        
        print(f"Backup file size: {len(sql_content)} characters")
        
        # Parse database name from the backup content or use config
        db_config = parse_database_uri(app.config['SQLALCHEMY_DATABASE_URI'])
        target_database = db_config['database'] if db_config else 'pullan_dental_db'
        
        # Connect to the target database
        try:
            connection = psycopg2.connect(
                host=host,
                user=username,
                password=password,
                database=target_database,
                port=port,
                connect_timeout=30
            )
            connection.autocommit = True  # Important for DDL operations
            print(f"Connected to database: {target_database}")
        except psycopg2.OperationalError as e:
            # If target database doesn't exist, connect to postgres and create it
            if "does not exist" in str(e):
                print(f"Database {target_database} doesn't exist, connecting to postgres...")
                connection = psycopg2.connect(
                    host=host,
                    user=username,
                    password=password,
                    database='postgres',
                    port=port,
                    connect_timeout=30
                )
                connection.autocommit = True
            else:
                raise e
        
        cursor = connection.cursor()
        
        # STEP 1: Create schema if it doesn't exist
        try:
            cursor.execute("CREATE SCHEMA IF NOT EXISTS pullandentalclinic;")
            print("Created/verified pullandentalclinic schema")
        except Exception as schema_error:
            print(f"Schema creation warning: {schema_error}")
        
        # STEP 2: Set search path
        try:
            cursor.execute("SET search_path = pullandentalclinic, public;")
            print("Set search path to pullandentalclinic, public")
        except Exception as path_error:
            print(f"Search path warning: {path_error}")
        
        # STEP 3: Parse and clean SQL content
        sql_lines = []
        for line in sql_content.split('\n'):
            line = line.strip()
            # Skip comments, empty lines, and problematic statements
            if (line and 
                not line.startswith('--') and 
                not line.startswith('/*') and
                not line.upper().startswith('SET ') and
                not line.upper().startswith('\\CONNECT')):
                sql_lines.append(line)
        
        sql_content = ' '.join(sql_lines)
        
        # STEP 4: Smart SQL statement splitting
        statements = []
        current_statement = ""
        in_quotes = False
        escape_next = False
        
        for char in sql_content:
            if escape_next:
                current_statement += char
                escape_next = False
                continue
                
            if char == '\\':
                escape_next = True
                current_statement += char
                continue
                
            if char == "'" and not escape_next:
                in_quotes = not in_quotes
                
            if char == ';' and not in_quotes:
                if current_statement.strip():
                    statements.append(current_statement.strip())
                current_statement = ""
            else:
                current_statement += char
        
        # Add the last statement if it exists
        if current_statement.strip():
            statements.append(current_statement.strip())
        
        print(f"Executing {len(statements)} SQL statements...")
        
        # STEP 5: Execute statements with enhanced error handling
        successful_statements = 0
        failed_statements = 0
        
        for i, statement in enumerate(statements):
            if not statement.strip():
                continue
                
            try:
                statement_upper = statement.upper().strip()
                
                # Skip certain problematic statements
                skip_patterns = [
                    'CREATE DATABASE',
                    'DROP DATABASE',
                    'ALTER DATABASE',
                    'GRANT ',
                    'REVOKE ',
                    'CREATE ROLE',
                    'ALTER ROLE'
                ]
                
                should_skip = False
                for pattern in skip_patterns:
                    if statement_upper.startswith(pattern):
                        should_skip = True
                        break
                
                if should_skip:
                    continue
                
                # Handle CREATE TABLE statements - ensure they use the schema
                if statement_upper.startswith('CREATE TABLE'):
                    # If table name doesn't have schema prefix, add it
                    if 'pullandentalclinic.' not in statement.lower():
                        # Extract table name and add schema prefix
                        parts = statement.split()
                        for j, part in enumerate(parts):
                            if part.upper() == 'TABLE':
                                if j + 1 < len(parts):
                                    table_name = parts[j + 1]
                                    # Remove any IF NOT EXISTS
                                    if table_name.upper() == 'IF':
                                        table_name = parts[j + 4] if j + 4 < len(parts) else parts[-1]
                                    # Clean table name
                                    table_name = table_name.replace('(', '').replace(',', '')
                                    if '.' not in table_name:
                                        statement = statement.replace(table_name, f'pullandentalclinic.{table_name}', 1)
                                break
                
                # Handle INSERT statements - ensure they use the schema
                elif statement_upper.startswith('INSERT INTO'):
                    if 'pullandentalclinic.' not in statement.lower():
                        # Extract table name and add schema prefix
                        parts = statement.split()
                        for j, part in enumerate(parts):
                            if part.upper() == 'INTO':
                                if j + 1 < len(parts):
                                    table_name = parts[j + 1]
                                    if '.' not in table_name and not table_name.startswith('pullandentalclinic'):
                                        statement = statement.replace(f'INTO {table_name}', f'INTO pullandentalclinic.{table_name}', 1)
                                break
                
                # Execute the statement
                cursor.execute(statement)
                successful_statements += 1
                
                # Progress indicator for large restores
                if i % 50 == 0:
                    print(f"Progress: {i}/{len(statements)} statements processed...")
                    
            except Exception as stmt_error:
                failed_statements += 1
                error_msg = str(stmt_error)
                
                # Only log significant errors
                if not any(skip_word in error_msg.lower() for skip_word in 
                          ['already exists', 'does not exist', 'permission denied', 'duplicate key']):
                    print(f"Warning: Statement {i+1} failed: {error_msg}")
                    print(f"Statement: {statement[:150]}...")
                
                # Continue with other statements
                continue
        
        print(f"Restore completed: {successful_statements} successful, {failed_statements} failed statements")
        
        # STEP 6: Verification and table count
        try:
            # Check pullandentalclinic schema
            cursor.execute("""
                SELECT tablename FROM pg_tables 
                WHERE schemaname = 'pullandentalclinic'
                ORDER BY tablename
            """)
            schema_tables = cursor.fetchall()
            
            if schema_tables:
                print(f"Verification: Found {len(schema_tables)} tables in pullandentalclinic schema:")
                for table in schema_tables:
                    print(f"  - {table[0]}")
            else:
                # Check public schema as fallback
                cursor.execute("""
                    SELECT tablename FROM pg_tables 
                    WHERE schemaname = 'public' 
                    AND tablename IN ('patients', 'appointment', 'users', 'inventory', 'dentalchart', 'teeth', 'report')
                    ORDER BY tablename
                """)
                public_tables = cursor.fetchall()
                
                if public_tables:
                    print(f"Verification: Found {len(public_tables)} key tables in public schema:")
                    for table in public_tables:
                        print(f"  - {table[0]}")
                    
                    # Move tables to pullandentalclinic schema
                    for table in public_tables:
                        table_name = table[0]
                        try:
                            cursor.execute(f"ALTER TABLE public.{table_name} SET SCHEMA pullandentalclinic;")
                            print(f"Moved {table_name} to pullandentalclinic schema")
                        except Exception as move_error:
                            print(f"Could not move {table_name}: {move_error}")
                else:
                    print("Warning: No expected tables found in either schema")
                
        except Exception as verify_error:
            print(f"Verification warning: {verify_error}")
        
        cursor.close()
        print(f"Direct PostgreSQL restore completed successfully from: {backup_path}")
        
    except Exception as e:
        raise Exception(f"Direct PostgreSQL restore failed: {str(e)}")
    finally:
        if connection:
            connection.close()

@app.route('/restore_backup/<filename>', methods=['POST'])
@admin_required
def restore_backup(filename):
    """Restore the database from a backup file - COMPLETE FIXED VERSION"""
    try:
        if session.get('access_level') != 'admin':
            return jsonify({"success": False, "error": "You don't have permission to perform this action"})
            
        backup_path = os.path.join(BACKUP_DIRECTORY, filename)
        
        if not os.path.exists(backup_path):
            return jsonify({"success": False, "error": "Backup file not found"})

        if is_sqlite_database():
            if not filename.endswith(('.sqlite', '.db')):
                return jsonify({
                    "success": False,
                    "error": "This app is using the local SQLite database, so only .sqlite or .db backups can be restored."
                })

            try:
                restore_sqlite_backup(backup_path)
                refresh_database_connection()
                log_user_action(
                    session.get('user_id'),
                    'Database Restore',
                    f'Restored local SQLite database from backup: {filename}'
                )
                return jsonify({
                    "success": True,
                    "message": f"Database restored successfully from backup: {filename}. Please refresh the page to see updated data."
                })
            except Exception as restore_error:
                return jsonify({
                    "success": False,
                    "error": f"Error restoring local database backup: {restore_error}"
                })
        
        # Verify backup file is readable and not empty
        try:
            with open(backup_path, 'r', encoding='utf-8') as f:
                first_line = f.readline()
                if not first_line.strip():
                    return jsonify({"success": False, "error": "Backup file appears to be empty"})
        except Exception as read_error:
            return jsonify({"success": False, "error": f"Cannot read backup file: {read_error}"})
            
        # Get database credentials from app config with proper URI parsing
        db_uri = app.config['SQLALCHEMY_DATABASE_URI']
        
        # Parse the PostgreSQL URI properly
        db_config = parse_database_uri(db_uri)
        if not db_config:
            return jsonify({"success": False, "error": "Failed to parse database URI"})
            
        username = db_config['username']
        password = db_config['password']
        host = db_config['host']
        port = db_config['port']
        
        print(f"Restore Config - Host: {host}, Port: {port}, User: {username}")
        print(f"Backup file: {backup_path}")
        
        # Resolve DNS issues
        resolved_host = resolve_host(host)
        
        # Test database connectivity before attempting restore
        try:
            test_connection = psycopg2.connect(
                host=resolved_host,
                user=username,
                password=password,
                database='postgres',  # Connect to postgres database for testing
                port=port,
                connect_timeout=10
            )
            test_connection.close()
            print("Database connectivity test successful")
        except Exception as conn_error:
            return jsonify({
                "success": False, 
                "error": f"Cannot connect to database server: {conn_error}"
            })

        # Try restore methods in order of preference
        restore_successful = False
        last_error = None
        
        # Method 1: Try external psql command (standard method)
        try:
            print("Attempting restore using external psql command...")
            restore_postgresql_backup(username, password, resolved_host, backup_path, port)
            restore_successful = True
            print("External psql restore completed successfully")
            
        except Exception as psql_error:
            last_error = str(psql_error)
            print(f"External psql restore failed: {psql_error}")
            
            # Method 2: Try direct restore method (Windows fallback)
            try:
                print("Attempting direct restore method (Windows fallback)...")
                restore_direct_postgresql_backup(username, password, resolved_host, backup_path, port)
                restore_successful = True
                print("Direct restore method completed successfully")
                
            except Exception as direct_error:
                last_error = str(direct_error)
                print(f"Direct restore method also failed: {direct_error}")
        
        if not restore_successful:
            return jsonify({
                "success": False, 
                "error": f"All restore methods failed. Last error: {last_error}"
            })
        
        # Test database after restore
        try:
            test_success, test_message = test_database_after_restore()
            print(f"Post-restore test result: {test_success}, message: {test_message}")
        except Exception as test_error:
            print(f"Post-restore test error: {test_error}")
        
        # Log the restore action (with error handling for missing tables)
        try:
            log_user_action(
                session.get('user_id'),
                'Database Restore',
                f'Restored PostgreSQL database from backup: {filename} (Method: {"External psql" if "psql" not in str(last_error) else "Direct fallback"})'
            )
        except Exception as log_error:
            print(f"Warning: Could not log restore action: {log_error}")
        
        # Refresh database connection
        try:
            refresh_database_connection()
        except Exception as refresh_error:
            print(f"Database connection refresh warning: {refresh_error}")
            
        return jsonify({
            "success": True,
            "message": f"Database restored successfully from backup: {filename}. Please refresh the page to see updated data."
        })
        
    except Exception as e:
        print(f"Error in restore_backup route: {e}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        return jsonify({
            "success": False, 
            "error": f"Restore operation failed: {str(e)}"
        })

    
def test_database_after_restore():
    """Test database connectivity after restore operation - FIXED VERSION"""
    try:
        with app.app_context():
            # Test basic connection with SQLAlchemy version compatibility
            try:
                # Try newer SQLAlchemy syntax first
                result = db.session.execute(text("SELECT 1"))
                row = result.fetchone()
            except AttributeError:
                # Fallback to older SQLAlchemy syntax
                result = db.engine.execute(text("SELECT 1"))
                row = result.fetchone()
            
            if not row or row[0] != 1:
                return False, "Basic connection test failed"
            
            # Test if main tables exist
            tables_to_check = ['patients', 'appointment', 'users', 'inventory']
            for table in tables_to_check:
                try:
                    # Try pullandentalclinic schema first
                    try:
                        result = db.session.execute(text(f"SELECT COUNT(*) FROM pullandentalclinic.{table}"))
                        count = result.fetchone()[0]
                        print(f"Table pullandentalclinic.{table}: {count} records")
                    except AttributeError:
                        # Fallback for older SQLAlchemy
                        result = db.engine.execute(text(f"SELECT COUNT(*) FROM pullandentalclinic.{table}"))
                        count = result.fetchone()[0]
                        print(f"Table pullandentalclinic.{table}: {count} records")
                except Exception:
                    # Try public schema as fallback
                    try:
                        try:
                            result = db.session.execute(text(f"SELECT COUNT(*) FROM public.{table}"))
                            count = result.fetchone()[0]
                            print(f"Table public.{table}: {count} records")
                        except AttributeError:
                            result = db.engine.execute(text(f"SELECT COUNT(*) FROM public.{table}"))
                            count = result.fetchone()[0]
                            print(f"Table public.{table}: {count} records")
                    except Exception as table_error:
                        print(f"Warning: Table {table} is not accessible: {str(table_error)}")
                        # Don't fail the test for missing tables
                        continue
            
            return True, "Database test completed"
            
    except Exception as e:
        return False, f"Database test failed: {str(e)}"

@app.route('/download_backup/<filename>')
@admin_required
def download_backup(filename):
    """Download a backup file"""
    try:
        backup_path = os.path.join(BACKUP_DIRECTORY, filename)
        
        if not os.path.exists(backup_path):
            return "Backup file not found", 404
        
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
@admin_required
def delete_backup(filename):
    """Delete a backup file"""
    try:
        if session.get('access_level') != 'admin':
            return jsonify({"success": False, "error": "You don't have permission to perform this action"})
            
        backup_path = os.path.join(BACKUP_DIRECTORY, filename)
        
        if not os.path.exists(backup_path):
            return jsonify({"success": False, "error": "Backup file not found"})
            
        os.remove(backup_path)
        
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

# ======================================================================
# PATIENT ROUTES - COMPLETE IMPLEMENTATION
# ======================================================================

@app.route('/patient/<int:patient_id>')
def patient_details(patient_id):
    """View details of a specific patient with real database data"""
    try:
        # Get patient regardless of is_deleted status for details view
        patient = Patient.query.get_or_404(patient_id)
        
        # Ensure is_deleted attribute exists (for backward compatibility)
        if not hasattr(patient, 'is_deleted'):
            patient.is_deleted = False
        
        formatted_patient_id = f"PAT-{patient.patId:03d}"
        
        real_appointments = Appointment.query.filter_by(apppatient=patient.patname).order_by(Appointment.appdate.desc()).all()
        
        formatted_appointments = []
        for appointment in real_appointments:
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
                'status': status,
                'raw_id': appointment.appid
            })
        
        dental_chart = DentalChart.query.filter_by(dcpatname=patient.patname, is_deleted=False).first()
        has_dental_chart = dental_chart is not None
        
        teeth_chart = Teeth.query.filter_by(tpatname=patient.patname, is_deleted=False).first()
        teeth_data = []
        
        if teeth_chart:
            for i in range(1, 33):
                tooth_condition = getattr(teeth_chart, f'l{i}', 'healthy')
                teeth_data.append({
                    'number': i,
                    'condition': tooth_condition or 'healthy'
                })
        
        recent_procedures = Report.query.filter_by(reppatient=patient.patname).order_by(Report.repdate.desc()).limit(5).all()
        
        formatted_procedures = []
        for proc in recent_procedures:
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
                'status': 'completed',
                'raw_id': proc.repid
            })
        
        # Log the view action
        log_user_action(
            session.get('user_id'),
            'View Patient Details',
            f'Viewed details for patient: {patient.patname} (ID: PAT-{patient.patId:03d}) - Status: {"Active" if not patient.is_deleted else "Inactive"}'
        )
        
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
        
        log_user_action(
            session.get('user_id'),
            'Create Patient',
            f'Created new patient: {new_patient.patname} (ID: PAT-{new_patient.patId:03d})'
        )
        
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

@app.route('/deactivate_patient/<int:patient_id>', methods=['POST'])
def deactivate_patient(patient_id):
    """Deactivate a patient (soft delete)"""
    try:
        patient = Patient.query.get_or_404(patient_id)
        patient.is_deleted = True
        
        db.session.commit()
        
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

@app.route('/reactivate_patient/<int:patient_id>', methods=['POST'])
def reactivate_patient(patient_id):
    """Reactivate a patient (restore from soft delete)"""
    try:
        patient = Patient.query.get_or_404(patient_id)
        patient.is_deleted = False
        
        db.session.commit()
        
        log_user_action(
            session.get('user_id'),
            'Reactivate Patient',
            f'Reactivated patient: {patient.patname} (ID: PAT-{patient.patId:03d})'
        )
        
        return jsonify({"success": True, "message": "Patient reactivated successfully"})
    except Exception as e:
        db.session.rollback()
        print(f"Error in reactivate_patient route: {e}")
        return jsonify({"success": False, "error": str(e)})

@app.route('/edit_patient/<int:patient_id>')
def edit_patient(patient_id):
    """Render edit patient page"""
    try:
        patient = Patient.query.get_or_404(patient_id)
        
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
        
        old_name = patient.patname
        
        patient.patname = request.form.get('name')
        patient.patemail = request.form.get('email')
        patient.patcontact = request.form.get('contact')
        
        dob_str = request.form.get('dob')
        if dob_str:
            patient.patdob = datetime.strptime(dob_str, '%Y-%m-%d').date()
        
        patient.patgender = request.form.get('gender')
        
        age_str = request.form.get('age')
        if age_str and age_str.isdigit():
            patient.patage = int(age_str)
        
        patient.pataddress = request.form.get('address')
        patient.patcityzipcode = request.form.get('cityzipcode')
        patient.patoccupation = request.form.get('occupation')
        patient.patreligion = request.form.get('religion')
        patient.patallergies = request.form.get('allergies')
        
        db.session.commit()
        
        log_user_action(
            session.get('user_id'),
            'Update Patient',
            f'Updated patient: {old_name} -> {patient.patname} (ID: PAT-{patient.patId:03d})'
        )
        
        return jsonify({'success': True})
    
    except Exception as e:
        db.session.rollback()
        print(f"Error in update_patient route: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/print_patients_report')
def print_patients_report():
    """Generate a printable patients report with filters"""
    try:
        status_filter = request.args.get('status', 'all')
        search_filter = request.args.get('search', '')
        
        print(f"Print request - Status: {status_filter}, Search: {search_filter}")
        
        if status_filter == 'active':
            patients_list = Patient.query.filter_by(is_deleted=False).all()
        elif status_filter == 'inactive':
            patients_list = Patient.query.filter_by(is_deleted=True).all()
        else:
            patients_list = Patient.query.all()
        
        if search_filter:
            filtered_patients = []
            for patient in patients_list:
                if (search_filter.lower() in patient.patname.lower() or 
                    search_filter.lower() in (patient.patcontact or '').lower() or
                    search_filter.lower() in (patient.patemail or '').lower()):
                    filtered_patients.append(patient)
            patients_list = filtered_patients
        
        active_patients = []
        inactive_patients = []
        
        for patient in patients_list:
            latest_appointment = Appointment.query.filter_by(apppatient=patient.patname).order_by(Appointment.appdate.desc()).first()
            last_visit = latest_appointment.appdate.strftime('%m/%d/%Y') if latest_appointment and latest_appointment.appdate else "No visits"
            
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
        
        status_labels = {
            'all': 'All Patients',
            'active': 'Active Patients Only',
            'inactive': 'Inactive Patients Only'
        }
        
        filter_info = {
            'status': status_labels.get(status_filter, status_filter.title()),
            'search': search_filter if search_filter else 'No search filter',
            'has_filters': status_filter != 'all' or search_filter,
            'status_filter': status_filter,
            'has_status_filter': status_filter != 'all'
        }
        
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
        else:
            total_patients = len(patients_list)
            active_count = len(active_patients)
            inactive_count = len(inactive_patients)
            filtered_patients = active_patients + inactive_patients
        
        current_user = session.get('real_name', session.get('username', 'Unknown User'))
        user_id = session.get('user_id')
        
        print_date = datetime.now().strftime('%B %d, %Y')
        print_time = datetime.now().strftime('%I:%M %p')
        print_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
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

# ======================================================================
# APPOINTMENTS ROUTES - COMPLETE IMPLEMENTATION
# ======================================================================

def _time_to_minutes(time_value):
    """Convert an HH:MM string to minutes after midnight."""
    clean_time = time_value.strip()
    if clean_time == '24:00':
        return 24 * 60
    parsed_time = datetime.strptime(clean_time, '%H:%M').time()
    return parsed_time.hour * 60 + parsed_time.minute


def _minutes_to_time(minutes):
    hours = minutes // 60
    minutes = minutes % 60
    return f"{hours:02d}:{minutes:02d}"


def _appointment_time_bounds(time_value):
    """Return start/end minutes for old single-time values or new time ranges."""
    if not time_value:
        return None, None

    clean_time = time_value.strip()
    lower_time = clean_time.lower()

    if ' - ' in clean_time:
        start_time, end_time = clean_time.split(' - ', 1)
    elif ' to ' in lower_time:
        split_at = lower_time.index(' to ')
        start_time = clean_time[:split_at]
        end_time = clean_time[split_at + 4:]
    elif '-' in clean_time:
        start_time, end_time = clean_time.split('-', 1)
    else:
        start_minutes = _time_to_minutes(clean_time)
        return start_minutes, min(start_minutes + 30, 24 * 60)

    return _time_to_minutes(start_time), _time_to_minutes(end_time)


def _format_time_range(start_time, end_time):
    start_minutes = _time_to_minutes(start_time)
    end_minutes = _time_to_minutes(end_time)

    if end_minutes <= start_minutes:
        raise ValueError("End time must be later than start time.")

    return f"{start_time.strip()} - {end_time.strip()}"


def _appointment_duration(time_value):
    try:
        start_minutes, end_minutes = _appointment_time_bounds(time_value)
    except ValueError:
        return "N/A"

    if start_minutes is None or end_minutes is None:
        return "N/A"

    return f"{end_minutes - start_minutes} min"


def _find_overlapping_appointment(appointment_date, start_time, end_time, exclude_id=None):
    start_minutes = _time_to_minutes(start_time)
    end_minutes = _time_to_minutes(end_time)

    query = Appointment.query.filter(Appointment.appdate == appointment_date)
    if exclude_id:
        query = query.filter(Appointment.appid != exclude_id)

    for appointment in query.all():
        if getattr(appointment, 'status', 'active') == 'cancelled':
            continue

        try:
            existing_start, existing_end = _appointment_time_bounds(appointment.apptime)
        except ValueError:
            continue

        if existing_start is None or existing_end is None:
            continue

        if start_minutes < existing_end and existing_start < end_minutes:
            return appointment

    return None

@app.route('/appointments')
def appointments():
    """Render the appointments page with status filtering"""
    try:
        status_filter = request.args.get('status', 'all')
        
        if status_filter == 'active':
            appointments_list = Appointment.query.filter_by(status='active').order_by(Appointment.appdate.desc()).all()
        elif status_filter == 'completed':
            appointments_list = Appointment.query.filter_by(status='completed').order_by(Appointment.appdate.desc()).all()
        elif status_filter == 'cancelled':
            appointments_list = Appointment.query.filter_by(status='cancelled').order_by(Appointment.appdate.desc()).all()
        else:
            appointments_list = Appointment.query.order_by(Appointment.appdate.desc()).all()
        
        all_patients = Patient.query.filter_by(is_deleted=False).all()
        
        formatted_appointments = []
        for appointment in appointments_list:
            status = getattr(appointment, 'status', 'active')
            
            if not hasattr(appointment, 'status') or not appointment.status:
                current_date = datetime.now().date()
                if appointment.appdate < current_date:
                    status = 'completed'
                elif appointment.appdate == current_date:
                    status = 'active'
                else:
                    status = 'active'
            
            formatted_appointments.append({
                'id': f"APT-{appointment.appid:03d}",
                'patient_name': appointment.apppatient,
                'doctor_name': "Dr. Andrews",
                'treatment': "General Checkup",
                'date': appointment.appdate.strftime('%B %d, %Y') if appointment.appdate else "N/A",
                'raw_date': appointment.appdate.strftime('%Y-%m-%d') if appointment.appdate else "",
                'time': appointment.apptime,
                'duration': _appointment_duration(appointment.apptime),
                'status': status,
                'status_class': f"status-{status}",
                'raw_id': appointment.appid
            })
        
        active_count = Appointment.query.filter_by(status='active').count() if hasattr(Appointment, 'status') else 0
        completed_count = Appointment.query.filter_by(status='completed').count() if hasattr(Appointment, 'status') else 0
        cancelled_count = Appointment.query.filter_by(status='cancelled').count() if hasattr(Appointment, 'status') else 0
        total_count = Appointment.query.count()
        
        if not hasattr(Appointment, 'status'):
            current_date = datetime.now().date()
            all_appointments = Appointment.query.all()
            active_count = sum(1 for apt in all_appointments if apt.appdate >= current_date)
            completed_count = sum(1 for apt in all_appointments if apt.appdate < current_date)
            cancelled_count = 0
        
        current_date = datetime.now().strftime("%A, %B %d, %Y")
        today_date = datetime.now().strftime("%Y-%m-%d")
        
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

@app.route('/add_appointment', methods=['POST'])
def add_appointment():
    """Add a new appointment with active status"""
    try:
        patient_id = request.form.get('patient_id')
        patient = Patient.query.get(patient_id)
        patient_name = patient.patname if patient else "Unknown Patient"
        appointment_date = datetime.strptime(request.form.get('date'), '%Y-%m-%d').date()
        start_time = request.form.get('start_time') or request.form.get('time')
        end_time = request.form.get('end_time')

        if not start_time or not end_time:
            return jsonify({"success": False, "error": "Start time and end time are required."})

        time_range = _format_time_range(start_time, end_time)
        overlapping_appointment = _find_overlapping_appointment(appointment_date, start_time, end_time)

        if overlapping_appointment:
            return jsonify({
                "success": False,
                "error": f"This time overlaps with {overlapping_appointment.apppatient}'s appointment at {overlapping_appointment.apptime}."
            })
        
        appointment_data = {
            'apppatient': patient_name,
            'apptime': time_range,
            'appdate': appointment_date
        }
        
        if hasattr(Appointment, 'status'):
            appointment_data['status'] = 'active'
        
        new_appointment = Appointment(**appointment_data)
        
        db.session.add(new_appointment)
        db.session.commit()
        
        log_user_action(
            session.get('user_id'),
            'Create Appointment',
            f'Created appointment for {patient_name} on {new_appointment.appdate} at {new_appointment.apptime}'
        )
        
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

@app.route('/cancel_appointment/<int:appointment_id>', methods=['POST'])
def cancel_appointment(appointment_id):
    """Cancel an appointment by setting status to cancelled"""
    try:
        appointment = Appointment.query.get_or_404(appointment_id)
        
        if hasattr(appointment, 'status'):
            appointment.status = 'cancelled'
        else:
            return jsonify({"success": False, "error": "Status field not available."})
        
        db.session.commit()
        
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
        
        if hasattr(appointment, 'status'):
            appointment.status = 'completed'
        
        db.session.commit()
        
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

@app.route('/reactivate_appointment/<int:appointment_id>', methods=['POST'])
def reactivate_appointment(appointment_id):
    """Reactivate a cancelled appointment"""
    try:
        appointment = Appointment.query.get_or_404(appointment_id)
        
        if hasattr(appointment, 'status'):
            try:
                start_minutes, end_minutes = _appointment_time_bounds(appointment.apptime)
            except ValueError:
                start_minutes, end_minutes = None, None

            if start_minutes is not None and end_minutes is not None:
                overlapping_appointment = _find_overlapping_appointment(
                    appointment.appdate,
                    _minutes_to_time(start_minutes),
                    _minutes_to_time(end_minutes),
                    exclude_id=appointment.appid
                )
                if overlapping_appointment:
                    return jsonify({
                        "success": False,
                        "error": f"This appointment overlaps with {overlapping_appointment.apppatient}'s appointment at {overlapping_appointment.apptime}."
                    })
            appointment.status = 'active'
        
        db.session.commit()
        
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

@app.route('/appointment_details/<int:appointment_id>')
def appointment_details(appointment_id):
    """View details of a specific appointment"""
    try:
        appointment = Appointment.query.get_or_404(appointment_id)
        
        patient = Patient.query.filter_by(patname=appointment.apppatient).first()
        patient_id = patient.patId if patient else None
        
        formatted_appointment = {
            'id': f"APT-{appointment.appid:03d}",
            'patient_name': appointment.apppatient,
            'doctor_name': "Dr. Andrews",
            'treatment': "General Checkup",
            'date': appointment.appdate.strftime('%B %d, %Y') if appointment.appdate else "N/A",
            'time': appointment.apptime,
            'duration': _appointment_duration(appointment.apptime),
            'status': "Scheduled",
            'notes': "No notes available",
            'raw_id': appointment.appid,
            'patient_id': f"PAT-{patient.patId:03d}" if patient else "Unknown",
            'raw_patient_id': patient_id,
            'patient_phone': patient.patcontact if patient else "N/A",
            'patient_email': patient.patemail if patient else "N/A"
        }
        
        current_date = datetime.now().strftime("%A, %B %d, %Y")
        
        return render_template('appointments/appointment_details.html', 
                             appointment=formatted_appointment,
                             current_date=current_date)
    except Exception as e:
        print(f"Error in appointment_details route: {e}")
        return f"Error loading appointment details: {e}", 500

@app.route('/reschedule_appointment', methods=['POST'])
def reschedule_appointment():
    """Reschedule an existing appointment and record the change"""
    try:
        appointment_id = request.form.get('appointment_id')
        new_date = request.form.get('date')
        new_start_time = request.form.get('start_time') or request.form.get('time')
        new_end_time = request.form.get('end_time')
        reason = request.form.get('reason', '')
        
        if not appointment_id or not new_date or not new_start_time or not new_end_time:
            return jsonify({"success": False, "error": "Missing required fields"})
        
        appointment = Appointment.query.get_or_404(int(appointment_id))
        parsed_new_date = datetime.strptime(new_date, '%Y-%m-%d').date()
        new_time = _format_time_range(new_start_time, new_end_time)
        overlapping_appointment = _find_overlapping_appointment(
            parsed_new_date,
            new_start_time,
            new_end_time,
            exclude_id=appointment.appid
        )

        if overlapping_appointment:
            return jsonify({
                "success": False,
                "error": f"This time overlaps with {overlapping_appointment.apppatient}'s appointment at {overlapping_appointment.apptime}."
            })
        
        max_id_result = db.session.query(db.func.max(RescheduleAppointment.rappid)).first()
        next_id = 1
        if max_id_result[0] is not None:
            next_id = max_id_result[0] + 1
        
        reschedule_record = RescheduleAppointment(
            rappid=next_id,
            rapppatient=appointment.apppatient,
            rapptime=appointment.apptime,
            rappdate=appointment.appdate,
            rappnewtime=new_time,
            rappnewdate=parsed_new_date,
            rappreason=reason
        )
        
        old_date = appointment.appdate
        old_time = appointment.apptime
        
        appointment.appdate = parsed_new_date
        appointment.apptime = new_time
        
        db.session.add(reschedule_record)
        db.session.commit()
        
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

@app.route('/rescheduled_appointments')
def rescheduled_appointments():
    """Render the rescheduled appointments page with data from the database"""
    try:
        rescheduled_list = RescheduleAppointment.query.order_by(RescheduleAppointment.rappnewdate.desc()).all()
        
        formatted_rescheduled = []
        for reschedule in rescheduled_list:
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
        
        current_date = datetime.now().strftime("%A, %B %d, %Y")
        today_date = datetime.now().strftime("%Y-%m-%d")
        
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
        status_filter = request.args.get('status', 'all')
        date_filter = request.args.get('date', '')
        patient_filter = request.args.get('patient', '')
        
        query = Appointment.query
        
        if status_filter == 'active':
            if hasattr(Appointment, 'status'):
                query = query.filter_by(status='active')
            else:
                current_date = datetime.now().date()
                query = query.filter(Appointment.appdate >= current_date)
        elif status_filter == 'completed':
            if hasattr(Appointment, 'status'):
                query = query.filter_by(status='completed')
            else:
                current_date = datetime.now().date()
                query = query.filter(Appointment.appdate < current_date)
        elif status_filter == 'cancelled':
            if hasattr(Appointment, 'status'):
                query = query.filter_by(status='cancelled')
            else:
                query = query.filter(False)
        
        appointments_list = query.order_by(Appointment.appdate.desc()).all()
        
        formatted_appointments = []
        for appointment in appointments_list:
            if hasattr(appointment, 'status') and appointment.status:
                status = appointment.status
            else:
                current_date = datetime.now().date()
                if appointment.appdate < current_date:
                    status = 'completed'
                elif appointment.appdate == current_date:
                    status = 'active'
                else:
                    status = 'active'
            
            include_appointment = True
            
            if date_filter:
                try:
                    filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
                    if appointment.appdate != filter_date:
                        include_appointment = False
                except ValueError:
                    pass
            
            if patient_filter and include_appointment:
                if patient_filter.lower() not in appointment.apppatient.lower():
                    include_appointment = False
            
            if include_appointment:
                patient = Patient.query.filter_by(patname=appointment.apppatient).first()
                
                formatted_appointments.append({
                    'id': f"APT-{appointment.appid:03d}",
                    'patient_name': appointment.apppatient,
                    'patient_contact': patient.patcontact if patient else "N/A",
                    'patient_id': f"PAT-{patient.patId:03d}" if patient else "N/A",
                    'date': appointment.appdate.strftime('%B %d, %Y') if appointment.appdate else "N/A",
                    'time': appointment.apptime or "N/A",
                    'status': status.capitalize(),
                    'doctor': "Dr. Andrews",
                    'treatment': "General Checkup",
                    'raw_date': appointment.appdate.strftime('%Y-%m-%d') if appointment.appdate else "",
                    'raw_time': appointment.apptime or ""
                })
        
        formatted_appointments.sort(key=lambda x: (x['raw_date'], x['raw_time']))
        
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
            'status_filter': status_filter,
            'has_status_filter': status_filter != 'all'
        }
        
        total_appointments = len(formatted_appointments)
        status_counts = {
            'active': len([a for a in formatted_appointments if a['status'].lower() == 'active']),
            'completed': len([a for a in formatted_appointments if a['status'].lower() == 'completed']),
            'cancelled': len([a for a in formatted_appointments if a['status'].lower() == 'cancelled'])
        }
        
        current_user = session.get('real_name', session.get('username', 'Unknown User'))
        user_id = session.get('user_id')
        
        print_date = datetime.now().strftime('%B %d, %Y')
        print_time = datetime.now().strftime('%I:%M %p')
        print_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
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

# ======================================================================
# STAFF MANAGEMENT ROUTES - COMPLETE IMPLEMENTATION
# ======================================================================

@app.route('/staff')
def staff():
    """Staff management page with status filtering"""
    try:
        status_filter = request.args.get('status', 'active')
        
        base_query = User.query.filter(User.usersaccess.in_(['admin', 'user']))
        
        if status_filter == 'active':
            try:
                if hasattr(User, 'is_deleted'):
                    staff_users = base_query.filter(
                        db.or_(User.is_deleted == False, User.is_deleted.is_(None))
                    ).all()
                else:
                    staff_users = db.session.execute(text("""
                        SELECT * FROM users 
                        WHERE usersaccess IN ('admin', 'user') 
                        AND (is_deleted = FALSE OR is_deleted IS NULL)
                    """)).fetchall()
            except Exception as e:
                print(f"Error with model query, using raw SQL: {e}")
                staff_users = db.session.execute(text("""
                    SELECT * FROM users 
                    WHERE usersaccess IN ('admin', 'user') 
                    AND (is_deleted = FALSE OR is_deleted IS NULL)
                """)).fetchall()
                
        elif status_filter == 'inactive':
            try:
                if hasattr(User, 'is_deleted'):
                    staff_users = base_query.filter(User.is_deleted == True).all()
                else:
                    staff_users = db.session.execute(text("""
                        SELECT * FROM users 
                        WHERE usersaccess IN ('admin', 'user') 
                        AND is_deleted = TRUE
                    """)).fetchall()
            except Exception as e:
                print(f"Error with model query, using raw SQL: {e}")
                staff_users = db.session.execute(text("""
                    SELECT * FROM users 
                    WHERE usersaccess IN ('admin', 'user') 
                    AND is_deleted = TRUE
                """)).fetchall()
                
        else:
            try:
                staff_users = base_query.all()
            except Exception as e:
                print(f"Error with model query, using raw SQL: {e}")
                staff_users = db.session.execute(text("""
                    SELECT * FROM users 
                    WHERE usersaccess IN ('admin', 'user')
                """)).fetchall()
        
        staff_members = []
        for user in staff_users:
            is_active = True
            
            if hasattr(user, 'is_deleted'):
                is_active = not user.is_deleted if user.is_deleted is not None else True
            else:
                try:
                    is_active = not user.is_deleted if hasattr(user, 'is_deleted') and user.is_deleted is not None else True
                except:
                    is_active = True
            
            def get_attr(obj, attr_name, default=""):
                try:
                    return getattr(obj, attr_name, default) or default
                except:
                    return default
            
            staff_member = {
                'id': f"STF-{get_attr(user, 'usersid', 0):03d}",
                'raw_id': get_attr(user, 'usersid', 0),
                'name': get_attr(user, 'usersrealname', 'Unknown'),
                'email': get_attr(user, 'usersemail', 'No email'),
                'contact': get_attr(user, 'userscontact', 'No contact'),
                'role': "Staff",
                'occupation': get_attr(user, 'usersoccupation', 'Staff'),
                'access_level': get_attr(user, 'usersaccess', 'user').capitalize(),
                'join_date': datetime.now(),
                'is_active': is_active,
                'appointment_count': 0,
                'patient_count': 0,
            }
            
            staff_members.append(staff_member)
        
        try:
            if hasattr(User, 'is_deleted'):
                active_count = User.query.filter(
                    User.usersaccess.in_(['admin', 'user']),
                    db.or_(User.is_deleted == False, User.is_deleted.is_(None))
                ).count()
                inactive_count = User.query.filter(
                    User.usersaccess.in_(['admin', 'user']),
                    User.is_deleted == True
                ).count()
            else:
                active_result = db.session.execute(text("""
                    SELECT COUNT(*) as count FROM users 
                    WHERE usersaccess IN ('admin', 'user') 
                    AND (is_deleted = FALSE OR is_deleted IS NULL)
                """)).fetchone()
                active_count = active_result[0] if active_result else 0
                
                inactive_result = db.session.execute(text("""
                    SELECT COUNT(*) as count FROM users 
                    WHERE usersaccess IN ('admin', 'user') 
                    AND is_deleted = TRUE
                """)).fetchone()
                inactive_count = inactive_result[0] if inactive_result else 0
        except Exception as e:
            print(f"Error getting counts: {e}")
            active_count = len([s for s in staff_members if s['is_active']])
            inactive_count = len([s for s in staff_members if not s['is_active']])
        
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
        import traceback
        print(traceback.format_exc())
        return f"Error loading staff page: {e}", 500

@app.route('/staff_details/<int:staff_id>')
def staff_details(staff_id):
    """View details of a specific staff member"""
    try:
        staff = User.query.get_or_404(staff_id)
        
        staff.is_active = True
        if hasattr(staff, 'is_deleted'):
            staff.is_active = not staff.is_deleted
        
        if request.args.get('format') == 'json':
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
            
            if hasattr(staff, 'usersdob') and staff.usersdob:
                staff_data['usersdob_formatted'] = staff.usersdob.strftime('%Y-%m-%d')
            
            if hasattr(staff, 'usersage') and staff.usersage:
                staff_data['usersage'] = staff.usersage
                
            return jsonify(staff_data)
        
        current_date = datetime.now().strftime("%B %d, %Y")
        
        try:
            return render_template('staff_details.html', 
                                  staff=staff,
                                  current_date=current_date)
        except Exception as template_error:
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
                </div>
            </body>
            </html>
            """
    except Exception as e:
        print(f"Error in staff_details route: {e}")
        return f"Error loading staff details: {e}", 500

@app.route('/add_staff', methods=['POST'])
@admin_required
def add_staff():
    """Add a new staff member - Admin only"""
    try:
        password = request.form.get('password')
        
        is_valid, error_message = validate_password(password)
        if not is_valid:
            return jsonify({"success": False, "error": error_message})
        
        new_staff = User(
            usersusername=request.form.get('username'),
            userspassword=hash_password(password),
            usersrealname=request.form.get('name'),
            usersemail=request.form.get('email'),
            usershomeaddress=request.form.get('address'),
            userscityzipcode=request.form.get('cityzipcode'),
            userscontact=request.form.get('contact'),
            usersreligion=request.form.get('religion'),
            usersgender=request.form.get('gender'),
            usersaccess=request.form.get('access'),
            usersoccupation=request.form.get('occupation')
        )
        
        dob_str = request.form.get('dob')
        if dob_str:
            new_staff.usersdob = datetime.strptime(dob_str, '%Y-%m-%d').date()
        
        age_str = request.form.get('age')
        if age_str and age_str.isdigit():
            new_staff.usersage = int(age_str)
        
        db.session.add(new_staff)
        db.session.commit()
        
        log_user_action(
            session.get('user_id'),
            'Create Staff',
            f'Added new staff member: {new_staff.usersrealname} ({new_staff.usersusername})'
        )
        
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

@app.route('/update_staff/<int:staff_id>', methods=['POST'])
@admin_required
def update_staff(staff_id):
    """Update staff information - Admin only"""
    try:
        staff = User.query.get_or_404(staff_id)
        
        old_name = staff.usersrealname
        
        staff.usersrealname = request.form.get('name')
        staff.usersemail = request.form.get('email')
        staff.userscontact = request.form.get('contact')
        staff.usershomeaddress = request.form.get('address')
        staff.userscityzipcode = request.form.get('cityzipcode')
        staff.usersreligion = request.form.get('religion')
        staff.usersgender = request.form.get('gender')
        staff.usersaccess = request.form.get('access')
        staff.usersoccupation = request.form.get('occupation')
        
        dob_str = request.form.get('dob')
        if dob_str:
            staff.usersdob = datetime.strptime(dob_str, '%Y-%m-%d').date()
        
        age_str = request.form.get('age')
        if age_str and age_str.isdigit():
            staff.usersage = int(age_str)
        
        new_password = request.form.get('password')
        if new_password:
            is_valid, error_message = validate_password(new_password)
            if not is_valid:
                return jsonify({'success': False, 'error': error_message})
            staff.userspassword = hash_password(new_password)
        
        db.session.commit()
        
        log_user_action(
            session.get('user_id'),
            'Update Staff',
            f'Updated staff member: {old_name} -> {staff.usersrealname} ({staff.usersusername})'
        )
        
        return jsonify({'success': True})
    
    except Exception as e:
        db.session.rollback()
        print(f"Error in update_staff route: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/deactivate_staff/<int:staff_id>', methods=['POST'])
@admin_required
def deactivate_staff(staff_id):
    """Deactivate a staff member - Admin only"""
    try:
        staff = User.query.get_or_404(staff_id)
        
        if session.get('user_id') == staff_id:
            return jsonify({"success": False, "error": "Cannot deactivate your own account"})
        
        if hasattr(staff, 'is_deleted'):
            staff.is_deleted = True
        else:
            return jsonify({
                "success": False, 
                "error": "User model does not have is_deleted field. Please add it to the database schema first."
            })
        
        db.session.commit()
        
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
@admin_required
def reactivate_staff(staff_id):
    """Reactivate a staff member - Admin only"""
    try:
        staff = User.query.get_or_404(staff_id)
        
        if hasattr(staff, 'is_deleted'):
            staff.is_deleted = False
        else:
            return jsonify({
                "success": False, 
                "error": "User model does not have is_deleted field. Please add it to the database schema first."
            })
        
        db.session.commit()
        
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

@app.route('/print_staff_report')
def print_staff_report():
    """Generate a printable staff report with filters"""
    try:
        status_filter = request.args.get('status', 'all')
        access_filter = request.args.get('access', 'all')
        search_filter = request.args.get('search', '')
        
        base_query = User.query.filter(User.usersaccess.in_(['admin', 'user']))
        
        if status_filter == 'active':
            if hasattr(User, 'is_deleted'):
                staff_users = base_query.filter_by(is_deleted=False).all()
            else:
                staff_users = base_query.all()
        elif status_filter == 'inactive':
            if hasattr(User, 'is_deleted'):
                staff_users = base_query.filter_by(is_deleted=True).all()
            else:
                staff_users = []
        else:
            staff_users = base_query.all()
        
        if access_filter != 'all':
            staff_users = [user for user in staff_users if user.usersaccess == access_filter]
        
        if search_filter:
            filtered_staff = []
            for user in staff_users:
                if (search_filter.lower() in user.usersrealname.lower() or
                    search_filter.lower() in (user.usersemail or '').lower() or
                    search_filter.lower() in (user.usersusername or '').lower() or
                    search_filter.lower() in (user.usersoccupation or '').lower()):
                    filtered_staff.append(user)
            staff_users = filtered_staff
        
        formatted_staff = []
        for user in staff_users:
            is_active = True
            if hasattr(user, 'is_deleted'):
                is_active = not user.is_deleted
            
            formatted_staff.append({
                'id': f"STF-{user.usersid:03d}",
                'name': user.usersrealname,
                'occupation': user.usersoccupation if hasattr(user, 'usersoccupation') and user.usersoccupation else "Staff",
                'email': user.usersemail or "N/A",
                'contact': user.userscontact or "N/A",
                'address': user.usershomeaddress or "N/A",
                'access_level': user.usersaccess.capitalize(),
                'gender': user.usersgender or "N/A",
                'age': user.usersage if hasattr(user, 'usersage') and user.usersage else "N/A",
                'is_active': is_active,
                'raw_id': user.usersid
            })
        
        status_labels = {
            'all': 'All Staff',
            'active': 'Active Staff Only',
            'inactive': 'Inactive Staff Only'
        }
        
        access_labels = {
            'all': 'All Access Levels',
            'admin': 'Administrators Only',
            'user': 'Users Only'
        }
        
        filter_info = {
            'status': status_labels.get(status_filter, status_filter.title()),
            'access': access_labels.get(access_filter, access_filter.title()),
            'search': search_filter if search_filter else 'No search filter',
            'has_filters': status_filter != 'all' or access_filter != 'all' or search_filter,
            'status_filter': status_filter,
            'access_filter': access_filter,
            'has_status_filter': status_filter != 'all',
            'has_access_filter': access_filter != 'all'
        }
        
        total_staff = len(formatted_staff)
        active_count = len([s for s in formatted_staff if s['is_active']])
        inactive_count = len([s for s in formatted_staff if not s['is_active']])
        admin_count = len([s for s in formatted_staff if s['access_level'].lower() == 'admin'])
        user_count = len([s for s in formatted_staff if s['access_level'].lower() == 'user'])
        
        current_user = session.get('real_name', session.get('username', 'Unknown User'))
        user_id = session.get('user_id')
        
        print_date = datetime.now().strftime('%B %d, %Y')
        print_time = datetime.now().strftime('%I:%M %p')
        print_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        filter_description = []
        filter_description.append(f"Status: {status_labels.get(status_filter, status_filter)}")
        if access_filter != 'all':
            filter_description.append(f"Access: {access_labels.get(access_filter, access_filter)}")
        if search_filter:
            filter_description.append(f"Search: {search_filter}")
        
        filter_text = ", ".join(filter_description)
        
        log_user_action(
            user_id,
            'Print Staff Report',
            f'Generated staff report: {total_staff} staff members ({filter_text})'
        )
        
        return render_template('print_staff_report.html',
                              staff_members=formatted_staff,
                              filter_info=filter_info,
                              total_staff=total_staff,
                              active_count=active_count,
                              inactive_count=inactive_count,
                              admin_count=admin_count,
                              user_count=user_count,
                              current_user=current_user,
                              print_date=print_date,
                              print_time=print_time,
                              print_datetime=print_datetime)
    
    except Exception as e:
        print(f"Error generating staff report: {e}")
        return f"Error generating staff report: {e}", 500

# ======================================================================
# INVENTORY MANAGEMENT ROUTES - COMPLETE IMPLEMENTATION
# ======================================================================

@app.route('/inventory')
def inventory():
    """Render the inventory management page with status filtering"""
    try:
        status_filter = request.args.get('status', 'active')
        
        if status_filter == 'active':
            inventory_items = Inventory.query.filter_by(is_deleted=False).all()
        elif status_filter == 'inactive':
            inventory_items = Inventory.query.filter_by(is_deleted=True).all()
        else:
            inventory_items = Inventory.query.all()
        
        formatted_items = []
        for item in inventory_items:
            is_expired = item.invdoe and item.invdoe < datetime.now().date()
            
            formatted_items.append({
                'id': f"INV-{item.invid:03d}",
                'name': item.invname,
                'type': item.invtype,
                'quantity': item.invquantity,
                'expiry': item.invdoe.strftime('%Y-%m-%d') if item.invdoe else "N/A",
                'min_quantity': 5,
                'status': "Expired" if is_expired else ("Low" if item.invquantity < 5 else "OK"),
                'remarks': item.invremarks or "",
                'is_active': not item.is_deleted,
                'raw_id': item.invid
            })
        
        current_date = datetime.now().strftime("%A, %B %d, %Y")
        
        active_items = Inventory.query.filter_by(is_deleted=False).all()
        total_items = len(active_items)
        low_stock = sum(1 for item in active_items if item.invquantity < 5)
        expired = sum(1 for item in active_items if item.invdoe and item.invdoe < datetime.now().date())
        
        total_value = sum(item.invquantity * 10 for item in active_items)
        
        active_count = Inventory.query.filter_by(is_deleted=False).count()
        inactive_count = Inventory.query.filter_by(is_deleted=True).count()
        total_count = active_count + inactive_count
        
        return render_template('inventory.html', 
                              inventory_items=formatted_items,
                              total_items=total_items,
                              low_stock_count=low_stock,
                              expired_count=expired,
                              total_value=total_value,
                              current_date=current_date,
                              status_filter=status_filter,
                              active_count=active_count,
                              inactive_count=inactive_count,
                              total_count=total_count)
    except Exception as e:
        print(f"Error in inventory route: {e}")
        return f"Error loading inventory: {e}", 500

@app.route('/inventory_item/<int:item_id>')
def get_inventory_item(item_id):
    """Get details of a specific inventory item"""
    try:
        item = Inventory.query.get_or_404(item_id)
        
        formatted_item = {
            'id': f"INV-{item.invid:03d}",
            'name': item.invname, 
            'type': item.invtype,
            'quantity': item.invquantity,
            'expiry_date': item.invdoe.strftime('%Y-%m-%d') if item.invdoe else "",
            'min_quantity': 5,
            'remarks': item.invremarks or "",
            'is_active': not item.is_deleted,
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
        new_item = Inventory(
            invname=request.form.get('name'),
            invtype=request.form.get('type'),
            invquantity=int(request.form.get('quantity', 0)),
            invremarks=request.form.get('remarks', ''),
            is_deleted=False
        )
        
        expiry_date = request.form.get('expiry_date')
        if expiry_date:
            new_item.invdoe = datetime.strptime(expiry_date, '%Y-%m-%d').date()
        
        db.session.add(new_item)
        db.session.commit()
        
        log_user_action(
            session.get('user_id'),
            'Create Inventory',
            f'Added new inventory item: {new_item.invname} (Quantity: {new_item.invquantity})'
        )
        
        active_items = Inventory.query.filter_by(is_deleted=False).all()
        total_items = len(active_items)
        low_stock = sum(1 for item in active_items if item.invquantity < 5)
        expired = sum(1 for item in active_items if item.invdoe and item.invdoe < datetime.now().date())
        
        is_expired = new_item.invdoe and new_item.invdoe < datetime.now().date()
        formatted_item = {
            'id': f"INV-{new_item.invid:03d}",
            'name': new_item.invname,
            'type': new_item.invtype,
            'quantity': new_item.invquantity,
            'expiry': new_item.invdoe.strftime('%Y-%m-%d') if new_item.invdoe else "N/A",
            'min_quantity': 5,
            'status': "Expired" if is_expired else ("Low" if new_item.invquantity < 5 else "OK"),
            'remarks': new_item.invremarks or "",
            'is_active': True,
            'raw_id': new_item.invid
        }
        
        inventory_stats = {
            'total_items': total_items,
            'low_stock': low_stock,
            'expired': expired,
            'total_value': total_items * 10
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
        
        old_name = item.invname
        old_quantity = item.invquantity
        
        item.invname = request.form.get('name')
        item.invtype = request.form.get('type')
        item.invquantity = int(request.form.get('quantity', 0))
        item.invremarks = request.form.get('remarks', '')
        
        expiry_date = request.form.get('expiry_date')
        if expiry_date:
            item.invdoe = datetime.strptime(expiry_date, '%Y-%m-%d').date()
        else:
            item.invdoe = None
        
        db.session.commit()
        
        log_user_action(
            session.get('user_id'),
            'Update Inventory',
            f'Updated inventory item: {old_name} -> {item.invname} (Quantity: {old_quantity} -> {item.invquantity})'
        )
        
        active_items = Inventory.query.filter_by(is_deleted=False).all()
        total_items = len(active_items)
        low_stock = sum(1 for item_stat in active_items if item_stat.invquantity < 5)
        expired = sum(1 for item_stat in active_items if item_stat.invdoe and item_stat.invdoe < datetime.now().date())
        
        is_expired = item.invdoe and item.invdoe < datetime.now().date()
        formatted_item = {
            'id': f"INV-{item.invid:03d}",
            'name': item.invname,
            'type': item.invtype,
            'quantity': item.invquantity,
            'expiry': item.invdoe.strftime('%Y-%m-%d') if item.invdoe else "N/A",
            'min_quantity': 5,
            'status': "Expired" if is_expired else ("Low" if item.invquantity < 5 else "OK"),
            'remarks': item.invremarks or "",
            'is_active': not item.is_deleted,
            'raw_id': item.invid
        }
        
        inventory_stats = {
            'total_items': total_items,
            'low_stock': low_stock,
            'expired': expired,
            'total_value': total_items * 10
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

@app.route('/deactivate_inventory/<int:item_id>', methods=['POST'])
def deactivate_inventory(item_id):
    """Deactivate an inventory item (soft delete)"""
    try:
        item = Inventory.query.get_or_404(item_id)
        
        item.is_deleted = True
        db.session.commit()
        
        log_user_action(
            session.get('user_id'),
            'Deactivate Inventory',
            f'Deactivated inventory item: {item.invname} (Quantity: {item.invquantity})'
        )
        
        active_items = Inventory.query.filter_by(is_deleted=False).all()
        total_items = len(active_items)
        low_stock = sum(1 for item_stat in active_items if item_stat.invquantity < 5)
        expired = sum(1 for item_stat in active_items if item_stat.invdoe and item_stat.invdoe < datetime.now().date())
        
        inventory_stats = {
            'total_items': total_items,
            'low_stock': low_stock,
            'expired': expired,
            'total_value': total_items * 10
        }
        
        return jsonify({"success": True, "stats": inventory_stats, "message": "Item deactivated successfully"})
    except Exception as e:
        db.session.rollback()
        print(f"Error in deactivate_inventory route: {e}")
        return jsonify({"success": False, "error": str(e)})

@app.route('/reactivate_inventory/<int:item_id>', methods=['POST'])
def reactivate_inventory(item_id):
    """Reactivate an inventory item (restore from soft delete)"""
    try:
        item = Inventory.query.get_or_404(item_id)
        
        item.is_deleted = False
        db.session.commit()
        
        log_user_action(
            session.get('user_id'),
            'Reactivate Inventory',
            f'Reactivated inventory item: {item.invname} (Quantity: {item.invquantity})'
        )
        
        active_items = Inventory.query.filter_by(is_deleted=False).all()
        total_items = len(active_items)
        low_stock = sum(1 for item_stat in active_items if item_stat.invquantity < 5)
        expired = sum(1 for item_stat in active_items if item_stat.invdoe and item_stat.invdoe < datetime.now().date())
        
        inventory_stats = {
            'total_items': total_items,
            'low_stock': low_stock,
            'expired': expired,
            'total_value': total_items * 10
        }
        
        return jsonify({"success": True, "stats": inventory_stats, "message": "Item reactivated successfully"})
    except Exception as e:
        db.session.rollback()
        print(f"Error in reactivate_inventory route: {e}")
        return jsonify({"success": False, "error": str(e)})

@app.route('/filter_inventory/<filter_type>')
def filter_inventory(filter_type):
    """Filter inventory items by type"""
    try:
        if filter_type == 'inactive':
            query = Inventory.query.filter_by(is_deleted=True)
        else:
            query = Inventory.query.filter_by(is_deleted=False)
        
        if filter_type == 'low_stock':
            query = query.filter(Inventory.invquantity < 5)
        elif filter_type == 'expired':
            query = query.filter(
                Inventory.invdoe.isnot(None), 
                Inventory.invdoe < datetime.now().date()
            )
        elif filter_type not in ['all', 'inactive']:
            query = query.filter_by(invtype=filter_type)
        
        inventory_items = query.all()
        
        formatted_items = []
        for item in inventory_items:
            is_expired = item.invdoe and item.invdoe < datetime.now().date()
            
            formatted_items.append({
                'id': f"INV-{item.invid:03d}",
                'name': item.invname,
                'type': item.invtype,
                'quantity': item.invquantity,
                'expiry': item.invdoe.strftime('%Y-%m-%d') if item.invdoe else "N/A",
                'min_quantity': 5,
                'status': "Expired" if is_expired else ("Low" if item.invquantity < 5 else "OK"),
                'remarks': item.invremarks or "",
                'is_active': not item.is_deleted,
                'raw_id': item.invid
            })
        
        return jsonify({"success": True, "items": formatted_items})
    except Exception as e:
        print(f"Error in filter_inventory route: {e}")
        return jsonify({"success": False, "error": str(e)})

@app.route('/print_inventory_report')
def print_inventory_report():
    """Generate a printable inventory report with status filters"""
    try:
        status_filter = request.args.get('status', 'active')
        filter_type = request.args.get('filter', 'all')
        search_filter = request.args.get('search', '')
        
        if status_filter == 'active':
            query = Inventory.query.filter_by(is_deleted=False)
        elif status_filter == 'inactive':
            query = Inventory.query.filter_by(is_deleted=True)
        else:
            query = Inventory.query
        
        if filter_type == 'low-stock':
            inventory_items = query.filter(Inventory.invquantity < 5).all()
        elif filter_type == 'expired':
            inventory_items = query.filter(
                Inventory.invdoe.isnot(None), 
                Inventory.invdoe < datetime.now().date()
            ).all()
        elif filter_type != 'all':
            inventory_items = query.filter_by(invtype=filter_type.title()).all()
        else:
            inventory_items = query.all()
        
        if search_filter:
            filtered_items = []
            for item in inventory_items:
                if (search_filter.lower() in item.invname.lower() or 
                    search_filter.lower() in (item.invtype or '').lower() or
                    search_filter.lower() in (item.invremarks or '').lower()):
                    filtered_items.append(item)
            inventory_items = filtered_items
        
        formatted_items = []
        for item in inventory_items:
            if item.is_deleted:
                status = "Inactive"
            elif item.invdoe and item.invdoe < datetime.now().date():
                status = "Expired"
            elif item.invquantity < 5:
                status = "Low Stock"
            else:
                status = "OK"
            
            formatted_items.append({
                'id': f"INV-{item.invid:03d}",
                'name': item.invname,
                'type': item.invtype or "N/A",
                'quantity': item.invquantity,
                'expiry_date': item.invdoe.strftime('%m/%d/%Y') if item.invdoe else "No Expiry",
                'min_quantity': 5,
                'status': status,
                'remarks': item.invremarks or "None",
                'formatted_expiry': item.invdoe.strftime('%B %d, %Y') if item.invdoe else "No Expiry Date",
                'is_active': not item.is_deleted
            })
        
        status_labels = {
            'active': 'Active Items Only',
            'inactive': 'Inactive Items Only',
            'all': 'All Items (Active & Inactive)'
        }
        
        filter_labels = {
            'all': 'All Categories',
            'consumables': 'Consumables Only',
            'equipment': 'Equipment Only', 
            'medicines': 'Medicines Only',
            'instruments': 'Instruments Only',
            'office_supplies': 'Office Supplies Only',
            'low-stock': 'Low Stock Items Only',
            'expired': 'Expired Items Only'
        }
        
        filter_info = {
            'status': status_labels.get(status_filter, status_filter.title()),
            'filter_type': filter_labels.get(filter_type, filter_type.title()),
            'search': search_filter if search_filter else 'No search filter',
            'has_filters': status_filter != 'active' or filter_type != 'all' or search_filter,
            'status_filter': status_filter,
            'category_filter': filter_type,
            'has_status_filter': status_filter != 'active',
            'has_category_filter': filter_type != 'all'
        }
        
        total_items = len(formatted_items)
        
        active_items = [item for item in formatted_items if item['is_active']]
        inactive_items = [item for item in formatted_items if not item['is_active']]
        
        active_count = len(active_items)
        inactive_count = len(inactive_items)
        
        low_stock_count = len([item for item in active_items if item['status'] == 'Low Stock'])
        expired_count = len([item for item in active_items if item['status'] == 'Expired'])
        ok_count = len([item for item in active_items if item['status'] == 'OK'])
        
        categorized_items = {}
        for item in formatted_items:
            category = item['type']
            if category not in categorized_items:
                categorized_items[category] = {'active': [], 'inactive': []}
            
            if item['is_active']:
                categorized_items[category]['active'].append(item)
            else:
                categorized_items[category]['inactive'].append(item)
        
        current_user = session.get('real_name', session.get('username', 'Unknown User'))
        user_id = session.get('user_id')
        
        print_date = datetime.now().strftime('%B %d, %Y')
        print_time = datetime.now().strftime('%I:%M %p')
        print_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        filter_description = []
        filter_description.append(f"Status: {status_labels.get(status_filter, status_filter)}")
        if filter_type != 'all':
            filter_description.append(f"Category: {filter_labels.get(filter_type, filter_type)}")
        if search_filter:
            filter_description.append(f"Search: {search_filter}")
        
        filter_text = ", ".join(filter_description)
        
        log_user_action(
            user_id,
            'Print Inventory Report',
            f'Generated inventory report: {total_items} items ({filter_text})'
        )
        
        return render_template('print_inventory_report.html',
                              inventory_items=formatted_items,
                              active_items=active_items,
                              inactive_items=inactive_items,
                              categorized_items=categorized_items,
                              filter_info=filter_info,
                              total_items=total_items,
                              active_count=active_count,
                              inactive_count=inactive_count,
                              low_stock_count=low_stock_count,
                              expired_count=expired_count,
                              ok_count=ok_count,
                              current_user=current_user,
                              print_date=print_date,
                              print_time=print_time,
                              print_datetime=print_datetime)
    
    except Exception as e:
        print(f"Error generating inventory report: {e}")
        return f"Error generating inventory report: {e}", 500

# ======================================================================
# USER REGISTRATION AND AUTHENTICATION ROUTES
# ======================================================================

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/register_process', methods=['POST'])
def register_process():
    """Process new user registration with enhanced password validation"""
    try:
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
        
        if password != confirm_password:
            return render_template('register.html', error="Passwords do not match")
        
        is_valid, error_message = validate_password(password)
        if not is_valid:
            return render_template('register.html', error=error_message)
        
        if contact:
            contact_clean = ''.join(filter(str.isdigit, contact))
            if len(contact_clean) != 11:
                return render_template('register.html', error="Contact number must be exactly 11 digits")
            contact = contact_clean
        else:
            return render_template('register.html', error="Contact number is required")
        
        if city_zipcode:
            zipcode_clean = ''.join(filter(str.isdigit, city_zipcode))
            if len(zipcode_clean) != 4:
                return render_template('register.html', error="Zipcode must be exactly 4 digits")
        else:
            return render_template('register.html', error="City and zipcode are required")
        
        existing_user = User.query.filter_by(usersusername=username).first()
        if existing_user:
            return render_template('register.html', error="Username already exists")
        
        new_user = User(
            usersusername=username,
            userspassword=hash_password(password),
            usersrealname=realname,
            usersemail=email,
            usershomeaddress=home_address,
            userscityzipcode=city_zipcode,
            userscontact=contact,
            usersreligion=religion,
            usersgender=gender,
            usersoccupation=occupation,
            usersaccess='user'
        )
        
        dob_str = request.form.get('usersdob')
        if dob_str:
            new_user.usersdob = datetime.strptime(dob_str, '%Y-%m-%d').date()
        
        age_str = request.form.get('usersage')
        if age_str and age_str.isdigit():
            new_user.usersage = int(age_str)
        
        db.session.add(new_user)
        db.session.commit()
        
        log_user_action(
            new_user.usersid,
            'User Registration',
            f'New user registered: {realname} ({username})'
        )
        
        return redirect(url_for('login', registration_success=True))
    
    except Exception as e:
        db.session.rollback()
        print(f"Error in register_process route: {e}")
        return render_template('register.html', error=f"Registration failed: {str(e)}")

@app.route('/forgot_password')
def forgot_password():
    """Render the forgot password page with optional pre-filled data"""
    reason = request.args.get('reason')
    username = request.args.get('username', '')
    
    context = {
        'prefill_username': username,
        'redirect_reason': reason
    }
    
    return render_template('forget_password.html', **context)

@app.route('/verify_identity', methods=['POST'])
def verify_identity():
    """Verify user identity with real name and username/email"""
    try:
        real_name = request.form.get('real_name', '').strip()
        username_email = request.form.get('username_email', '').strip()
        
        if not real_name or not username_email:
            return jsonify({"success": False, "error": "Please fill in all fields"})
        
        user = None
        
        user_by_username = User.query.filter_by(usersusername=username_email).first()
        if user_by_username and user_by_username.usersrealname.lower() == real_name.lower():
            user = user_by_username
        
        if not user:
            user_by_email = User.query.filter_by(usersemail=username_email).first()
            if user_by_email and user_by_email.usersrealname.lower() == real_name.lower():
                user = user_by_email
        
        if user:
            log_user_action(
                user.usersid,
                'Password Reset Verification',
                f'Identity verified for password reset: {user.usersrealname} ({user.usersusername})'
            )
            
            return jsonify({
                "success": True, 
                "user_name": user.usersrealname,
                "message": "Identity verified successfully"
            })
        else:
            log_user_action(
                0,
                'Failed Password Reset Verification',
                f'Failed identity verification attempt: Real Name: {real_name}, Username/Email: {username_email}'
            )
            
            return jsonify({
                "success": False, 
                "error": "The name and username/email combination does not match our records"
            })
            
    except Exception as e:
        print(f"Error in verify_identity route: {e}")
        return jsonify({"success": False, "error": "An error occurred during verification"})

@app.route('/reset_password', methods=['POST'])
def reset_password():
    """Reset user password after identity verification with enhanced password validation"""
    try:
        real_name = request.form.get('real_name', '').strip()
        username_email = request.form.get('username_email', '').strip()
        new_password = request.form.get('new_password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        
        if not all([real_name, username_email, new_password, confirm_password]):
            return render_template('forget_password.html', 
                                 error="Please fill in all fields")
        
        if new_password != confirm_password:
            return render_template('forget_password.html', 
                                 error="Passwords do not match")
        
        is_valid, error_message = validate_password(new_password)
        if not is_valid:
            return render_template('forget_password.html', error=error_message)
        
        user = None
        
        user_by_username = User.query.filter_by(usersusername=username_email).first()
        if user_by_username and user_by_username.usersrealname.lower() == real_name.lower():
            user = user_by_username
        
        if not user:
            user_by_email = User.query.filter_by(usersemail=username_email).first()
            if user_by_email and user_by_email.usersrealname.lower() == real_name.lower():
                user = user_by_email
        
        if not user:
            return render_template('forget_password.html', 
                                 error="Identity verification failed. Please try again.")
        
        user.userspassword = hash_password(new_password)
        db.session.commit()
        
        session['failed_attempts'] = 0
        
        log_user_action(
            user.usersid,
            'Password Reset Completed',
            f'Password successfully reset for: {user.usersrealname} ({user.usersusername})'
        )
        
        return render_template('forget_password.html', 
                             success_message="Password updated successfully! You can now login with your new password. Failed login attempts have been reset.")
        
    except Exception as e:
        db.session.rollback()
        print(f"Error in reset_password route: {e}")
        return render_template('forget_password.html', 
                             error="An error occurred while updating your password. Please try again.")

@app.route('/clear_failed_attempts', methods=['POST'])
@admin_required
def clear_failed_attempts():
    """Clear failed login attempts for current session - Admin only"""
    try:
        session['failed_attempts'] = 0
        
        log_user_action(
            session.get('user_id'),
            'Clear Failed Attempts',
            'Admin cleared failed login attempts for current session'
        )
        
        return jsonify({"success": True, "message": "Failed login attempts cleared"})
    except Exception as e:
        print(f"Error clearing failed attempts: {e}")
        return jsonify({"success": False, "error": str(e)})

# ======================================================================
# TREATMENTS/PROCEDURES ROUTES
# ======================================================================

@app.route('/treatments')
def treatments():
    """Redirect to procedures page"""
    return redirect(url_for('procedures'))

@app.route('/procedures')
def procedures():
    """Main procedures page showing all patients and recent procedures"""
    try:
        selected_patient_id = request.args.get('patient_id', type=int)
        patients_list = Patient.query.filter_by(is_deleted=False).order_by(Patient.patname.asc()).all()
        patient_by_name = {patient.patname: patient for patient in patients_list}
        inventory_items = Inventory.query.filter(
            Inventory.is_deleted == False,
            Inventory.invquantity > 0,
            or_(Inventory.invdoe.is_(None), Inventory.invdoe >= date.today())
        ).order_by(Inventory.invname.asc()).all()
        
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
        ).order_by(Report.repdate.desc(), Report.repid.desc()).all()
        
        formatted_patients = []
        patient_teeth_map = {}
        for patient in patients_list:
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
                'chart_complete': dental_chart is not None and teeth_chart is not None and is_chart_complete(dental_chart),
                'raw_id': patient.patId
            })

            patient_teeth_map[str(patient.patId)] = []
            for tooth_number in range(1, 33):
                if tooth_number <= 8:
                    quadrant = 1
                elif tooth_number <= 16:
                    quadrant = 2
                elif tooth_number <= 24:
                    quadrant = 3
                else:
                    quadrant = 4

                patient_teeth_map[str(patient.patId)].append({
                    'number': tooth_number,
                    'condition': getattr(teeth_chart, f'l{tooth_number}', 'healthy') if teeth_chart else 'healthy',
                    'quadrant': quadrant
                })

        formatted_inventory_items = []
        for item in inventory_items:
            formatted_inventory_items.append({
                'id': f"INV-{item.invid:03d}",
                'raw_id': item.invid,
                'name': item.invname,
                'type': item.invtype or "N/A",
                'quantity': item.invquantity or 0,
                'expiry': item.invdoe.strftime('%B %d, %Y') if item.invdoe else "No Expiry"
            })
        
        formatted_procedures = []
        for proc in recent_procedures:
            patient = patient_by_name.get(proc.reppatient)
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
                'patient_id': f"PAT-{patient.patId:03d}" if patient else "N/A",
                'patient_raw_id': patient.patId if patient else None,
                'date': proc.repdate.strftime('%B %d, %Y') if proc.repdate else "N/A",
                'date_iso': proc.repdate.strftime('%Y-%m-%d') if proc.repdate else "",
                'dentist': proc.repdentist or "N/A",
                'procedures': ", ".join(procedures_done) if procedures_done else "General Visit",
                'prescription': proc.repprescription or "None",
                'notes': proc.repothers or "None",
                'raw_id': proc.repid
            })
        
        total_patients = len(patients_list)
        patients_with_charts = sum(1 for p in formatted_patients if p['has_dental_chart'])
        today_procedures = Report.query.filter_by(repdate=date.today()).count()
        total_procedures = Report.query.count()
        
        current_date = datetime.now().strftime("%A, %B %d, %Y")
        
        return render_template('procedures.html',
                              patients=formatted_patients,
                              inventory_items=formatted_inventory_items,
                              patient_teeth_map=patient_teeth_map,
                              recent_procedures=formatted_procedures,
                              total_patients=total_patients,
                              patients_with_charts=patients_with_charts,
                              today_procedures=today_procedures,
                              total_procedures=total_procedures,
                              selected_patient_id=selected_patient_id,
                              current_date=current_date)
    
    except Exception as e:
        print(f"Error in procedures route: {e}")
        return f"Error loading procedures: {e}", 500

@app.route('/procedure_history/<int:patient_id>')
def procedure_history(patient_id):
    """View complete procedure history for a patient"""
    try:
        patient = Patient.query.get_or_404(patient_id)
        
        procedures = Report.query.filter_by(reppatient=patient.patname).order_by(Report.repdate.desc()).all()
        
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
        
        return render_template('procedure_history.html',
                              patient=patient,
                              procedures=formatted_procedures,
                              current_date=current_date)
    
    except Exception as e:
        print(f"Error in procedure_history route: {e}")
        return f"Error loading procedure history: {e}", 500

@app.route('/print_procedure/<int:procedure_id>')
def print_procedure(procedure_id):
    """Generate a printable record for one procedure"""
    try:
        procedure = Report.query.get_or_404(procedure_id)
        patient = Patient.query.filter_by(patname=procedure.reppatient).first()
        
        procedures_done = []
        if procedure.repcleaning: procedures_done.append("Cleaning")
        if procedure.repextraction: procedures_done.append("Extraction")
        if procedure.reprootcanal: procedures_done.append("Root Canal")
        if procedure.repbraces: procedures_done.append("Braces")
        if procedure.repdentures: procedures_done.append("Dentures")
        if procedure.repothers: procedures_done.append(procedure.repothers)
        
        procedure_record = {
            'id': f"PROC-{procedure.repid:03d}",
            'patient_name': procedure.reppatient,
            'date': procedure.repdate.strftime('%B %d, %Y') if procedure.repdate else "N/A",
            'dentist': procedure.repdentist or "N/A",
            'procedures': ", ".join(procedures_done) if procedures_done else "General Visit",
            'prescription': procedure.repprescription or "None",
            'notes': procedure.repothers or "None",
            'raw_id': procedure.repid
        }
        
        current_user = session.get('real_name', session.get('username', 'Unknown User'))
        print_date = datetime.now().strftime('%B %d, %Y')
        print_time = datetime.now().strftime('%I:%M %p')
        print_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        log_user_action(
            session.get('user_id'),
            'Print Procedure',
            f'Printed procedure {procedure_record["id"]} for {procedure.reppatient}'
        )
        
        return render_template('print_procedure.html',
                              procedure=procedure_record,
                              patient=patient,
                              current_user=current_user,
                              print_date=print_date,
                              print_time=print_time,
                              print_datetime=print_datetime)
    
    except Exception as e:
        print(f"Error generating procedure printout: {e}")
        return f"Error generating procedure printout: {e}", 500

# ======================================================================
# ENHANCED DENTAL CHART ROUTES - COMPLETE IMPLEMENTATION
# ======================================================================

def is_chart_complete(dental_chart):
    """Check if a dental chart has all required information"""
    if not dental_chart:
        return False
    
    required_fields = [
        'dcdentist',
        'dcq1', 'dcq2', 'dcq3', 'dcq4', 'dcq5', 'dcq6'
    ]
    
    for field in required_fields:
        field_value = getattr(dental_chart, field, None)
        if not field_value or field_value.strip() == '':
            return False
    
    return True

@app.route('/dental_charts')
def dental_charts():
    """Dental charts overview page"""
    try:
        patients_list = Patient.query.filter_by(is_deleted=False).all()
        
        formatted_patients = []
        for patient in patients_list:
            dental_chart = DentalChart.query.filter_by(dcpatname=patient.patname, is_deleted=False).first()
            teeth_chart = Teeth.query.filter_by(tpatname=patient.patname, is_deleted=False).first()
            
            latest_procedure = Report.query.filter_by(reppatient=patient.patname).order_by(Report.repdate.desc()).first()
            
            chart_complete = dental_chart is not None and teeth_chart is not None and is_chart_complete(dental_chart)
            
            formatted_patients.append({
                'id': f"PAT-{patient.patId:03d}",
                'name': patient.patname,
                'contact': patient.patcontact or "N/A",
                'age': patient.patage or "N/A",
                'gender': patient.patgender or "N/A",
                'has_dental_chart': dental_chart is not None,
                'has_teeth_chart': teeth_chart is not None,
                'chart_complete': chart_complete,
                'last_procedure_date': latest_procedure.repdate.strftime('%B %d, %Y') if latest_procedure and latest_procedure.repdate else "No procedures",
                'raw_id': patient.patId
            })
        
        total_patients = len(patients_list)
        complete_charts = sum(1 for p in formatted_patients if p['chart_complete'])
        incomplete_charts = total_patients - complete_charts
        
        current_date = datetime.now().strftime("%A, %B %d, %Y")
        
        return render_template('dental_chart_overview.html',
                              patients=formatted_patients,
                              total_patients=total_patients,
                              complete_charts=complete_charts,
                              incomplete_charts=incomplete_charts,
                              current_date=current_date)
    
    except Exception as e:
        print(f"Error in dental_charts route: {e}")
        return f"Error loading dental charts: {e}", 500

@app.route('/create_dental_chart_now/<int:patient_id>')
def create_dental_chart_now(patient_id):
    """Robust dental chart creation with comprehensive error handling"""
    try:
        print(f"=== CREATE CHART DEBUG START for Patient ID: {patient_id} ===")
        
        patient = Patient.query.get(patient_id)
        if not patient:
            print(f"ERROR: Patient {patient_id} not found")
            return f"Error: Patient with ID {patient_id} not found", 404
            
        print(f"SUCCESS: Found patient {patient.patname}")
        
        existing_dental_chart = DentalChart.query.filter_by(
            dcpatname=patient.patname, 
            is_deleted=False
        ).first()
        
        if existing_dental_chart:
            print(f"INFO: Dental chart already exists, redirecting to edit")
            return redirect(f"/patient_dental_chart/{patient_id}?message=Chart already exists")
        
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
        
        try:
            teeth_data = {}
            for i in range(1, 33):
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
        
        try:
            db.session.commit()
            print(f"SUCCESS: Committed both charts to database")
            
        except Exception as commit_error:
            print(f"ERROR committing to database: {str(commit_error)}")
            db.session.rollback()
            return f"Database Commit Error: {str(commit_error)}", 500
        
        try:
            log_user_action(
                session.get('user_id', 0),
                'Create Dental Chart',
                f'Created dental chart for {patient.patname} (ID: PAT-{patient.patId:03d})'
            )
            print(f"SUCCESS: Logged user action")
            
        except Exception as log_error:
            print(f"WARNING: Failed to log action: {str(log_error)}")
        
        print(f"=== CREATE CHART DEBUG SUCCESS ===")
        
        return redirect(f"/patient_dental_chart/{patient_id}?created=success")
        
    except Exception as e:
        print(f"=== CREATE CHART CRITICAL ERROR ===")
        print(f"Error: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        db.session.rollback()
        
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

@app.route('/patient_dental_chart/<int:patient_id>')
def patient_dental_chart(patient_id):
    """Enhanced dental chart display with message handling"""
    try:
        created = request.args.get('created')
        message = request.args.get('message')
        
        patient = Patient.query.get_or_404(patient_id)
        
        dental_chart = DentalChart.query.filter_by(dcpatname=patient.patname, is_deleted=False).first()
        if not dental_chart:
            print(f"No dental chart found for {patient.patname}, creating one...")
            return redirect(f"/create_dental_chart_now/{patient_id}")
        
        teeth_chart = Teeth.query.filter_by(tpatname=patient.patname, is_deleted=False).first()
        if not teeth_chart:
            print(f"No teeth chart found for {patient.patname}, creating one...")
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
        
        procedure_history = Report.query.filter_by(reppatient=patient.patname).order_by(Report.repdate.desc()).all()
        
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

        try:
            tooth_number = int(tooth_number)
        except (TypeError, ValueError):
            return jsonify({"success": False, "error": "Please choose a valid tooth number."})

        valid_conditions = {'healthy', 'caries', 'filled', 'crown', 'extracted', 'root-canal', 'implant', 'dentures'}
        if tooth_number < 1 or tooth_number > 32:
            return jsonify({"success": False, "error": "Tooth number must be between 1 and 32."})
        if condition not in valid_conditions:
            return jsonify({"success": False, "error": "Please choose a valid tooth condition."})
        
        patient = Patient.query.get_or_404(patient_id)
        
        teeth_chart = Teeth.query.filter_by(tpatname=patient.patname, is_deleted=False).first()
        if not teeth_chart:
            return jsonify({"success": False, "error": "Teeth chart not found"})
        
        setattr(teeth_chart, f'l{tooth_number}', condition)
        db.session.commit()
        
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

        try:
            procedure_date_obj = datetime.strptime(procedure_date, '%Y-%m-%d').date()
        except (TypeError, ValueError):
            return jsonify({"success": False, "error": "Please choose a valid procedure date."})

        if procedure_date_obj < date.today():
            return jsonify({"success": False, "error": "Procedure date cannot be in the past."})
        
        cleaning = 1 if request.form.get('cleaning') else 0
        extraction = 1 if request.form.get('extraction') else 0
        root_canal = 1 if request.form.get('root_canal') else 0
        braces = 1 if request.form.get('braces') else 0
        dentures = 1 if request.form.get('dentures') else 0
        filling = 1 if request.form.get('filling') else 0
        crowning = 1 if request.form.get('crowning') else 0
        
        patient = Patient.query.get_or_404(patient_id)

        procedure_configs = [
            {'key': 'cleaning', 'label': 'Cleaning', 'selected': cleaning, 'condition': None, 'requires_teeth': False},
            {'key': 'extraction', 'label': 'Extraction', 'selected': extraction, 'condition': 'extracted', 'requires_teeth': True},
            {'key': 'root_canal', 'label': 'Root Canal', 'selected': root_canal, 'condition': 'root-canal', 'requires_teeth': True},
            {'key': 'braces', 'label': 'Braces', 'selected': braces, 'condition': None, 'requires_teeth': False},
            {'key': 'dentures', 'label': 'Dentures', 'selected': dentures, 'condition': 'dentures', 'requires_teeth': True},
            {'key': 'filling', 'label': 'Filling', 'selected': filling, 'condition': 'filled', 'requires_teeth': True},
            {'key': 'crowning', 'label': 'Crowning', 'selected': crowning, 'condition': 'crown', 'requires_teeth': True}
        ]

        procedure_teeth = {}
        for procedure_config in procedure_configs:
            if not procedure_config['selected']:
                continue

            selected_teeth = []
            for raw_tooth_number in request.form.getlist(f"affected_teeth_{procedure_config['key']}"):
                try:
                    tooth_number = int(raw_tooth_number)
                except (TypeError, ValueError):
                    return jsonify({"success": False, "error": f"Please choose valid teeth for {procedure_config['label']}."})

                if tooth_number < 1 or tooth_number > 32:
                    return jsonify({"success": False, "error": "Affected tooth number must be between 1 and 32."})

                if tooth_number not in selected_teeth:
                    selected_teeth.append(tooth_number)

            if procedure_config['requires_teeth'] and not selected_teeth:
                return jsonify({"success": False, "error": f"Please select affected teeth for {procedure_config['label']}."})

            procedure_teeth[procedure_config['key']] = selected_teeth

        inventory_usage_by_id = {}
        inventory_item_ids = request.form.getlist('inventory_item_id')
        for raw_item_id in inventory_item_ids:
            try:
                item_id = int(raw_item_id)
                used_quantity = int(request.form.get(f'inventory_quantity_{item_id}', 0))
            except (TypeError, ValueError):
                return jsonify({"success": False, "error": "Please enter a valid quantity for each inventory item used."})

            if used_quantity <= 0:
                return jsonify({"success": False, "error": "Inventory quantity used must be at least 1."})

            inventory_usage_by_id[item_id] = inventory_usage_by_id.get(item_id, 0) + used_quantity

        inventory_usage = []
        for item_id, used_quantity in inventory_usage_by_id.items():
            inventory_item = Inventory.query.filter_by(invid=item_id, is_deleted=False).first()
            if not inventory_item:
                return jsonify({"success": False, "error": "One selected inventory item was not found or is inactive."})

            if inventory_item.invdoe and inventory_item.invdoe < date.today():
                return jsonify({"success": False, "error": f"{inventory_item.invname} is expired and cannot be used."})

            current_quantity = inventory_item.invquantity or 0
            if used_quantity > current_quantity:
                return jsonify({
                    "success": False,
                    "error": f"Not enough stock for {inventory_item.invname}. Available: {current_quantity}, requested: {used_quantity}."
                })

            inventory_usage.append((inventory_item, used_quantity))
        
        max_id = db.session.query(db.func.max(Report.repid)).first()[0]
        next_id = 1 if max_id is None else max_id + 1
        
        other_entries = []
        tooth_selection_entries = []
        for procedure_config in procedure_configs:
            if not procedure_config['selected']:
                continue

            selected_teeth = procedure_teeth.get(procedure_config['key'], [])
            teeth_summary = ", ".join(f"#{tooth}" for tooth in selected_teeth)
            tooth_selection_entries.append(f"{procedure_config['label']}: {teeth_summary}")

        if tooth_selection_entries:
            other_entries.append(f"Teeth Selections - {'; '.join(tooth_selection_entries)}")
        if notes:
            other_entries.append(notes)
        other_procedure_notes = ", ".join(other_entries)

        new_procedure = Report(
            repid=next_id,
            reppatient=patient.patname,
            repdate=procedure_date_obj,
            repprescription=prescription,
            repcleaning=cleaning,
            repextraction=extraction,
            reprootcanal=root_canal,
            repbraces=braces,
            repdentures=dentures,
            repdentist=dentist,
            repothers=other_procedure_notes
        )
        
        db.session.add(new_procedure)

        used_inventory_summary = []
        for inventory_item, used_quantity in inventory_usage:
            inventory_item.invquantity = (inventory_item.invquantity or 0) - used_quantity
            used_inventory_summary.append(f"{inventory_item.invname} x{used_quantity}")
        
        procedures_done = []
        for procedure_config in procedure_configs:
            if not procedure_config['selected']:
                continue

            selected_teeth = procedure_teeth.get(procedure_config['key'], [])
            teeth_summary = ", ".join(f"#{tooth}" for tooth in selected_teeth)
            procedures_done.append(f"{procedure_config['label']} ({teeth_summary})" if teeth_summary else procedure_config['label'])
        if notes: procedures_done.append(notes)

        procedure_summary = ", ".join(procedures_done) if procedures_done else "General Visit"
        dental_chart = DentalChart.query.filter_by(dcpatname=patient.patname, is_deleted=False).first()
        if not dental_chart:
            max_dental_id = db.session.query(db.func.max(DentalChart.dcID)).scalar() or 0
            dental_chart = DentalChart(
                dcID=max_dental_id + 1,
                dcpatname=patient.patname,
                dcpcontact=patient.patcontact or "",
                dcdoctor="",
                dcdcontact="",
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

        dental_chart.dcdentist = dentist
        dental_chart.dcpcontact = patient.patcontact or dental_chart.dcpcontact
        dental_chart.dcvisit = f"{procedure_date_obj.strftime('%B %d, %Y')} - {procedure_summary}"[:255]

        updated_teeth_summary = []
        tooth_updates = [
            (procedure_config, procedure_teeth.get(procedure_config['key'], []))
            for procedure_config in procedure_configs
            if procedure_config['selected'] and procedure_config['condition']
        ]
        if tooth_updates:
            teeth_chart = Teeth.query.filter_by(tpatname=patient.patname, is_deleted=False).first()
            if not teeth_chart:
                max_teeth_id = db.session.query(db.func.max(Teeth.tID)).scalar() or 0
                teeth_data = {f'l{i}': 'healthy' for i in range(1, 33)}
                teeth_chart = Teeth(
                    tID=max_teeth_id + 1,
                    tpatname=patient.patname,
                    is_deleted=False,
                    **teeth_data
                )
                db.session.add(teeth_chart)

            for procedure_config, selected_teeth in tooth_updates:
                for tooth_number in selected_teeth:
                    setattr(teeth_chart, f'l{tooth_number}', procedure_config['condition'])
                teeth_summary = ", ".join(f"#{tooth_number}" for tooth_number in selected_teeth)
                updated_teeth_summary.append(f"{procedure_config['label']}: {teeth_summary} to {procedure_config['condition']}")

        db.session.commit()
        
        log_user_action(
            session.get('user_id'),
            'Add Procedure',
            f'Added procedure for {patient.patname}: {procedure_summary}'
            + (f' | Inventory used: {", ".join(used_inventory_summary)}' if used_inventory_summary else '')
            + (f' | Updated teeth: {"; ".join(updated_teeth_summary)}' if updated_teeth_summary else '')
        )
        
        return jsonify({
            "success": True,
            "message": "Procedure added successfully",
            "procedure": {
                "id": f"PROC-{new_procedure.repid:03d}",
                "patient": patient.patname,
                "date": new_procedure.repdate.strftime('%B %d, %Y'),
                "procedures": procedure_summary
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
        
        dental_chart = DentalChart.query.filter_by(dcpatname=patient.patname, is_deleted=False).first()
        if not dental_chart:
            return jsonify({"success": False, "error": "Dental chart not found"})
        
        required_fields = {
            'dentist': request.form.get('dentist'),
            'q1': request.form.get('q1'),
            'q2': request.form.get('q2'),
            'q3': request.form.get('q3'),
            'q4': request.form.get('q4'),
            'q5': request.form.get('q5'),
            'q6': request.form.get('q6')
        }
        
        missing_fields = []
        for field_name, field_value in required_fields.items():
            if not field_value or field_value.strip() == '':
                if field_name == 'dentist':
                    missing_fields.append('Dentist Name')
                else:
                    question_number = field_name[1:]
                    missing_fields.append(f'Question {question_number}')
        
        if missing_fields:
            return jsonify({
                "success": False, 
                "error": f"Please complete the following required fields: {', '.join(missing_fields)}",
                "missing_fields": missing_fields
            })
        
        dental_chart.dcdoctor = request.form.get('doctor')
        dental_chart.dcdentist = request.form.get('dentist')
        dental_chart.dcdcontact = request.form.get('dentist_contact')
        dental_chart.dcpcontact = request.form.get('patient_contact') or dental_chart.dcpcontact
        dental_chart.dcvisit = request.form.get('visit_reason') or dental_chart.dcvisit
        
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
        
        log_user_action(
            session.get('user_id'),
            'Update Dental Chart',
            f'Updated complete dental chart for patient {patient.patname}'
        )
        
        return jsonify({
            "success": True,
            "message": "Dental chart saved successfully! Chart is now complete."
        })
    
    except Exception as e:
        db.session.rollback()
        print(f"Error in update_dental_chart route: {e}")
        return jsonify({"success": False, "error": str(e)})

@app.route('/print_dental_chart/<int:patient_id>')
def print_dental_chart(patient_id):
    """Generate a printable dental chart"""
    try:
        print(f"=== PRINT DENTAL CHART DEBUG START for Patient ID: {patient_id} ===")
        
        patient = Patient.query.get_or_404(patient_id)
        print(f"Found patient: {patient.patname}")
        
        dental_chart = DentalChart.query.filter_by(dcpatname=patient.patname, is_deleted=False).first()
        if not dental_chart:
            print(f"WARNING: No dental chart found for patient {patient.patname}")
            dental_chart = type('obj', (object,), {
                'dcdoctor': '',
                'dcdentist': '',
                'dcdcontact': '',
                'dcpcontact': patient.patcontact or '',
                'dcq1': '', 'dcq2': '', 'dcq3': '', 'dcq4': '', 'dcq5': '', 'dcq6': '',
                'dcqe2': '', 'dcqe3': '', 'dcqe4': '', 'dcqe5': ''
            })
        
        teeth_chart = Teeth.query.filter_by(tpatname=patient.patname, is_deleted=False).first()
        print(f"Teeth chart found: {teeth_chart is not None}")
        
        teeth_data = []
        if teeth_chart:
            print("Processing teeth data...")
            for i in range(1, 33):
                tooth_condition = getattr(teeth_chart, f'l{i}', 'healthy')
                
                if 1 <= i <= 8:
                    quadrant = 1
                elif 9 <= i <= 16:
                    quadrant = 2
                elif 17 <= i <= 24:
                    quadrant = 3
                else:
                    quadrant = 4
                
                tooth_data = {
                    'number': i,
                    'condition': tooth_condition or 'healthy',
                    'quadrant': quadrant
                }
                teeth_data.append(tooth_data)
                
            print(f"Created teeth data for {len(teeth_data)} teeth")
        else:
            print("No teeth chart found - creating default healthy teeth")
            for i in range(1, 33):
                if 1 <= i <= 8:
                    quadrant = 1
                elif 9 <= i <= 16:
                    quadrant = 2
                elif 17 <= i <= 24:
                    quadrant = 3
                else:
                    quadrant = 4
                    
                teeth_data.append({
                    'number': i,
                    'condition': 'healthy',
                    'quadrant': quadrant
                })
        
        procedure_history = Report.query.filter_by(reppatient=patient.patname).order_by(Report.repdate.desc()).all()
        print(f"Found {len(procedure_history)} procedures")
        
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
        
        current_user = session.get('real_name', session.get('username', 'Unknown User'))
        user_id = session.get('user_id')
        
        print_date = datetime.now().strftime('%B %d, %Y')
        print_time = datetime.now().strftime('%I:%M %p')
        print_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        log_user_action(
            user_id,
            'Print Dental Chart',
            f'Printed dental chart for {patient.patname} (ID: PAT-{patient.patId:03d})'
        )
        
        print(f"=== PRINT DENTAL CHART DEBUG SUCCESS ===")
        
        template_data = {
            'patient': patient,
            'dental_chart': dental_chart,
            'teeth_data': teeth_data,
            'procedure_history': formatted_history,
            'current_user': current_user,
            'print_date': print_date,
            'print_time': print_time,
            'print_datetime': print_datetime
        }
        
        return render_template('print_dental_chart.html', **template_data)
    
    except Exception as e:
        print(f"=== PRINT DENTAL CHART ERROR ===")
        print(f"Error: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        return f"Error generating printable dental chart: {e}", 500

# ======================================================================
# SETTINGS AND OTHER ROUTES
# ======================================================================

PAYMENT_METHOD_LABELS = {
    'cash': 'Cash',
    'gcash': 'GCash',
    'bank_transfer': 'Bank Transfer'
}

PAYMENT_TYPE_LABELS = {
    'partial': 'Partial Payment',
    'full': 'Full Payment'
}

SERVICE_PRICE_LIST = [
    {'key': 'cleaning', 'label': 'Cleaning / Oral Prophylaxis', 'price': '1000.00'},
    {'key': 'extraction', 'label': 'Tooth Extraction', 'price': '1500.00'},
    {'key': 'root_canal', 'label': 'Root Canal Treatment', 'price': '8000.00'},
    {'key': 'braces', 'label': 'Braces / Orthodontic Treatment', 'price': '50000.00'},
    {'key': 'dentures', 'label': 'Dentures', 'price': '15000.00'},
    {'key': 'filling', 'label': 'Dental Filling', 'price': '1500.00'},
    {'key': 'crowning', 'label': 'Dental Crown', 'price': '12000.00'},
    {'key': 'special_case', 'label': 'Special Case / Other Service', 'price': '0.00'}
]

CLINIC_RECEIPT_INFO = {
    'name': 'Pullan Dental Clinic',
    'address': '142 Timog Avenue, Sacred Heart',
    'city': 'Quezon City, 1103 Metro Manila, Philippines',
    'phone': '(02) 8123-4567 / +63 917 123 4567',
    'email': 'info@pullandental.com.ph',
    'tin': os.getenv('CLINIC_TIN', ''),
    'bir_permit': os.getenv('CLINIC_BIR_PERMIT', ''),
    'business_style': os.getenv('CLINIC_BUSINESS_STYLE', 'Dental Clinic'),
    'accreditation': os.getenv('CLINIC_ACCREDITATION', '')
}

MONEY_QUANT = Decimal('0.01')

def ensure_payments_table():
    """Create the payments table when running without migrations."""
    Payment.__table__.create(bind=db.engine, checkfirst=True)
    ServicePrice.__table__.create(bind=db.engine, checkfirst=True)
    columns = {column['name'] for column in inspect(db.engine).get_columns(Payment.__tablename__)}
    if 'service_items' not in columns:
        db.session.execute(text('ALTER TABLE payments ADD COLUMN service_items TEXT'))
        db.session.commit()

    seed_service_prices()

def parse_money(raw_value, field_name):
    try:
        amount = Decimal(str(raw_value or '').replace(',', '').strip()).quantize(MONEY_QUANT)
    except (InvalidOperation, ValueError):
        raise ValueError(f"Please enter a valid {field_name}.")

    if amount <= 0:
        raise ValueError(f"{field_name.title()} must be greater than 0.")

    return amount

def decimal_money(value):
    if value is None:
        return Decimal('0.00')
    return Decimal(str(value)).quantize(MONEY_QUANT)

def format_money(value):
    return f"PHP {decimal_money(value):,.2f}"

def seed_service_prices():
    existing_prices = {
        service.service_key: service
        for service in ServicePrice.query.all()
    }
    changed = False

    for default_service in SERVICE_PRICE_LIST:
        if default_service['key'] == 'special_case':
            continue

        service_record = existing_prices.get(default_service['key'])
        if not service_record:
            service_record = ServicePrice(
                service_key=default_service['key'],
                service_name=default_service['label'],
                price=decimal_money(default_service['price']),
                is_active=True,
                updated_at=datetime.utcnow()
            )
            db.session.add(service_record)
            changed = True
        elif service_record.service_name != default_service['label']:
            service_record.service_name = default_service['label']
            changed = True

    if changed:
        db.session.commit()

def get_service_price_list():
    ensure_service_table_only()
    seed_service_prices()
    saved_prices = {
        service.service_key: service
        for service in ServicePrice.query.filter_by(is_active=True).all()
    }

    service_prices = []
    for default_service in SERVICE_PRICE_LIST:
        if default_service['key'] == 'special_case':
            service_prices.append(default_service.copy())
            continue

        saved = saved_prices.get(default_service['key'])
        service_prices.append({
            'key': default_service['key'],
            'label': saved.service_name if saved else default_service['label'],
            'price': f"{decimal_money(saved.price if saved else default_service['price']):.2f}"
        })

    return service_prices

def ensure_service_table_only():
    ServicePrice.__table__.create(bind=db.engine, checkfirst=True)

def service_price_map(service_prices):
    return {service['key']: service for service in service_prices}

def make_service_item(service_key, service_prices):
    price_lookup = service_price_map(service_prices)
    service = price_lookup.get(service_key)
    if not service:
        return None

    unit_price = decimal_money(service['price'])
    return {
        'key': service_key,
        'name': service['label'],
        'quantity': '1.00',
        'unit_price': f"{unit_price:.2f}",
        'line_total': f"{unit_price:.2f}"
    }

def procedure_service_items_from_report(procedure, service_prices):
    service_keys = []
    if procedure.repcleaning:
        service_keys.append('cleaning')
    if procedure.repextraction:
        service_keys.append('extraction')
    if procedure.reprootcanal:
        service_keys.append('root_canal')
    if procedure.repbraces:
        service_keys.append('braces')
    if procedure.repdentures:
        service_keys.append('dentures')

    notes = (procedure.repothers or '').lower()
    if 'filling:' in notes:
        service_keys.append('filling')
    if 'crowning:' in notes:
        service_keys.append('crowning')

    service_items = []
    for service_key in service_keys:
        if service_key not in [item['key'] for item in service_items]:
            service_item = make_service_item(service_key, service_prices)
            if service_item:
                service_items.append(service_item)

    return service_items

def total_from_service_items(service_items):
    return sum((decimal_money(item.get('line_total') or 0) for item in service_items), Decimal('0.00')).quantize(MONEY_QUANT)

def parse_service_items(raw_items, fallback_description, fallback_amount, service_prices):
    try:
        submitted_items = json.loads(raw_items or '[]')
    except (TypeError, json.JSONDecodeError):
        submitted_items = []

    service_items = []
    total_from_items = Decimal('0.00')

    if isinstance(submitted_items, list):
        for item in submitted_items:
            if not isinstance(item, dict):
                continue

            service_key = (item.get('key') or 'custom').strip()
            price_lookup = service_price_map(service_prices)
            configured_service = price_lookup.get(service_key)

            if configured_service and service_key != 'special_case':
                service_name = configured_service['label']
                unit_price = decimal_money(configured_service['price'])
            else:
                service_key = 'special_case'
                service_name = (item.get('name') or '').strip()
                unit_price = parse_money(item.get('unit_price'), 'special case service price')

            if not service_name:
                continue

            quantity = parse_money(item.get('quantity') or '1', 'service quantity')
            line_total = (quantity * unit_price).quantize(MONEY_QUANT)

            service_items.append({
                'key': service_key[:60],
                'name': service_name[:180],
                'quantity': f"{quantity:.2f}",
                'unit_price': f"{unit_price:.2f}",
                'line_total': f"{line_total:.2f}"
            })
            total_from_items += line_total

    if service_items:
        description = ", ".join(item['name'] for item in service_items)[:255]
        return service_items, total_from_items.quantize(MONEY_QUANT), description

    fallback_total = parse_money(fallback_amount, 'total amount')
    description = (fallback_description or 'Dental service payment').strip()[:255]
    return [{
        'key': 'custom',
        'name': description,
        'quantity': '1.00',
        'unit_price': f"{fallback_total:.2f}",
        'line_total': f"{fallback_total:.2f}"
    }], fallback_total, description

def get_payment_service_items(payment_record):
    try:
        saved_items = json.loads(payment_record.service_items or '[]')
    except (TypeError, json.JSONDecodeError):
        saved_items = []

    if not saved_items:
        saved_items = [{
            'name': payment_record.description or 'Dental service payment',
            'quantity': '1.00',
            'unit_price': f"{decimal_money(payment_record.total_amount):.2f}",
            'line_total': f"{decimal_money(payment_record.total_amount):.2f}"
        }]

    formatted_items = []
    for item in saved_items:
        formatted_items.append({
            'name': item.get('name') or 'Dental service payment',
            'quantity': decimal_money(item.get('quantity') or '1'),
            'unit_price': format_money(item.get('unit_price') or 0),
            'line_total': format_money(item.get('line_total') or 0)
        })

    return formatted_items

def procedure_name_from_report(procedure):
    procedures_done = []
    if procedure.repcleaning:
        procedures_done.append("Cleaning")
    if procedure.repextraction:
        procedures_done.append("Extraction")
    if procedure.reprootcanal:
        procedures_done.append("Root Canal")
    if procedure.repbraces:
        procedures_done.append("Braces")
    if procedure.repdentures:
        procedures_done.append("Dentures")
    if procedure.repothers:
        procedures_done.append(procedure.repothers)
    return ", ".join(procedures_done) if procedures_done else "General Visit"

def build_report_payment_summaries():
    summaries = {}
    payments_with_reports = Payment.query.filter(Payment.report_id.isnot(None)).order_by(Payment.paid_at.asc(), Payment.payment_id.asc()).all()

    for payment_record in payments_with_reports:
        summary = summaries.setdefault(payment_record.report_id, {
            'total_amount': Decimal('0.00'),
            'paid': Decimal('0.00'),
            'balance': Decimal('0.00'),
            'service_items': []
        })
        summary['total_amount'] = decimal_money(payment_record.total_amount)
        summary['paid'] += decimal_money(payment_record.amount_paid)
        summary['balance'] = max(summary['total_amount'] - summary['paid'], Decimal('0.00'))
        if not summary['service_items'] and payment_record.service_items:
            try:
                summary['service_items'] = json.loads(payment_record.service_items)
            except (TypeError, json.JSONDecodeError):
                summary['service_items'] = []

    return summaries

@app.route('/billing')
def billing():
    """Keep old billing links working by opening the payments module."""
    return redirect(url_for('payments'))

@app.route('/payments')
def payments():
    """Record and review patient payments."""
    try:
        ensure_payments_table()

        selected_patient_id = request.args.get('patient_id', type=int)
        service_prices = get_service_price_list()
        patients_list = Patient.query.filter_by(is_deleted=False).order_by(Patient.patname.asc()).all()
        all_patients = Patient.query.all()
        patient_by_name = {patient.patname: patient for patient in all_patients}

        reports = Report.query.order_by(Report.repdate.desc(), Report.repid.desc()).all()
        report_payment_summaries = build_report_payment_summaries()

        formatted_reports = []
        for procedure in reports:
            patient = patient_by_name.get(procedure.reppatient)
            summary = report_payment_summaries.get(procedure.repid, {
                'total_amount': Decimal('0.00'),
                'paid': Decimal('0.00'),
                'balance': Decimal('0.00'),
                'service_items': []
            })
            procedure_service_items = summary['service_items'] or procedure_service_items_from_report(procedure, service_prices)
            default_total = total_from_service_items(procedure_service_items)
            total_amount = summary['total_amount'] if summary['total_amount'] > 0 else default_total
            balance = summary['balance'] if summary['total_amount'] > 0 else default_total
            formatted_reports.append({
                'raw_id': procedure.repid,
                'id': f"PROC-{procedure.repid:03d}",
                'patient_id': patient.patId if patient else '',
                'patient_name': procedure.reppatient,
                'date': procedure.repdate.strftime('%B %d, %Y') if procedure.repdate else 'N/A',
                'description': procedure_name_from_report(procedure),
                'service_items': procedure_service_items,
                'total_amount': f"{total_amount:.2f}" if total_amount > 0 else '',
                'paid': f"{summary['paid']:.2f}",
                'balance': f"{balance:.2f}" if balance > 0 else '',
                'balance_display': format_money(balance) if total_amount > 0 else 'No priced services'
            })

        all_payment_records = Payment.query.all()
        payment_records = Payment.query.order_by(Payment.paid_at.desc(), Payment.payment_id.desc()).limit(100).all()
        formatted_payments = []
        total_collected = Decimal('0.00')
        full_count = 0
        partial_count = 0

        for payment_record in all_payment_records:
            amount_paid = decimal_money(payment_record.amount_paid)
            total_collected += amount_paid
            if decimal_money(payment_record.balance_after) <= 0:
                full_count += 1
            else:
                partial_count += 1

        for payment_record in payment_records:
            formatted_payments.append({
                'raw_id': payment_record.payment_id,
                'id': payment_record.formatted_id(),
                'patient': payment_record.patient_name,
                'description': payment_record.description or 'Dental service',
                'date': payment_record.paid_at.strftime('%B %d, %Y %I:%M %p') if payment_record.paid_at else 'N/A',
                'method': PAYMENT_METHOD_LABELS.get(payment_record.payment_method, payment_record.payment_method),
                'type': PAYMENT_TYPE_LABELS.get(payment_record.payment_type, payment_record.payment_type.title()),
                'amount': format_money(payment_record.amount_paid),
                'balance': format_money(payment_record.balance_after),
                'status_class': 'paid' if decimal_money(payment_record.balance_after) <= 0 else 'partial'
            })

        outstanding_balance = sum((summary['balance'] for summary in report_payment_summaries.values()), Decimal('0.00'))

        current_date = datetime.now().strftime("%A, %B %d, %Y")

        return render_template(
            'payments.html',
            patients=patients_list,
            procedures=formatted_reports,
            payments=formatted_payments,
            payment_methods=PAYMENT_METHOD_LABELS,
            service_prices=service_prices,
            selected_patient_id=selected_patient_id,
            total_collected=format_money(total_collected),
            outstanding_balance=format_money(outstanding_balance),
            full_count=full_count,
            partial_count=partial_count,
            current_date=current_date
        )

    except Exception as e:
        print(f"Error loading payments page: {e}")
        return f"Error loading payments page: {e}", 500

@app.route('/add_payment', methods=['POST'])
def add_payment():
    """Save a patient payment and open its printable receipt."""
    try:
        ensure_payments_table()

        patient_id = request.form.get('patient_id', type=int)
        patient = Patient.query.get_or_404(patient_id)

        raw_report_id = request.form.get('report_id')
        report_id = int(raw_report_id) if raw_report_id else None
        procedure = Report.query.get(report_id) if report_id else None
        if report_id and not procedure:
            return "Selected procedure was not found.", 404
        if procedure and procedure.reppatient != patient.patname:
            return "Selected procedure does not belong to this patient.", 400

        amount_paid = parse_money(request.form.get('amount_paid'), 'payment amount')
        payment_method = (request.form.get('payment_method') or '').strip()
        payment_type = (request.form.get('payment_type') or '').strip()
        reference_number = (request.form.get('reference_number') or '').strip()
        notes = (request.form.get('notes') or '').strip()

        if payment_method not in PAYMENT_METHOD_LABELS:
            return "Please choose a valid payment method.", 400
        if payment_type not in PAYMENT_TYPE_LABELS:
            return "Please choose partial or full payment.", 400
        if payment_method in ('gcash', 'bank_transfer') and not reference_number:
            return "Reference number is required for GCash and bank transfer payments.", 400

        paid_at = datetime.now()
        raw_payment_date = request.form.get('payment_date')
        if raw_payment_date:
            try:
                payment_date = datetime.strptime(raw_payment_date, '%Y-%m-%d').date()
                paid_at = datetime.combine(payment_date, datetime.now().time())
            except ValueError:
                return "Please choose a valid payment date.", 400

        previous_paid = Decimal('0.00')
        prior_payments = []
        if report_id:
            prior_payments = Payment.query.filter_by(report_id=report_id).order_by(Payment.paid_at.asc(), Payment.payment_id.asc()).all()
            previous_paid = sum((decimal_money(existing.amount_paid) for existing in prior_payments), Decimal('0.00'))

        if prior_payments:
            first_payment = prior_payments[0]
            total_amount = decimal_money(first_payment.total_amount)
            description = first_payment.description or procedure_name_from_report(procedure)
            try:
                service_items = json.loads(first_payment.service_items or '[]')
            except (TypeError, json.JSONDecodeError):
                service_items = []
            if not service_items:
                service_items = [{
                    'key': 'custom',
                    'name': description,
                    'quantity': '1.00',
                    'unit_price': f"{total_amount:.2f}",
                    'line_total': f"{total_amount:.2f}"
                }]
        else:
            service_prices = get_service_price_list()
            service_items, total_amount, description = parse_service_items(
                request.form.get('service_items'),
                request.form.get('description'),
                request.form.get('total_amount'),
                service_prices
            )

        if total_amount < previous_paid:
            return "Total amount cannot be lower than the amount already paid for this procedure.", 400

        balance_before = (total_amount - previous_paid).quantize(MONEY_QUANT)
        if balance_before <= 0:
            return "This procedure has already been fully paid.", 400

        if amount_paid > balance_before:
            return "Payment amount cannot be greater than the remaining balance.", 400

        balance_after = (balance_before - amount_paid).quantize(MONEY_QUANT)
        if payment_type == 'full' and balance_after > 0:
            return "Full payment must cover the full remaining balance.", 400

        computed_payment_type = 'full' if balance_after <= 0 else 'partial'
        if not description:
            description = procedure_name_from_report(procedure) if procedure else 'Dental service payment'

        current_user = session.get('real_name', session.get('username', 'Unknown User'))
        new_payment = Payment(
            patient_id=patient.patId,
            patient_name=patient.patname,
            report_id=report_id,
            description=description[:255],
            service_items=json.dumps(service_items),
            total_amount=total_amount,
            balance_before=balance_before,
            amount_paid=amount_paid,
            balance_after=balance_after,
            payment_type=computed_payment_type,
            payment_method=payment_method,
            reference_number=reference_number or None,
            notes=notes or None,
            received_by=current_user,
            paid_at=paid_at
        )

        db.session.add(new_payment)
        db.session.commit()

        log_user_action(
            session.get('user_id'),
            'Add Payment',
            f'Recorded {PAYMENT_TYPE_LABELS[computed_payment_type]} for {patient.patname}: {format_money(amount_paid)} via {PAYMENT_METHOD_LABELS[payment_method]}'
        )

        return redirect(url_for('payment_receipt', payment_id=new_payment.payment_id))

    except ValueError as e:
        db.session.rollback()
        return str(e), 400
    except Exception as e:
        db.session.rollback()
        print(f"Error saving payment: {e}")
        return f"Error saving payment: {e}", 500

@app.route('/payment_receipt/<int:payment_id>')
def payment_receipt(payment_id):
    """Generate a printable payment receipt."""
    try:
        ensure_payments_table()

        payment_record = Payment.query.get_or_404(payment_id)
        patient = Patient.query.get(payment_record.patient_id) if payment_record.patient_id else None
        procedure = Report.query.get(payment_record.report_id) if payment_record.report_id else None
        service_items = get_payment_service_items(payment_record)

        receipt = {
            'id': payment_record.formatted_id(),
            'patient_name': payment_record.patient_name,
            'patient_id': f"PAT-{payment_record.patient_id:03d}" if payment_record.patient_id else "N/A",
            'description': payment_record.description or 'Dental service payment',
            'procedure_id': f"PROC-{payment_record.report_id:03d}" if payment_record.report_id else "N/A",
            'payment_date': payment_record.paid_at.strftime('%B %d, %Y') if payment_record.paid_at else 'N/A',
            'payment_time': payment_record.paid_at.strftime('%I:%M %p') if payment_record.paid_at else 'N/A',
            'payment_method': PAYMENT_METHOD_LABELS.get(payment_record.payment_method, payment_record.payment_method),
            'payment_type': PAYMENT_TYPE_LABELS.get(payment_record.payment_type, payment_record.payment_type.title()),
            'reference_number': payment_record.reference_number or 'N/A',
            'total_amount': format_money(payment_record.total_amount),
            'balance_before': format_money(payment_record.balance_before),
            'amount_paid': format_money(payment_record.amount_paid),
            'total_paid_to_date': format_money(decimal_money(payment_record.total_amount) - decimal_money(payment_record.balance_after)),
            'balance_after': format_money(payment_record.balance_after),
            'status': payment_record.status,
            'notes': payment_record.notes or 'None',
            'received_by': payment_record.received_by or 'Unknown User',
            'service_items': service_items
        }

        current_user = session.get('real_name', session.get('username', 'Unknown User'))
        print_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        log_user_action(
            session.get('user_id'),
            'Print Payment Receipt',
            f'Opened receipt {receipt["id"]} for {payment_record.patient_name}'
        )

        return render_template(
            'print_payment_receipt.html',
            receipt=receipt,
            patient=patient,
            procedure=procedure,
            clinic=CLINIC_RECEIPT_INFO,
            current_user=current_user,
            print_datetime=print_datetime
        )

    except Exception as e:
        print(f"Error generating payment receipt: {e}")
        return f"Error generating payment receipt: {e}", 500

@app.route('/update_service_prices', methods=['POST'])
@admin_required
def update_service_prices():
    """Allow admins to update the preset service price list."""
    try:
        ensure_payments_table()
        updated_services = []

        for default_service in SERVICE_PRICE_LIST:
            service_key = default_service['key']
            if service_key == 'special_case':
                continue

            price = parse_money(request.form.get(f'price_{service_key}'), f'{default_service["label"]} price')
            service_record = ServicePrice.query.filter_by(service_key=service_key).first()
            if not service_record:
                service_record = ServicePrice(
                    service_key=service_key,
                    service_name=default_service['label'],
                    is_active=True
                )
                db.session.add(service_record)

            service_record.price = price
            service_record.updated_at = datetime.utcnow()
            updated_services.append(f'{service_record.service_name}: {format_money(price)}')

        db.session.commit()

        log_user_action(
            session.get('user_id'),
            'Update Service Prices',
            f'Updated payment service prices: {", ".join(updated_services)}'
        )

        return redirect(url_for('payments'))

    except ValueError as e:
        db.session.rollback()
        return str(e), 400
    except Exception as e:
        db.session.rollback()
        print(f"Error updating service prices: {e}")
        return f"Error updating service prices: {e}", 500

@app.route('/settings')
def settings():
    """About page with system and clinic information"""
    try:
        import sys
        import platform
        from sqlalchemy import __version__ as sqlalchemy_version
        
        system_info = {
            'version': 'v2.5.1 (Build 2025.01) - PostgreSQL',
            'release_date': 'January 15, 2025',
            'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            'platform': platform.system(),
            'sqlalchemy_version': sqlalchemy_version,
            'database_status': 'Connected (PostgreSQL)',
            'last_update': 'January 15, 2025',
            'next_update': 'March 1, 2025'
        }
        
        clinic_info = {
            'name': 'Pullan Dental Clinic',
            'address': '142 Timog Avenue, Sacred Heart',
            'city': 'Quezon City, 1103 Metro Manila, Philippines',
            'phone': '(02) 8123-4567 / +63 917 123 4567',
            'email': 'info@pullandental.com.ph',
            'website': 'www.pullandental.com.ph',
            'established': '2018',
            'license': 'QC-DC-2018-0142'
        }
        
        try:
            total_patients = Patient.query.filter_by(is_deleted=False).count()
            total_appointments = Appointment.query.count()
            total_procedures = Report.query.count()
            total_staff = User.query.filter(User.usersaccess.in_(['admin', 'user'])).count()
        except:
            total_patients = 0
            total_appointments = 0
            total_procedures = 0
            total_staff = 0
        
        current_user = session.get('real_name', session.get('username', 'User'))
        current_date = datetime.now().strftime("%A, %B %d, %Y")
        
        log_user_action(
            session.get('user_id'),
            'View About Page',
            f'User {current_user} viewed system about page'
        )
        
        return render_template('about.html',
                              system_info=system_info,
                              clinic_info=clinic_info,
                              total_patients=total_patients,
                              total_appointments=total_appointments,
                              total_procedures=total_procedures,
                              total_staff=total_staff,
                              current_user=current_user,
                              current_date=current_date)
    
    except Exception as e:
        print(f"Error in settings/about route: {e}")
        return f"Error loading about page: {e}", 500



def get_lan_ip_addresses():
    """Return possible local LAN IP addresses for showing access URLs."""
    addresses = set()

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as lan_socket:
            lan_socket.connect(("8.8.8.8", 80))
            addresses.add(lan_socket.getsockname()[0])
    except OSError:
        pass

    try:
        hostname = socket.gethostname()
        for ip_address in socket.gethostbyname_ex(hostname)[2]:
            if not ip_address.startswith("127."):
                addresses.add(ip_address)
    except OSError:
        pass

    return sorted(addresses) or ["YOUR_COMPUTER_IP"]


if __name__ == "__main__":
    host = os.getenv("APP_HOST", "0.0.0.0")
    port = int(os.getenv("APP_PORT", "5000"))
    debug = os.getenv("FLASK_DEBUG", "true").lower() in ("1", "true", "yes", "on")

    print("\nPullan Dental Clinic is starting...")
    print(f"Local access: http://127.0.0.1:{port}")
    if host == "0.0.0.0":
        print("LAN access:")
        for ip_address in get_lan_ip_addresses():
            print(f"  http://{ip_address}:{port}")
    else:
        print(f"Configured host access: http://{host}:{port}")
    print("Use the LAN access URL on the other computer connected to the same network.\n")

    app.run(host=host, port=port, debug=debug)
