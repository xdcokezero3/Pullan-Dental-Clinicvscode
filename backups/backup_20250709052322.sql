-- Database Backup for: pullan_dental_db
-- Generated on: 2025-07-09 05:23:24
-- By: Pullan Dental Clinic Management System
-- PostgreSQL Version: 160009
-- Host: dpg-d1er2l3e5dus739sktvg-a.oregon-postgres.render.com:5432

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;

DROP DATABASE IF EXISTS pullan_dental_db;
CREATE DATABASE pullan_dental_db WITH TEMPLATE = template0 ENCODING = 'UTF8';
\connect pullan_dental_db;

SET search_path = pullandentalclinic, public;

-- Table structure for table appointment
DROP TABLE IF EXISTS pullandentalclinic.appointment;
CREATE TABLE pullandentalclinic.appointment (
    appid integer NOT NULL DEFAULT nextval('pullandentalclinic.appointment_appid_seq'::regclass),
    apppatient character varying,
    apptime character varying,
    status character varying DEFAULT 'active'::character varying,
    appdate date
);

-- Dumping data for table appointment (2 rows)
INSERT INTO pullandentalclinic.appointment (appid, apppatient, apptime, status, appdate) VALUES
(2, 'Patient Man', '16:00', 'active', '2025-07-09'),
(1, 'Rad Cabodil', '09:10', 'active', '2025-09-09');

-- Table structure for table dentalchart
DROP TABLE IF EXISTS pullandentalclinic.dentalchart;
CREATE TABLE pullandentalclinic.dentalchart (
    dcID integer NOT NULL,
    dcpatname character varying,
    dcdoctor character varying,
    dcpcontact character varying,
    dcdentist character varying,
    dcdcontact character varying,
    dcvisit character varying,
    dcq1 character varying,
    dcq2 character varying,
    dcqe2 character varying,
    dcq3 character varying,
    dcqe3 character varying,
    dcq4 character varying,
    dcqe4 character varying,
    dcq5 character varying,
    dcqe5 character varying,
    dcq6 character varying,
    dcq7 character varying,
    dcqe7 character varying,
    dcq8 character varying,
    dcqe8 character varying,
    dcq9 character varying,
    dcqe9 character varying,
    is_deleted boolean DEFAULT false
);

-- Dumping data for table dentalchart (1 rows)
INSERT INTO pullandentalclinic.dentalchart (dcID, dcpatname, dcdoctor, dcpcontact, dcdentist, dcdcontact, dcvisit, dcq1, dcq2, dcqe2, dcq3, dcqe3, dcq4, dcqe4, dcq5, dcqe5, dcq6, dcq7, dcqe7, dcq8, dcqe8, dcq9, dcqe9, is_deleted) VALUES
(1, 'Rad Cabodil', 'Doctor Cocktor', '12345678901', 'DoctorMagnet', '12345678901', NULL, 'No', 'No', '', 'No', '', 'No', '', 'No', '', 'No', NULL, NULL, NULL, NULL, NULL, NULL, False);

-- Table structure for table inventory
DROP TABLE IF EXISTS pullandentalclinic.inventory;
CREATE TABLE pullandentalclinic.inventory (
    invid integer NOT NULL DEFAULT nextval('pullandentalclinic.inventory_invid_seq'::regclass),
    invname character varying,
    invquantity integer,
    invdoe date,
    invtype character varying,
    invremarks character varying,
    is_deleted boolean DEFAULT false
);

-- Dumping data for table inventory (2 rows)
INSERT INTO pullandentalclinic.inventory (invid, invname, invquantity, invdoe, invtype, invremarks, is_deleted) VALUES
(2, 'Second Aid', 100, '2025-07-08', 'Medicines', '', False),
(1, 'First Aid', 4, NULL, 'Equipment', '', False);

-- Table structure for table patients
DROP TABLE IF EXISTS pullandentalclinic.patients;
CREATE TABLE pullandentalclinic.patients (
    patId integer NOT NULL DEFAULT nextval('pullandentalclinic."patients_patId_seq"'::regclass),
    patname character varying NOT NULL,
    patemail character varying,
    pataddress character varying,
    patcityzipcode character varying,
    patcontact character varying,
    patreligion character varying,
    patdob date,
    patgender character varying,
    patage integer,
    patoccupation character varying,
    patallergies character varying,
    is_deleted boolean DEFAULT false,
    last_visit date,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);

-- Dumping data for table patients (2 rows)
INSERT INTO pullandentalclinic.patients (patId, patname, patemail, pataddress, patcityzipcode, patcontact, patreligion, patdob, patgender, patage, patoccupation, patallergies, is_deleted, last_visit, created_at) VALUES
(1, 'Rad Cabodil', 'rad@yahoo.com', 'Marikina', '1802', '12345678901', 'RC', '2004-08-06', 'Male', 20, 'Dentist', 'RC', False, NULL, '2025-07-08 20:40:22.373375'),
(2, 'Patient Man', 'patient@yahoo.com', 'Marikina', '1802', '12345678901', 'RC', '2001-11-06', 'Male', 23, 'Dentist', 'RC', False, NULL, '2025-07-08 20:58:21.434566');

