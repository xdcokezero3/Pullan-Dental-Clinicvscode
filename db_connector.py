# db_connector.py - Fresh Start with Robust MySQL Connection + UserLog Model
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import pymysql
import os
import time
from datetime import date, datetime
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

# Install PyMySQL as MySQLdb replacement
pymysql.install_as_MySQLdb()

# Create Flask app
app = Flask(__name__)

# Database configuration class
class DatabaseConfig:
    """Centralized database configuration with multiple fallback options"""
    
    # Default configuration - modify these if needed
    DB_USER = 'root'
    DB_PASSWORD = 'root' 
    DB_NAME = 'pullandentalclinic'
    DB_PORT = 3306
    
    # Host options to try in order
    HOST_OPTIONS = [
        'localhost',
        '127.0.0.1',
        '::1',  # IPv6 localhost
    ]
    
    @classmethod
    def test_connection(cls, host, user, password, database, port):
        """Test if we can connect to MySQL with given parameters"""
        try:
            # Test basic connection
            connection = pymysql.connect(
                host=host,
                user=user,
                password=password,
                database=database,
                port=port,
                connect_timeout=10,
                read_timeout=10,
                write_timeout=10,
                charset='utf8mb4'
            )
            
            # Test query execution
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                if result[0] != 1:
                    raise Exception("Query test failed")
            
            connection.close()
            return True
            
        except Exception as e:
            print(f"Connection test failed for {host}: {str(e)}")
            return False
    
    @classmethod
    def get_working_uri(cls):
        """Find a working database URI by testing different configurations"""
        print("Testing database connections...")
        
        for host in cls.HOST_OPTIONS:
            print(f"Testing connection to {host}:{cls.DB_PORT}...")
            
            if cls.test_connection(host, cls.DB_USER, cls.DB_PASSWORD, cls.DB_NAME, cls.DB_PORT):
                uri = f"mysql+pymysql://{cls.DB_USER}:{cls.DB_PASSWORD}@{host}:{cls.DB_PORT}/{cls.DB_NAME}"
                print(f"✅ Successfully connected to MySQL at {host}:{cls.DB_PORT}")
                return uri
        
        # If all direct connections fail, try without specifying database
        print("Direct database connections failed. Trying to connect to MySQL server...")
        for host in cls.HOST_OPTIONS:
            try:
                connection = pymysql.connect(
                    host=host,
                    user=cls.DB_USER,
                    password=cls.DB_PASSWORD,
                    port=cls.DB_PORT,
                    connect_timeout=10
                )
                
                # Try to create database if it doesn't exist
                with connection.cursor() as cursor:
                    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {cls.DB_NAME}")
                    cursor.execute(f"USE {cls.DB_NAME}")
                
                connection.close()
                uri = f"mysql+pymysql://{cls.DB_USER}:{cls.DB_PASSWORD}@{host}:{cls.DB_PORT}/{cls.DB_NAME}"
                print(f"✅ Connected to MySQL server and created/used database at {host}:{cls.DB_PORT}")
                return uri
                
            except Exception as e:
                print(f"Failed to connect to MySQL server at {host}: {str(e)}")
                continue
        
        # Last resort - return a default URI and let SQLAlchemy handle the error
        print("❌ All connection attempts failed!")
        print("Please check:")
        print("1. MySQL service is running")
        print("2. Username and password are correct")
        print("3. Database exists")
        print("4. Port 3306 is not blocked")
        
        return f"mysql+pymysql://{cls.DB_USER}:{cls.DB_PASSWORD}@localhost:{cls.DB_PORT}/{cls.DB_NAME}"

# Get working database URI
database_uri = DatabaseConfig.get_working_uri()

# Configure Flask app with database settings
app.config['SQLALCHEMY_DATABASE_URI'] = database_uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_size': 10,
    'pool_timeout': 20,
    'pool_recycle': 3600,  # 1 hour
    'pool_pre_ping': True,  # Verify connections before using
    'max_overflow': 20,
    'connect_args': {
        'connect_timeout': 10,
        'read_timeout': 10,
        'write_timeout': 10,
        'charset': 'utf8mb4'
    }
}

# Initialize SQLAlchemy
db = SQLAlchemy(app)

