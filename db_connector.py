# db_connector.py
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import pymysql
from datetime import date

# This is needed for PyMySQL to work with SQLAlchemy
pymysql.install_as_MySQLdb()

app = Flask(__name__)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:root@127.0.0.1:3306/pullandentalclinic'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Create SQLAlchemy instance
db = SQLAlchemy(app)

# Function to get database connection
def get_db_connection():
    return db

# Optional: Function to test the database connection
def test_connection():
    try:
        # Try to execute a simple query
        result = db.engine.execute("SELECT 1")
        for row in result:
            print("Connection successful:", row[0])
        return True
    except Exception as e:
        print("Connection failed:", e)
        return False


# Define model classes for all tables in the database


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


# Example functions demonstrating how to use the models

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


# If this file is run directly, test the connection
if __name__ == "__main__":
    with app.app_context():
        test_connection()