-- Table structure for table rappointment
DROP TABLE IF EXISTS pullandentalclinic.rappointment;
CREATE TABLE pullandentalclinic.rappointment (
    rappid integer NOT NULL,
    rapppatient character varying,
    rapptime character varying,
    rappdate date,
    rappnewtime character varying,
    rappnewdate date,
    rappreason character varying
);

-- Dumping data for table rappointment (1 rows)
INSERT INTO pullandentalclinic.rappointment (rappid, rapppatient, rapptime, rappdate, rappnewtime, rappnewdate, rappreason) VALUES
(1, 'Rad Cabodil', '09:10', '2025-07-09', '09:10', '2025-09-09', '');

-- Table structure for table reports
DROP TABLE IF EXISTS pullandentalclinic.reports;
CREATE TABLE pullandentalclinic.reports (
    repid integer NOT NULL,
    reppatient character varying,
    repdate date,
    repprescription character varying,
    repcleaning integer,
    repextraction integer,
    reprootcanal integer,
    repbraces integer,
    repdentures integer,
    repdentist character varying,
    repothers character varying
);

-- No data for table reports

-- Table structure for table teeth
DROP TABLE IF EXISTS pullandentalclinic.teeth;
CREATE TABLE pullandentalclinic.teeth (
    tID integer NOT NULL,
    tpatname character varying,
    l1 character varying,
    l2 character varying,
    l3 character varying,
    l4 character varying,
    l5 character varying,
    l6 character varying,
    l7 character varying,
    l8 character varying,
    l9 character varying,
    l10 character varying,
    l11 character varying,
    l12 character varying,
    l13 character varying,
    l14 character varying,
    l15 character varying,
    l16 character varying,
    l17 character varying,
    l18 character varying,
    l19 character varying,
    l20 character varying,
    l21 character varying,
    l22 character varying,
    l23 character varying,
    l24 character varying,
    l25 character varying,
    l26 character varying,
    l27 character varying,
    l28 character varying,
    l29 character varying,
    l30 character varying,
    l31 character varying,
    l32 character varying,
    is_deleted boolean DEFAULT false
);

-- Dumping data for table teeth (1 rows)
INSERT INTO pullandentalclinic.teeth (tID, tpatname, l1, l2, l3, l4, l5, l6, l7, l8, l9, l10, l11, l12, l13, l14, l15, l16, l17, l18, l19, l20, l21, l22, l23, l24, l25, l26, l27, l28, l29, l30, l31, l32, is_deleted) VALUES
(1, 'Rad Cabodil', 'crown', 'root-canal', 'healthy', 'caries', 'healthy', 'healthy', 'filled', 'healthy', 'healthy', 'healthy', 'healthy', 'healthy', 'healthy', 'healthy', 'healthy', 'healthy', 'healthy', 'healthy', 'healthy', 'healthy', 'healthy', 'healthy', 'healthy', 'healthy', 'healthy', 'healthy', 'healthy', 'healthy', 'healthy', 'healthy', 'crown', 'healthy', False);

-- Table structure for table user_logs
DROP TABLE IF EXISTS pullandentalclinic.user_logs;
CREATE TABLE pullandentalclinic.user_logs (
    log_id integer NOT NULL DEFAULT nextval('pullandentalclinic.user_logs_log_id_seq'::regclass),
    user_id integer,
    action character varying,
    timestamp timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    details text
);

