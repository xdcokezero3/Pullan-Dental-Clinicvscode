-- Database Backup for: pullan_dental_db
-- Generated on: 2025-07-08 16:37:28
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

-- Dumping data for table appointment (8 rows)
INSERT INTO pullandentalclinic.appointment (appid, apppatient, apptime, status, appdate) VALUES
(1, 'HEYY', '07:00', 'completed', '2025-07-02'),
(2, 'HEYY', '01:00', 'completed', '2025-07-02'),
(3, 'loe', '06:00', 'completed', '2025-08-07'),
(4, 'loe', '20:00', 'completed', '2025-07-03'),
(5, 'TEST', '21:00', 'completed', '2025-07-06'),
(6, 'loe', '20:00', 'completed', '2025-08-06'),
(7, 'loe', '22:00', 'completed', '2025-07-06'),
(8, 'loe', '23:00', 'cancelled', '2025-07-06');

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

-- Dumping data for table dentalchart (3 rows)
INSERT INTO pullandentalclinic.dentalchart (dcID, dcpatname, dcdoctor, dcpcontact, dcdentist, dcdcontact, dcvisit, dcq1, dcq2, dcqe2, dcq3, dcqe3, dcq4, dcqe4, dcq5, dcqe5, dcq6, dcq7, dcqe7, dcq8, dcqe8, dcq9, dcqe9, is_deleted) VALUES
(1, 'HEYY', 'Yo', '12345678901', 'Yo', '12345678901', NULL, 'Yes', 'Yes', 'das', 'Yes', 'das', 'Yes', 'das', 'Yes', 'das', 'Yes', NULL, NULL, NULL, NULL, NULL, NULL, False),
(2, 'loe', 'yo', '09166532911', 'yo', '12345678901', NULL, 'Yes', 'Yes', '12', 'Yes', '12', 'Yes', '12', 'Yes', '12', 'Yes', NULL, NULL, NULL, NULL, NULL, NULL, False),
(3, 'TEST', '', '12345678901', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', False);

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

-- Dumping data for table inventory (1 rows)
INSERT INTO pullandentalclinic.inventory (invid, invname, invquantity, invdoe, invtype, invremarks, is_deleted) VALUES
(4, 'dsad', 22, NULL, 'Equipment', '', False);

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

-- Dumping data for table patients (3 rows)
INSERT INTO pullandentalclinic.patients (patId, patname, patemail, pataddress, patcityzipcode, patcontact, patreligion, patdob, patgender, patage, patoccupation, patallergies, is_deleted, last_visit, created_at) VALUES
(1, 'HEYY', 'hey@gmail.com', '#20 SAMPAGUITA, INDUSTRIAL VALLEY COMPLEX, MARIKINA CITY', '1802', '12345678901', 'RC', '2001-11-06', 'Male', 23, 'hello', '11', False, NULL, '2025-07-01 11:27:17'),
(2, 'loe', 'loe@yahoo.com', 'Marikina', '1802', '09166532911', 'RC', '2001-02-22', 'Male', 22, 'FAKE', 'RC', False, NULL, '2025-07-02 12:38:51'),
(3, 'TEST', 'hey@gmail.com', '#20 SAMPAGUITA, INDUSTRIAL VALLEY COMPLEX, MARIKINA CITY', '1802', '12345678901', 'RC', '2001-11-06', 'Male', 22, 'FAKE', 'RC', False, NULL, '2025-07-03 17:48:31');

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

-- Dumping data for table rappointment (3 rows)
INSERT INTO pullandentalclinic.rappointment (rappid, rapppatient, rapptime, rappdate, rappnewtime, rappnewdate, rappreason) VALUES
(1, 'loe', '06:00', '2025-07-24', '06:00', '2025-08-07', ''),
(2, 'loe', '21:00', '2025-07-06', '21:00', '2025-07-07', ''),
(3, 'loe', '21:00', '2025-07-07', '22:00', '2025-07-06', '');

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

-- Dumping data for table teeth (3 rows)
INSERT INTO pullandentalclinic.teeth (tID, tpatname, l1, l2, l3, l4, l5, l6, l7, l8, l9, l10, l11, l12, l13, l14, l15, l16, l17, l18, l19, l20, l21, l22, l23, l24, l25, l26, l27, l28, l29, l30, l31, l32, is_deleted) VALUES
(1, 'HEYY', 'extracted', 'root-canal', 'caries', 'crown', 'implant', 'healthy', 'filled', 'root-canal', 'crown', 'filled', 'caries', 'healthy', 'crown', 'crown', 'implant', 'crown', 'crown', 'caries', 'filled', 'extracted', 'filled', 'extracted', 'crown', 'filled', 'caries', 'crown', 'root-canal', 'extracted', 'filled', 'crown', 'crown', 'extracted', False),
(2, 'loe', 'filled', 'root-canal', 'root-canal', 'caries', 'implant', 'caries', 'crown', 'root-canal', 'crown', 'filled', 'healthy', 'healthy', 'extracted', 'root-canal', 'crown', 'healthy', 'root-canal', 'extracted', 'filled', 'healthy', 'extracted', 'crown', 'healthy', 'healthy', 'root-canal', 'filled', 'crown', 'crown', 'filled', 'filled', 'filled', 'root-canal', False),
(3, 'TEST', 'healthy', 'caries', 'filled', 'healthy', 'crown', 'implant', 'crown', 'healthy', 'filled', 'healthy', 'root-canal', 'crown', 'healthy', 'caries', 'healthy', 'healthy', 'extracted', 'healthy', 'root-canal', 'healthy', 'healthy', 'crown', 'healthy', 'crown', 'healthy', 'filled', 'caries', 'extracted', 'crown', 'healthy', 'implant', 'healthy', False);

-- Table structure for table user_logs
DROP TABLE IF EXISTS pullandentalclinic.user_logs;
CREATE TABLE pullandentalclinic.user_logs (
    log_id integer NOT NULL DEFAULT nextval('pullandentalclinic.user_logs_log_id_seq'::regclass),
    user_id integer,
    action character varying,
    timestamp timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    details text
);

-- Dumping data for table user_logs (42 rows)
INSERT INTO pullandentalclinic.user_logs (log_id, user_id, action, timestamp, details) VALUES
(1, 0, 'Logout', '2025-07-01 03:12:55', 'Hardcoded admin logged out'),
(2, 0, 'Login', '2025-07-01 03:13:25', 'Hardcoded admin logged in successfully'),
(3, 0, 'Export Logs', '2025-07-01 03:13:43', 'User exported 2 log entries'),
(4, 0, 'Logout', '2025-07-01 03:16:40', 'Hardcoded admin logged out'),
(5, 0, 'Login', '2025-07-01 03:16:43', 'Hardcoded admin logged in successfully'),
(6, 0, 'Print Staff Report', '2025-07-01 03:23:05', 'Generated staff report: 0 staff members (Status: Active Staff Only)'),
(7, 0, 'Logout', '2025-07-01 03:25:19', 'Hardcoded admin logged out'),
(8, 1, 'User Registration', '2025-07-01 03:25:51', 'New user registered: loe (loe)'),
(9, 1, 'Login', '2025-07-01 03:25:55', 'User loe logged in successfully'),
(10, 1, 'Print Staff Report', '2025-07-01 03:26:01', 'Generated staff report: 1 staff members (Status: Active Staff Only)'),
(11, 1, 'Logout', '2025-07-01 03:26:05', 'User loe logged out'),
(12, 0, 'Login', '2025-07-01 03:26:10', 'Hardcoded admin logged in successfully'),
(13, 0, 'Update Staff', '2025-07-01 03:26:20', 'Updated staff member: loe -> loe (loe)'),
(14, 0, 'Logout', '2025-07-01 03:26:22', 'Hardcoded admin logged out'),
(15, 1, 'Login', '2025-07-01 03:26:29', 'User loe logged in successfully'),
(16, 1, 'Create Patient', '2025-07-01 03:27:18', 'Created new patient: HEYY (ID: PAT-001)'),
(17, 1, 'Create Dental Chart', '2025-07-01 03:27:32', 'Created dental chart for HEYY (ID: PAT-001)'),
(18, 1, 'Update Tooth Condition', '2025-07-01 03:27:35', 'Updated tooth #2 condition to "root-canal" for patient HEYY'),
(19, 1, 'Update Tooth Condition', '2025-07-01 03:27:36', 'Updated tooth #7 condition to "filled" for patient HEYY'),
(20, 1, 'Update Tooth Condition', '2025-07-01 03:27:37', 'Updated tooth #3 condition to "caries" for patient HEYY'),
(331, 0, 'Logout', '2025-07-08 08:22:10.868501', 'Hardcoded admin logged out'),
(332, 0, 'Login', '2025-07-08 08:22:15.966213', 'Hardcoded admin logged in successfully'),
(333, 0, 'Delete Backup', '2025-07-08 08:22:24.359756', 'Deleted backup file: backup_20250708092925.sql'),
(334, 0, 'Delete Backup', '2025-07-08 08:22:26.798405', 'Deleted backup file: backup_20250708091803.sql'),
(335, 0, 'Delete Backup', '2025-07-08 08:22:28.742904', 'Deleted backup file: backup_20250708090339.sql'),
(336, 0, 'Database Backup', '2025-07-08 08:22:35.980450', 'Created PostgreSQL database backup: backup_20250708082232.sql (0.02 MB)'),
(337, 0, 'Deactivate Patient', '2025-07-08 08:22:40.684120', 'Deactivated patient: HEYY (ID: PAT-001)'),
(340, 0, 'Reactivate Patient', '2025-07-08 08:23:56.179679', 'Reactivated patient: TEST (ID: PAT-003)'),
(341, 0, 'Delete Backup', '2025-07-08 08:24:07.011200', 'Deleted backup file: backup_20250708082232.sql'),
(342, 0, 'Login', '2025-07-08 08:28:49.590059', 'Hardcoded admin logged in successfully'),
(343, 0, 'Delete Backup', '2025-07-08 08:28:59.562919', 'Deleted backup file: backup_20250708092925.sql'),
(344, 0, 'Delete Backup', '2025-07-08 08:29:01.559394', 'Deleted backup file: backup_20250708091803.sql'),
(345, 0, 'Delete Backup', '2025-07-08 08:29:03.737762', 'Deleted backup file: backup_20250708090339.sql'),
(346, 0, 'Database Backup', '2025-07-08 08:29:15.170571', 'Created PostgreSQL database backup: backup_20250708162908.sql (0.01 MB)'),
(347, 0, 'Deactivate Patient', '2025-07-08 08:29:22.013944', 'Deactivated patient: TEST (ID: PAT-003)'),
(348, 0, 'Delete Backup', '2025-07-08 08:30:02.186891', 'Deleted backup file: backup_20250708162908.sql'),
(349, 0, 'Database Backup', '2025-07-08 08:30:18.649683', 'Created PostgreSQL database backup: backup_20250708163011.sql (0.01 MB)'),
(350, 0, 'Reactivate Patient', '2025-07-08 08:30:30.965470', 'Reactivated patient: TEST (ID: PAT-003)'),
(351, 0, 'Login', '2025-07-08 08:37:12.184765', 'Hardcoded admin logged in successfully'),
(352, 0, 'Delete Backup', '2025-07-08 08:37:24.212996', 'Deleted backup file: backup_20250708163011.sql'),
(338, 0, 'Deactivate Patient', '2025-07-08 08:23:18.113583', 'Deactivated patient: loe (ID: PAT-002)'),
(339, 0, 'Deactivate Patient', '2025-07-08 08:23:22.074104', 'Deactivated patient: TEST (ID: PAT-003)');

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

-- Dumping data for table users (2 rows)
INSERT INTO pullandentalclinic.users (usersid, usersusername, userspassword, usersrealname, usersemail, usershomeaddress, userscityzipcode, userscontact, usersreligion, usersdob, usersgender, usersage, usersoccupation, usersaccess, key, is_deleted) VALUES
(1, 'loe', '6c241236470212d37f015d5e4003ca0536d4f2b531361f440283c1e3aebeac5b', 'loe', 'loe@yahoo.com', 'Marikina', '1802', '09166532911', 'RC', '2001-11-06', 'Male', 23, 'Arsonist', 'admin', NULL, False),
(2, '123', 'a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3', '123', '123@yahoo.com', '#20 SAMPAGUITA, INDUSTRIAL VALLEY COMPLEX, MARIKINA CITY', '1802', '13123123123', 'RC', '2001-11-06', 'Male', 23, 'Arsonist', 'user', NULL, False);

-- Backup completed on 2025-07-08 16:37:33
