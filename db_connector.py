# db_connector.py - PostgreSQL Version for pgAdmin 4 with Schema Fix
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import psycopg2
import os
import time
from datetime import date, datetime
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

# Create Flask app
app = Flask(__name__)

# Database configuration class for PostgreSQL
class DatabaseConfig:
    """Centralized PostgreSQL database configuration"""
    
    # PostgreSQL configuration - modify these to match your pgAdmin setup
    DB_USER = 'pullan_dental_db_user'  # Default PostgreSQL username
    DB_PASSWORD = 'HRZrgc3Zn9wJ1IhhqrOnvKTQy04f0CZH'  # Change this to your PostgreSQL password
    DB_NAME = 'pullan_dental_db'
    DB_HOST = 'dpg-d1er2l3e5dus739sktvg-a.oregon-postgres.render.com'
    DB_PORT = 5432  # Default PostgreSQL port
    DB_SCHEMA = 'pullandentalclinic'  # Add schema specification
    
    @classmethod
    def test_connection(cls, host, user, password, database, port):
        """Test if we can connect to PostgreSQL with given parameters"""
        try:
            # Test basic connection
            connection = psycopg2.connect(
                host=host,
                user=user,
                password=password,
                database=database,
                port=port,
                connect_timeout=10
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
        """Get PostgreSQL database URI with schema"""
        print("Testing PostgreSQL connection...")
        
        if cls.test_connection(cls.DB_HOST, cls.DB_USER, cls.DB_PASSWORD, cls.DB_NAME, cls.DB_PORT):
            # Add options to set search_path to include the correct schema
            uri = f"postgresql://{cls.DB_USER}:{cls.DB_PASSWORD}@{cls.DB_HOST}:{cls.DB_PORT}/{cls.DB_NAME}?options=-csearch_path%3D{cls.DB_SCHEMA}%2Cpublic"
            print(f"✅ Successfully connected to PostgreSQL at {cls.DB_HOST}:{cls.DB_PORT}")
            return uri
        
        # If connection fails, try connecting to default 'postgres' database
        print("Direct database connection failed. Trying default postgres database...")
        try:
            connection = psycopg2.connect(
                host=cls.DB_HOST,
                user=cls.DB_USER,
                password=cls.DB_PASSWORD,
                database='postgres',  # Default database
                port=cls.DB_PORT
            )
            
            # Try to create database if it doesn't exist
            connection.autocommit = True
            with connection.cursor() as cursor:
                cursor.execute(f"SELECT 1 FROM pg_catalog.pg_database WHERE datname = '{cls.DB_NAME}'")
                exists = cursor.fetchone()
                if not exists:
                    cursor.execute(f"CREATE DATABASE {cls.DB_NAME}")
                    print(f"Created database {cls.DB_NAME}")
            
            connection.close()
            uri = f"postgresql://{cls.DB_USER}:{cls.DB_PASSWORD}@{cls.DB_HOST}:{cls.DB_PORT}/{cls.DB_NAME}?options=-csearch_path%3D{cls.DB_SCHEMA}%2Cpublic"
            print(f"✅ Connected to PostgreSQL server and created/used database at {cls.DB_HOST}:{cls.DB_PORT}")
            return uri
            
        except Exception as e:
            print(f"Failed to connect to PostgreSQL server: {str(e)}")
            print("❌ All connection attempts failed!")
            print("Please check:")
            print("1. PostgreSQL service is running")
            print("2. Username and password are correct")
            print("3. Database exists or you have permission to create it")
            print("4. Port 5432 is not blocked")
            
            return f"postgresql://{cls.DB_USER}:{cls.DB_PASSWORD}@{cls.DB_HOST}:{cls.DB_PORT}/{cls.DB_NAME}?options=-csearch_path%3D{cls.DB_SCHEMA}%2Cpublic"

# Get working database URI
database_uri = DatabaseConfig.get_working_uri()

# Configure Flask app with PostgreSQL database settings
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
        'options': f'-csearch_path={DatabaseConfig.DB_SCHEMA},public'  # Set search_path
    }
}

# Initialize SQLAlchemy
db = SQLAlchemy(app)