-- Dumping data for table user_logs (33 rows)
INSERT INTO pullandentalclinic.user_logs (log_id, user_id, action, timestamp, details) VALUES
(1, 0, 'Login', '2025-07-08 20:38:54.411485', 'Hardcoded admin logged in successfully'),
(2, 0, 'Create Inventory', '2025-07-08 20:39:20.098467', 'Added new inventory item: First Aid (Quantity: 100)'),
(3, 0, 'Create Staff', '2025-07-08 20:39:44.635220', 'Added new staff member: Louie Martin Averion (louie)'),
(4, 0, 'Create Patient', '2025-07-08 20:40:22.544808', 'Created new patient: Rad Cabodil (ID: PAT-001)'),
(5, 0, 'Create Appointment', '2025-07-08 20:40:40.418006', 'Created appointment for Rad Cabodil on 2025-07-09 at 09:10'),
(6, 0, 'Reschedule Appointment', '2025-07-08 20:41:02.920165', 'Rescheduled appointment for Rad Cabodil from 2025-07-09 09:10 to 2025-09-09 09:10. Reason: '),
(7, 0, 'Cancel Appointment', '2025-07-08 20:41:18.816016', 'Cancelled appointment for Rad Cabodil on 2025-09-09 at 09:10'),
(8, 0, 'Reactivate Appointment', '2025-07-08 20:41:25.401323', 'Reactivated appointment for Rad Cabodil on 2025-09-09 at 09:10'),
(9, 0, 'Create Dental Chart', '2025-07-08 20:42:22.355643', 'Created dental chart for Rad Cabodil (ID: PAT-001)'),
(10, 0, 'Update Tooth Condition', '2025-07-08 20:42:26.315766', 'Updated tooth #1 condition to "crown" for patient Rad Cabodil'),
(11, 0, 'Update Tooth Condition', '2025-07-08 20:42:27.521087', 'Updated tooth #2 condition to "root-canal" for patient Rad Cabodil'),
(12, 0, 'Update Tooth Condition', '2025-07-08 20:42:28.385532', 'Updated tooth #7 condition to "filled" for patient Rad Cabodil'),
(13, 0, 'Update Tooth Condition', '2025-07-08 20:42:29.472338', 'Updated tooth #4 condition to "caries" for patient Rad Cabodil'),
(14, 0, 'Update Tooth Condition', '2025-07-08 20:42:30.606371', 'Updated tooth #31 condition to "crown" for patient Rad Cabodil'),
(15, 0, 'Update Dental Chart', '2025-07-08 20:42:56.731124', 'Updated complete dental chart for patient Rad Cabodil'),
(16, 0, 'View FAQ Page', '2025-07-08 20:43:17.460701', 'User accessed FAQ and support page'),
(17, 0, 'View About Page', '2025-07-08 20:43:19.179291', 'User System Administrator viewed system about page'),
(18, 0, 'Logout', '2025-07-08 20:57:01.294220', 'Hardcoded admin logged out'),
(19, 0, 'Login', '2025-07-08 20:57:04.870682', 'Hardcoded admin logged in successfully'),
(20, 0, 'Login', '2025-07-08 20:57:25.998754', 'Hardcoded admin logged in successfully'),
(21, 0, 'Create Patient', '2025-07-08 20:58:20.708684', 'Created new patient: Patient Man (ID: PAT-002)'),
(22, 0, 'Create Appointment', '2025-07-08 20:58:43.673406', 'Created appointment for Patient Man on 2025-07-09 at 16:00'),
(23, 0, 'Cancel Appointment', '2025-07-08 20:59:12.701981', 'Cancelled appointment for Rad Cabodil on 2025-09-09 at 09:10'),
(24, 0, 'Reactivate Appointment', '2025-07-08 20:59:20.499890', 'Reactivated appointment for Rad Cabodil on 2025-09-09 at 09:10'),
(25, 0, 'View About Page', '2025-07-08 21:15:05.039122', 'User System Administrator viewed system about page'),
(26, 0, 'Logout', '2025-07-08 21:19:53.779332', 'Hardcoded admin logged out'),
(27, 0, 'Login', '2025-07-08 21:20:09.803136', 'Hardcoded admin logged in successfully'),
(28, 0, 'Create Inventory', '2025-07-08 21:20:54.211477', 'Added new inventory item: Second Aid (Quantity: 100)'),
(29, 0, 'Update Inventory', '2025-07-08 21:21:08.496357', 'Updated inventory item: Second Aid -> Second Aid (Quantity: 100 -> 100)'),
(30, 0, 'Update Inventory', '2025-07-08 21:21:54.099516', 'Updated inventory item: Second Aid -> Second Aid (Quantity: 100 -> 100)'),
(31, 0, 'Update Inventory', '2025-07-08 21:22:05.762335', 'Updated inventory item: Second Aid -> Second Aid (Quantity: 100 -> 4)'),
(32, 0, 'Update Inventory', '2025-07-08 21:22:26.537307', 'Updated inventory item: Second Aid -> Second Aid (Quantity: 4 -> 100)'),
(33, 0, 'Update Inventory', '2025-07-08 21:22:33.457804', 'Updated inventory item: First Aid -> First Aid (Quantity: 100 -> 4)');

-- Table structure for table users
DROP TABLE IF EXISTS pullandentalclinic.users;
CREATE TABLE pullandentalclinic.users (
    usersid integer NOT NULL DEFAULT nextval('pullandentalclinic.users_usersid_seq'::regclass),
    usersusername character varying NOT NULL,
    userspassword character varying NOT NULL,
    usersrealname character varying,
    usersemail character varying,
    usershomeaddress character varying,
    userscityzipcode character varying,
    userscontact character varying,
    usersreligion character varying,
    usersdob date,
    usersgender character varying,
    usersage integer,
    usersoccupation character varying,
    usersaccess character varying,
    key bytea,
    is_deleted boolean NOT NULL DEFAULT false
);

-- Dumping data for table users (1 rows)
INSERT INTO pullandentalclinic.users (usersid, usersusername, userspassword, usersrealname, usersemail, usershomeaddress, userscityzipcode, userscontact, usersreligion, usersdob, usersgender, usersage, usersoccupation, usersaccess, key, is_deleted) VALUES
(1, 'louie', '6c241236470212d37f015d5e4003ca0536d4f2b531361f440283c1e3aebeac5b', 'Louie Martin Averion', 'louie@yahoo.com', '#20 SAMPAGUITA, INDUSTRIAL VALLEY COMPLEX, MARIKINA CITY', '1802', '12345678901', 'RC', '2001-11-06', 'Male', 23, 'Dentist', 'admin', NULL, False);

-- Backup completed on 2025-07-09 05:23:30