# Test function for database connectivity
def test_database_connection():
    """Comprehensive database connection test"""
    print("\n" + "="*50)
    print("TESTING DATABASE CONNECTION")
    print("="*50)
    
    try:
        # Test 1: Basic SQLAlchemy connection
        with app.app_context():
            result = db.engine.execute(text("SELECT 1"))
            row = result.fetchone()
            if row[0] == 1:
                print("✅ SQLAlchemy connection: SUCCESS")
            else:
                print("❌ SQLAlchemy connection: FAILED")
                return False
        
        # Test 2: Database existence
        with app.app_context():
            result = db.engine.execute(text("SELECT DATABASE()"))
            db_name = result.fetchone()[0]
            print(f"✅ Connected to database: {db_name}")
        
        # Test 3: Check if tables can be created
        with app.app_context():
            db.engine.execute(text("CREATE TABLE IF NOT EXISTS connection_test (id INT PRIMARY KEY)"))
            db.engine.execute(text("DROP TABLE connection_test"))
            print("✅ Table creation/deletion: SUCCESS")
        
        print("✅ All database tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {str(e)}")
        return False

# Database Models
class Patient(db.Model):
    __tablename__ = 'patients'
    
    patId = db.Column(db.Integer, primary_key=True)
    patname = db.Column(db.String(255))
    patemail = db.Column(db.String(255))
    pataddress = db.Column(db.String(255))
    patcityzipcode = db.Column(db.String(255))
    patcontact = db.Column(db.String(20))
    patreligion = db.Column(db.String(20))
    patdob = db.Column(db.Date)
    patgender = db.Column(db.String(10))
    patage = db.Column(db.Integer)
    patoccupation = db.Column(db.String(255))
    patallergies = db.Column(db.String(255))
    is_deleted = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return f"<Patient {self.patId}: {self.patname}>"

class Appointment(db.Model):
    __tablename__ = 'appointment'
    
    appid = db.Column(db.Integer, primary_key=True)
    apppatient = db.Column(db.String(255))
    apptime = db.Column(db.String(255))
    appdate = db.Column(db.Date)
    
    def __repr__(self):
        return f"<Appointment {self.appid}: {self.apppatient} on {self.appdate}>"
    
    def formatted_id(self):
        return f"APT-{self.appid:03d}"

class RescheduleAppointment(db.Model):
    __tablename__ = 'rappointment'
    
    rappid = db.Column(db.Integer, primary_key=True)
    rapppatient = db.Column(db.String(255))
    rapptime = db.Column(db.String(255))
    rappdate = db.Column(db.Date)
    rappnewtime = db.Column(db.String(255))
    rappnewdate = db.Column(db.Date)
    rappreason = db.Column(db.String(255))
    
    def __repr__(self):
        return f"<RescheduleAppointment {self.rappid}: {self.rapppatient}>"

class Inventory(db.Model):
    __tablename__ = 'inventory'
    
    invid = db.Column(db.Integer, primary_key=True)
    invname = db.Column(db.String(255))
    invquantity = db.Column(db.Integer)
    invdoe = db.Column(db.Date)
    invtype = db.Column(db.String(255))
    invremarks = db.Column(db.String(255))
    is_deleted = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return f"<Inventory {self.invid}: {self.invname} ({self.invquantity})>"

class User(db.Model):
    __tablename__ = 'users'
    
    usersid = db.Column(db.Integer, primary_key=True, autoincrement=True)
    usersusername = db.Column(db.String(255), unique=True, nullable=False)
    userspassword = db.Column(db.String(255), nullable=False)
    usersrealname = db.Column(db.String(255))
    usersemail = db.Column(db.String(255))
    usershomeaddress = db.Column(db.String(255))
    userscityzipcode = db.Column(db.String(255))
    userscontact = db.Column(db.String(255))
    usersreligion = db.Column(db.String(255))
    usersdob = db.Column(db.Date)
    usersgender = db.Column(db.String(255))
    usersage = db.Column(db.Integer)
    usersoccupation = db.Column(db.String(255))
    usersaccess = db.Column(db.String(255))
    key = db.Column(db.LargeBinary)
    
    def __repr__(self):
        return f"<User {self.usersid}: {self.usersusername}>"

class UserLog(db.Model):
    __tablename__ = 'user_logs'
    
    log_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer)
    action = db.Column(db.String(255))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    details = db.Column(db.Text)
    
    def __repr__(self):
        return f"<UserLog {self.log_id}: {self.action} by user {self.user_id}>"
    
    def formatted_timestamp(self):
        """Return formatted timestamp for display"""
        return self.timestamp.strftime('%Y-%m-%d %H:%M:%S') if self.timestamp else "N/A"

