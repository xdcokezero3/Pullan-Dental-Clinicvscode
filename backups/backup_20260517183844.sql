-- Database Backup for: pullandental
-- Generated on: 2026-05-17 18:38:45
-- By: Pullan Dental Clinic Management System
-- PostgreSQL Version: 180003
-- Host: dpg-d84ob5btqb8s73fhch3g-a.oregon-postgres.render.com:5432

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;

DROP DATABASE IF EXISTS pullandental;
CREATE DATABASE pullandental WITH TEMPLATE = template0 ENCODING = 'UTF8';
\connect pullandental;

SET search_path = pullandentalclinic, public;

-- Table structure for table rappointment
DROP TABLE IF EXISTS pullandentalclinic.rappointment;
CREATE TABLE pullandentalclinic.rappointment (
    rappid integer NOT NULL DEFAULT nextval('pullandentalclinic.rappointment_rappid_seq'::regclass),
    rapppatient character varying,
    rapptime character varying,
    rappdate date,
    rappnewtime character varying,
    rappnewdate date,
    rappreason character varying
);

-- No data for table rappointment

-- Backup completed on 2026-05-17 18:38:46