# Test function for database connectivity
def test_database_connection():
    """Comprehensive database connection test"""
    print("\n" + "="*50)
    print("TESTING POSTGRESQL DATABASE CONNECTION")
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
            result = db.engine.execute(text("SELECT current_database()"))
            db_name = result.fetchone()[0]
            print(f"✅ Connected to database: {db_name}")
        
        # Test 3: Check current schema
        with app.app_context():
            result = db.engine.execute(text("SELECT current_schema()"))
            schema_name = result.fetchone()[0]
            print(f"✅ Current schema: {schema_name}")
        
        # Test 4: Check if patients table exists
        with app.app_context():
            result = db.engine.execute(text("""
                SELECT table_name, table_schema 
                FROM information_schema.tables 
                WHERE table_name = 'patients' 
                AND table_schema IN ('pullandentalclinic', 'public')
            """))
            tables = result.fetchall()
            if tables:
                for table in tables:
                    print(f"✅ Found patients table in schema: {table[1]}")
            else:
                print("❌ Patients table not found")
                return False
        
        # Test 5: Check if tables can be queried
        with app.app_context():
            try:
                result = db.engine.execute(text("SELECT COUNT(*) FROM patients"))
                count = result.fetchone()[0]
                print(f"✅ Patients table accessible: {count} records")
            except Exception as e:
                print(f"❌ Cannot query patients table: {e}")
                return False
        
        print("✅ All database tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {str(e)}")
        return False

# Database Models (Updated with explicit schema where needed)
class Patient(db.Model):
    __tablename__ = 'patients'
    __table_args__ = {'schema': 'pullandentalclinic'}  # Explicitly specify schema
    
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
    __table_args__ = {'schema': 'pullandentalclinic'}
    
    appid = db.Column(db.Integer, primary_key=True, autoincrement=True)
    apppatient = db.Column(db.String(100))
    apptime = db.Column(db.String(20))
    appdate = db.Column(db.Date)
    status = db.Column(db.String(20), default='active')
    
    def __repr__(self):
        return f'<Appointment {self.appid}: {self.apppatient} on {self.appdate} at {self.apptime} - {self.status}>'
    
    def formatted_id(self):
        return f"APT-{self.appid:03d}"

class RescheduleAppointment(db.Model):
    __tablename__ = 'rappointment'
    __table_args__ = {'schema': 'pullandentalclinic'}
    
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
    __table_args__ = {'schema': 'pullandentalclinic'}
    
    invid = db.Column(db.Integer, primary_key=True, autoincrement=True)
    invname = db.Column(db.String(100), nullable=False)
    invtype = db.Column(db.String(50))
    invquantity = db.Column(db.Integer, default=0)
    invdoe = db.Column(db.Date)  # Date of Expiry
    invremarks = db.Column(db.Text)
    is_deleted = db.Column(db.Boolean, default=False, nullable=False)
    
    def __repr__(self):
        return f'<Inventory {self.invname}>'
    
    def to_dict(self):
        return {
            'invid': self.invid,
            'invname': self.invname,
            'invtype': self.invtype,
            'invquantity': self.invquantity,
            'invdoe': self.invdoe.isoformat() if self.invdoe else None,
            'invremarks': self.invremarks,
            'is_deleted': self.is_deleted
        }
    
    @property
    def is_active(self):
        """Helper property to check if item is active"""
        return not self.is_deleted
    
    @property
    def status(self):
        """Helper property to get item status"""
        if self.is_deleted:
            return 'Inactive'
        elif self.invdoe and self.invdoe < datetime.now().date():
            return 'Expired'
        elif self.invquantity < 5:
            return 'Low Stock'
        else:
            return 'OK'

class User(db.Model):
    __tablename__ = 'users'
    __table_args__ = {'schema': 'pullandentalclinic'}
    
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
    is_deleted = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return f"<User {self.usersid}: {self.usersusername}>"

class UserLog(db.Model):
    __tablename__ = 'user_logs'
    __table_args__ = {'schema': 'pullandentalclinic'}
    
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
    __table_args__ = {'schema': 'pullandentalclinic'}
    
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
    __table_args__ = {'schema': 'pullandentalclinic'}
    
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

class Teeth(db.Model):
    __tablename__ = 'teeth'
    __table_args__ = {'schema': 'pullandentalclinic'}
    
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

def create_initial_teeth_chart(patient_name):
    """Create initial teeth chart for a patient with all teeth healthy"""
    try:
        existing_chart = Teeth.query.filter_by(tpatname=patient_name, is_deleted=False).first()
        if existing_chart:
            return existing_chart
        
        # For PostgreSQL, use sequence for auto-increment
        teeth_chart = Teeth(
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
    print("Pullan Dental Clinic - PostgreSQL Database Connector")
    print("="*60)
    
    with app.app_context():
        # Test connection
        if test_database_connection():
            print("\n🎉 PostgreSQL database connection successful!")
            
            # Initialize tables
            if init_database():
                print("🎉 Database setup complete!")
            else:
                print("❌ Database setup failed!")
        else:
            print("\n❌ PostgreSQL database connection failed!")
            print("\nTroubleshooting steps:")
            print("1. Check if PostgreSQL service is running")
            print("2. Verify username and password in DatabaseConfig class")
            print("3. Ensure database 'pullan_dental_db' exists in pgAdmin")
            print("4. Check if port 5432 is accessible")