class DentalChart(db.Model):
    __tablename__ = 'dentalchart'
    
    dcID = db.Column(db.Integer, primary_key=True)
    dcpatname = db.Column(db.String(255))
    dcdoctor = db.Column(db.String(255))
    dcpcontact = db.Column(db.String(255))
    dcdentist = db.Column(db.String(255))
    dcdcontact = db.Column(db.String(255))
    dcvisit = db.Column(db.String(255))
    dcq1 = db.Column(db.String(255))
    dcq2 = db.Column(db.String(255))
    dcqe2 = db.Column(db.String(255))
    dcq3 = db.Column(db.String(255))
    dcqe3 = db.Column(db.String(255))
    dcq4 = db.Column(db.String(255))
    dcqe4 = db.Column(db.String(255))
    dcq5 = db.Column(db.String(255))
    dcqe5 = db.Column(db.String(255))
    dcq6 = db.Column(db.String(255))
    dcq7 = db.Column(db.String(255))
    dcqe7 = db.Column(db.String(255))
    dcq8 = db.Column(db.String(255))
    dcqe8 = db.Column(db.String(255))
    dcq9 = db.Column(db.String(255))
    dcqe9 = db.Column(db.String(255))
    is_deleted = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return f"<DentalChart {self.dcID}: {self.dcpatname}>"

class Report(db.Model):
    __tablename__ = 'reports'
    
    repid = db.Column(db.Integer, primary_key=True)
    reppatient = db.Column(db.String(255))
    repdate = db.Column(db.Date)
    repprescription = db.Column(db.String(255))
    repcleaning = db.Column(db.Integer)
    repextraction = db.Column(db.Integer)
    reprootcanal = db.Column(db.Integer)
    repbraces = db.Column(db.Integer)
    repdentures = db.Column(db.Integer)
    repdentist = db.Column(db.String(255))
    repothers = db.Column(db.String(255))
    
    def __repr__(self):
        return f"<Report {self.repid}: {self.reppatient} on {self.repdate}>"
    
# Add this Teeth model to your db_connector.py file after the existing models

class Teeth(db.Model):
    __tablename__ = 'teeth'
    
    tID = db.Column(db.Integer, primary_key=True)
    tpatname = db.Column(db.String(255))
    l1 = db.Column(db.String(255), default='healthy')
    l2 = db.Column(db.String(255), default='healthy')
    l3 = db.Column(db.String(255), default='healthy')
    l4 = db.Column(db.String(255), default='healthy')
    l5 = db.Column(db.String(255), default='healthy')
    l6 = db.Column(db.String(255), default='healthy')
    l7 = db.Column(db.String(255), default='healthy')
    l8 = db.Column(db.String(255), default='healthy')
    l9 = db.Column(db.String(255), default='healthy')
    l10 = db.Column(db.String(255), default='healthy')
    l11 = db.Column(db.String(255), default='healthy')
    l12 = db.Column(db.String(255), default='healthy')
    l13 = db.Column(db.String(255), default='healthy')
    l14 = db.Column(db.String(255), default='healthy')
    l15 = db.Column(db.String(255), default='healthy')
    l16 = db.Column(db.String(255), default='healthy')
    l17 = db.Column(db.String(255), default='healthy')
    l18 = db.Column(db.String(255), default='healthy')
    l19 = db.Column(db.String(255), default='healthy')
    l20 = db.Column(db.String(255), default='healthy')
    l21 = db.Column(db.String(255), default='healthy')
    l22 = db.Column(db.String(255), default='healthy')
    l23 = db.Column(db.String(255), default='healthy')
    l24 = db.Column(db.String(255), default='healthy')
    l25 = db.Column(db.String(255), default='healthy')
    l26 = db.Column(db.String(255), default='healthy')
    l27 = db.Column(db.String(255), default='healthy')
    l28 = db.Column(db.String(255), default='healthy')
    l29 = db.Column(db.String(255), default='healthy')
    l30 = db.Column(db.String(255), default='healthy')
    l31 = db.Column(db.String(255), default='healthy')
    l32 = db.Column(db.String(255), default='healthy')
    is_deleted = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return f"<Teeth {self.tID}: {self.tpatname}>"
    
    def get_tooth_condition(self, tooth_number):
        """Get condition of a specific tooth"""
        return getattr(self, f'l{tooth_number}', 'healthy')
    
    def set_tooth_condition(self, tooth_number, condition):
        """Set condition of a specific tooth"""
        if 1 <= tooth_number <= 32:
            setattr(self, f'l{tooth_number}', condition)
            return True
        return False
    
    def get_all_teeth_conditions(self):
        """Get all teeth conditions as a dictionary"""
        conditions = {}
        for i in range(1, 33):
            conditions[i] = getattr(self, f'l{i}', 'healthy')
        return conditions
    
    def count_conditions(self):
        """Count teeth by condition"""
        conditions = self.get_all_teeth_conditions()
        count = {}
        for condition in conditions.values():
            count[condition] = count.get(condition, 0) + 1
        return count

