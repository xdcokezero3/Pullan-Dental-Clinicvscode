# diagnostic_appointment.py - Diagnose the real issue
from flask import Flask
from sqlalchemy import text
import traceback

# Import your existing database configuration
from db_connector import app, db, Appointment

def diagnose_appointment_status():
    """Comprehensive diagnosis of appointment status issues"""
    print("DIAGNOSING APPOINTMENT STATUS ISSUES")
    print("=" * 50)
    
    try:
        with app.app_context():
            # Test 1: Check table structure
            print("1. Checking appointment table structure...")
            result = db.session.execute(text("DESCRIBE appointment"))
            columns = result.fetchall()
            
            print("Columns in appointment table:")
            for column in columns:
                print(f"  - {column[0]}: {column[1]} (Default: {column[4]})")
            
            status_column = next((col for col in columns if col[0] == 'status'), None)
            if status_column:
                print(f"✅ Status column exists: {status_column[1]}")
            else:
                print("❌ Status column missing!")
                return False
            
            # Test 2: Check current data
            print("\n2. Checking current appointment data...")
            appointments = db.session.execute(text("SELECT appid, apppatient, appdate, status FROM appointment LIMIT 5")).fetchall()
            
            if appointments:
                print("Sample appointments:")
                for apt in appointments:
                    print(f"  ID: {apt[0]}, Patient: {apt[1]}, Date: {apt[2]}, Status: {apt[3]}")
            else:
                print("❌ No appointments found!")
                return False
            
            # Test 3: Check status distribution
            print("\n3. Status distribution...")
            status_counts = db.session.execute(text("SELECT status, COUNT(*) FROM appointment GROUP BY status")).fetchall()
            
            for status, count in status_counts:
                print(f"  {status}: {count} appointments")
            
            # Test 4: Test SQLAlchemy model access
            print("\n4. Testing SQLAlchemy model access...")
            first_appointment = Appointment.query.first()
            
            if first_appointment:
                print(f"First appointment ID: {first_appointment.appid}")
                print(f"Patient: {first_appointment.apppatient}")
                
                # Try to access status attribute
                try:
                    current_status = first_appointment.status
                    print(f"✅ Status accessed via model: {current_status}")
                except AttributeError as e:
                    print(f"❌ Cannot access status via model: {e}")
                    print("This suggests the model definition is out of sync!")
                    return False
                
                # Test updating status
                try:
                    original_status = first_appointment.status
                    first_appointment.status = 'test'
                    db.session.commit()
                    
                    # Verify update
                    updated_appointment = Appointment.query.get(first_appointment.appid)
                    if updated_appointment.status == 'test':
                        print("✅ Status update test successful")
                        
                        # Reset back
                        updated_appointment.status = original_status
                        db.session.commit()
                        print("✅ Reset to original status")
                    else:
                        print("❌ Status update failed - change not reflected")
                        
                except Exception as update_error:
                    print(f"❌ Error during status update test: {update_error}")
                    db.session.rollback()
                    return False
            
            # Test 5: Test the actual cancel operation
            print("\n5. Testing cancel operation simulation...")
            test_appointment = Appointment.query.filter_by(status='active').first()
            
            if test_appointment:
                try:
                    print(f"Testing with appointment ID: {test_appointment.appid}")
                    test_appointment.status = 'cancelled'
                    db.session.commit()
                    
                    # Verify
                    verification = Appointment.query.get(test_appointment.appid)
                    if verification.status == 'cancelled':
                        print("✅ Cancel operation simulation successful")
                        
                        # Reset
                        verification.status = 'active'
                        db.session.commit()
                        print("✅ Reset to active")
                    else:
                        print("❌ Cancel operation failed")
                        
                except Exception as cancel_error:
                    print(f"❌ Error during cancel simulation: {cancel_error}")
                    print(f"Error type: {type(cancel_error)}")
                    print(f"Traceback: {traceback.format_exc()}")
                    db.session.rollback()
                    return False
            
            print("\n✅ All diagnostic tests passed!")
            return True
            
    except Exception as e:
        print(f"❌ Diagnostic failed: {e}")
        print(f"Error type: {type(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        return False

def check_model_definition():
    """Check if the Appointment model has the status field properly defined"""
    print("\n6. Checking model definition...")
    
    try:
        # Check if status is in the model's columns
        appointment_columns = Appointment.__table__.columns.keys()
        print(f"Model columns: {appointment_columns}")
        
        if 'status' in appointment_columns:
            print("✅ Status field is in model definition")
            
            # Check the column definition
            status_column = Appointment.__table__.columns['status']
            print(f"Status column type: {status_column.type}")
            print(f"Status column default: {status_column.default}")
            
            return True
        else:
            print("❌ Status field missing from model definition!")
            print("You need to restart your Flask application after adding the status field to the model!")
            return False
            
    except Exception as e:
        print(f"❌ Error checking model: {e}")
        return False

def suggest_fixes():
    """Suggest fixes based on the diagnostic results"""
    print("\nSUGGESTED FIXES:")
    print("=" * 20)
    
    print("1. Restart your Flask application completely")
    print("2. Check that db_connector.py has status field in Appointment model:")
    print("   status = db.Column(db.String(20), default='active')")
    print("3. Clear any SQLAlchemy metadata cache")
    print("4. Check for any typos in the cancel_appointment route")
    print("5. Enable Flask debug mode to see detailed error messages")

if __name__ == "__main__":
    if diagnose_appointment_status():
        check_model_definition()
        print("\n🎉 Diagnosis complete - everything looks good!")
        print("If you're still getting errors, the issue might be in the frontend JavaScript.")
    else:
        print("\n❌ Issues found during diagnosis")
        suggest_fixes()