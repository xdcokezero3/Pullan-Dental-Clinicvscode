#!/usr/bin/env python3
"""
MySQL Connection Diagnostic Tool
Run this script to diagnose and fix MySQL connection issues
"""

import pymysql
import socket
import subprocess
import os
import platform

class MySQLDiagnostic:
    def __init__(self):
        self.config = {
            'host_options': ['localhost', '127.0.0.1'],
            'user': 'root',
            'password': 'root',
            'database': 'pullandentalclinic',
            'port': 3306
        }
        
    def print_header(self, title):
        print("\n" + "="*60)
        print(f" {title}")
        print("="*60)
    
    def print_step(self, step_num, description):
        print(f"\n[Step {step_num}] {description}")
        print("-" * 40)
    
    def check_mysql_service(self):
        """Check if MySQL service is running"""
        self.print_step(1, "Checking MySQL Service Status")
        
        system = platform.system().lower()
        service_running = False
        
        try:
            if system == "windows":
                # Check Windows services
                result = subprocess.run(['sc', 'query', 'mysql'], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0 and 'RUNNING' in result.stdout:
                    print("✅ MySQL service is RUNNING")
                    service_running = True
                else:
                    print("❌ MySQL service is NOT RUNNING")
                    print("💡 Try running: net start mysql (as Administrator)")
                    
                # Also check for MySQL80 service
                result80 = subprocess.run(['sc', 'query', 'mysql80'], 
                                        capture_output=True, text=True, timeout=10)
                if result80.returncode == 0 and 'RUNNING' in result80.stdout:
                    print("✅ MySQL80 service is RUNNING")
                    service_running = True
                    
            else:
                # Check Linux/Mac services
                commands = [
                    ['systemctl', 'is-active', 'mysql'],
                    ['systemctl', 'is-active', 'mysqld'],
                    ['brew', 'services', 'list']  # For macOS with Homebrew
                ]
                
                for cmd in commands:
                    try:
                        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                        if result.returncode == 0:
                            print(f"✅ MySQL service found and running: {' '.join(cmd)}")
                            service_running = True
                            break
                    except (subprocess.SubprocessError, FileNotFoundError):
                        continue
                
                if not service_running:
                    print("❌ MySQL service not found or not running")
                    print("💡 Try: sudo systemctl start mysql")
                    
        except Exception as e:
            print(f"⚠️  Could not check service status: {e}")
            
        return service_running

    def check_port_connectivity(self):
        """Check if MySQL port is accessible"""
        self.print_step(2, "Checking Port Connectivity")
        
        accessible_hosts = []
        
        for host in self.config['host_options']:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                result = sock.connect_ex((host, self.config['port']))
                sock.close()
                
                if result == 0:
                    print(f"✅ Port {self.config['port']} is OPEN on {host}")
                    accessible_hosts.append(host)
                else:
                    print(f"❌ Port {self.config['port']} is CLOSED on {host}")
                    
            except Exception as e:
                print(f"❌ Cannot test {host}:{self.config['port']} - {e}")
        
        if not accessible_hosts:
            print("💡 MySQL port is not accessible. Check:")
            print("   - MySQL service is running")
            print("   - Firewall is not blocking port 3306")
            print("   - MySQL is configured to accept connections")
            
        return accessible_hosts

    def test_database_connections(self, accessible_hosts):
        """Test actual database connections"""
        self.print_step(3, "Testing Database Connections")
        
        working_connections = []
        
        for host in accessible_hosts:
            print(f"\nTesting connection to {host}...")
            
            # Test connection without database first
            try:
                connection = pymysql.connect(
                    host=host,
                    user=self.config['user'],
                    password=self.config['password'],
                    port=self.config['port'],
                    connect_timeout=10
                )
                
                with connection.cursor() as cursor:
                    cursor.execute("SELECT VERSION()")
                    version = cursor.fetchone()[0]
                    print(f"✅ Connected to MySQL {version} on {host}")
                    
                    # Check if database exists
                    cursor.execute(f"SHOW DATABASES LIKE '{self.config['database']}'")
                    db_exists = cursor.fetchone()
                    
                    if db_exists:
                        print(f"✅ Database '{self.config['database']}' exists")
                        
                        # Test connection with database
                        connection.close()
                        db_connection = pymysql.connect(
                            host=host,
                            user=self.config['user'],
                            password=self.config['password'],
                            database=self.config['database'],
                            port=self.config['port'],
                            connect_timeout=10
                        )
                        
                        with db_connection.cursor() as db_cursor:
                            db_cursor.execute("SELECT DATABASE()")
                            current_db = db_cursor.fetchone()[0]
                            print(f"✅ Successfully connected to database: {current_db}")
                            
                        db_connection.close()
                        working_connections.append(host)
                        
                    else:
                        print(f"⚠️  Database '{self.config['database']}' does not exist")
                        print(f"💡 Creating database '{self.config['database']}'...")
                        
                        try:
                            cursor.execute(f"CREATE DATABASE {self.config['database']}")
                            print(f"✅ Database '{self.config['database']}' created successfully")
                            working_connections.append(host)
                        except Exception as create_error:
                            print(f"❌ Failed to create database: {create_error}")
                
                connection.close()
                
            except Exception as e:
                print(f"❌ Connection failed to {host}: {e}")
                
                if "Access denied" in str(e):
                    print("💡 Check username and password")
                elif "Unknown database" in str(e):
                    print(f"💡 Database '{self.config['database']}' needs to be created")
                    
        return working_connections

    def generate_flask_config(self, working_hosts):
        """Generate Flask database configuration"""
        self.print_step(4, "Generating Flask Configuration")
        
        if working_hosts:
            best_host = working_hosts[0]  # Use first working host
            
            flask_uri = f"mysql+pymysql://{self.config['user']}:{self.config['password']}@{best_host}:{self.config['port']}/{self.config['database']}"
            
            print("✅ Recommended Flask-SQLAlchemy configuration:")
            print(f"SQLALCHEMY_DATABASE_URI = '{flask_uri}'")
            
            print("\n📋 Copy this configuration to your db_connector.py:")
            print("-" * 50)
            print(f"app.config['SQLALCHEMY_DATABASE_URI'] = '{flask_uri}'")
            print("app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False")
            
            return flask_uri
        else:
            print("❌ No working database connections found")
            return None

    def run_full_diagnostic(self):
        """Run complete diagnostic sequence"""
        self.print_header("MySQL Connection Diagnostic Tool")
        print("This tool will help diagnose and fix MySQL connection issues.")
        
        # Step 1: Check MySQL service
        service_running = self.check_mysql_service()
        
        # Step 2: Check port connectivity
        accessible_hosts = self.check_port_connectivity()
        
        if not accessible_hosts:
            print("\n❌ DIAGNOSIS: MySQL service is not accessible")
            print("🔧 SOLUTION: Start MySQL service and check firewall settings")
            return False
            
        # Step 3: Test database connections
        working_hosts = self.test_database_connections(accessible_hosts)
        
        if not working_hosts:
            print("\n❌ DIAGNOSIS: Cannot authenticate with MySQL")
            print("🔧 SOLUTION: Check username, password, and database permissions")
            return False
            
        # Step 4: Generate Flask config
        flask_uri = self.generate_flask_config(working_hosts)
        
        if flask_uri:
            print("\n🎉 SUCCESS: MySQL connection is working!")
            print("✨ You can now use the generated configuration in your Flask app")
            return True
        else:
            return False

def main():
    diagnostic = MySQLDiagnostic()
    success = diagnostic.run_full_diagnostic()
    
    if success:
        print("\n" + "="*60)
        print("🎉 Diagnostic completed successfully!")
        print("Your MySQL connection should now work with Flask.")
        print("="*60)
    else:
        print("\n" + "="*60)
        print("❌ Issues found that need to be resolved:")
        print("1. Ensure MySQL is installed and running")
        print("2. Check username/password (default: root/root)")
        print("3. Create database 'pullandentalclinic' if needed")
        print("4. Check firewall settings for port 3306")
        print("="*60)

if __name__ == "__main__":
    main()