# Add this utility function after the models
def create_initial_teeth_chart(patient_name):
    """Create initial teeth chart for a patient with all teeth healthy"""
    try:
        # Check if teeth chart already exists
        existing_chart = Teeth.query.filter_by(tpatname=patient_name, is_deleted=False).first()
        if existing_chart:
            return existing_chart
        
        # Get next ID
        max_id = db.session.query(db.func.max(Teeth.tID)).first()[0]
        next_id = 1 if max_id is None else max_id + 1
        
        # Create new teeth chart
        teeth_chart = Teeth(
            tID=next_id,
            tpatname=patient_name,
            is_deleted=False
        )
        
        db.session.add(teeth_chart)
        db.session.commit()
        
        return teeth_chart
    except Exception as e:
        db.session.rollback()
        print(f"Error creating teeth chart: {e}")
        return None

def get_teeth_chart_for_patient(patient_name):
    """Get or create teeth chart for a patient"""
    teeth_chart = Teeth.query.filter_by(tpatname=patient_name, is_deleted=False).first()
    if not teeth_chart:
        teeth_chart = create_initial_teeth_chart(patient_name)
    return teeth_chart

# Also update the import statement at the top of your app.py to include Teeth:
# from db_connector import app as db_app, db, Patient, Appointment, DentalChart, Inventory, RescheduleAppointment, Report, User, UserLog, Teeth, log_user_action

# Utility functions
def get_db_connection():
    """Get database connection instance"""
    return db

def log_user_action(user_id, action, details=None):
    """Log user action to the database"""
    try:
        new_log = UserLog(
            user_id=user_id,
            action=action,
            details=details
        )
        db.session.add(new_log)
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        print(f"Error logging user action: {e}")
        return False

def add_patient(name, email, address, cityzipcode, contact, religion, dob, gender, age, occupation, allergies):
    """Add a new patient to the database"""
    new_patient = Patient(
        patname=name,
        patemail=email,
        pataddress=address,
        patcityzipcode=cityzipcode,
        patcontact=contact,
        patreligion=religion,
        patdob=dob,
        patgender=gender,
        patage=age,
        patoccupation=occupation,
        patallergies=allergies
    )
    
    try:
        db.session.add(new_patient)
        db.session.commit()
        return True, new_patient.patId
    except Exception as e:
        db.session.rollback()
        return False, str(e)

def get_all_patients(include_deleted=False):
    """Get all patients from the database"""
    if include_deleted:
        return Patient.query.all()
    else:
        return Patient.query.filter_by(is_deleted=False).all()

def get_upcoming_appointments(from_date=None):
    """Get all upcoming appointments"""
    if from_date is None:
        from_date = date.today()
    
    return Appointment.query.filter(Appointment.appdate >= from_date).order_by(Appointment.appdate, Appointment.apptime).all()

# Initialize database tables
def init_database():
    """Initialize database tables"""
    try:
        with app.app_context():
            print("Creating database tables...")
            db.create_all()
            print("✅ Database tables created successfully!")
            return True
    except Exception as e:
        print(f"❌ Error creating database tables: {str(e)}")
        return False

# Main execution
if __name__ == "__main__":
    print("Pullan Dental Clinic - Database Connector")
    print("="*50)
    
    with app.app_context():
        # Test connection
        if test_database_connection():
            print("\n🎉 Database connection successful!")
            
            # Initialize tables
            if init_database():
                print("🎉 Database setup complete!")
            else:
                print("❌ Database setup failed!")
        else:
            print("\n❌ Database connection failed!")
            print("\nTroubleshooting steps:")
            print("1. Check if MySQL service is running")
            print("2. Verify username and password")
            print("3. Ensure database 'pullandentalclinic' exists")
            print("4. Check if port 3306 is accessible")