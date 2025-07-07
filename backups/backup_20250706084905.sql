-- Database Backup for: pullandentalclinic
-- Generated on: 2025-07-06 08:49:05
-- By: Pullan Dental Clinic Management System
-- MySQL Version: 8.0.42
-- Host: localhost:3306

SET FOREIGN_KEY_CHECKS=0;
SET SQL_MODE = 'NO_AUTO_VALUE_ON_ZERO';
SET AUTOCOMMIT = 0;
START TRANSACTION;
SET time_zone = '+00:00';

DROP DATABASE IF EXISTS `pullandentalclinic`;
CREATE DATABASE `pullandentalclinic` CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
USE `pullandentalclinic`;

-- Table structure for table `appointment`
DROP TABLE IF EXISTS `appointment`;
CREATE TABLE `appointment` (
  `appid` int NOT NULL AUTO_INCREMENT,
  `apppatient` varchar(255) DEFAULT NULL,
  `apptime` varchar(255) DEFAULT NULL,
  `status` varchar(20) DEFAULT 'active',
  `appdate` date DEFAULT NULL,
  PRIMARY KEY (`appid`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Dumping data for table `appointment` (4 rows)
INSERT INTO `appointment` (`appid`, `apppatient`, `apptime`, `status`, `appdate`) VALUES
(1, 'HEYY', '07:00', 'completed', '2025-07-02 00:00:00'),
(2, 'HEYY', '01:00', 'completed', '2025-07-02 00:00:00'),
(3, 'loe', '06:00', 'active', '2025-07-24 00:00:00'),
(4, 'loe', '20:00', 'active', '2025-07-03 00:00:00');

-- Table structure for table `dentalchart`
DROP TABLE IF EXISTS `dentalchart`;
CREATE TABLE `dentalchart` (
  `dcID` int NOT NULL,
  `dcpatname` varchar(255) DEFAULT NULL,
  `dcdoctor` varchar(255) DEFAULT NULL,
  `dcpcontact` varchar(255) DEFAULT NULL,
  `dcdentist` varchar(255) DEFAULT NULL,
  `dcdcontact` varchar(255) DEFAULT NULL,
  `dcvisit` varchar(255) DEFAULT NULL,
  `dcq1` varchar(255) DEFAULT NULL,
  `dcq2` varchar(255) DEFAULT NULL,
  `dcqe2` varchar(255) DEFAULT NULL,
  `dcq3` varchar(255) DEFAULT NULL,
  `dcqe3` varchar(255) DEFAULT NULL,
  `dcq4` varchar(255) DEFAULT NULL,
  `dcqe4` varchar(255) DEFAULT NULL,
  `dcq5` varchar(255) DEFAULT NULL,
  `dcqe5` varchar(255) DEFAULT NULL,
  `dcq6` varchar(255) DEFAULT NULL,
  `dcq7` varchar(255) DEFAULT NULL,
  `dcqe7` varchar(255) DEFAULT NULL,
  `dcq8` varchar(255) DEFAULT NULL,
  `dcqe8` varchar(255) DEFAULT NULL,
  `dcq9` varchar(255) DEFAULT NULL,
  `dcqe9` varchar(255) DEFAULT NULL,
  `is_deleted` tinyint(1) DEFAULT '0',
  PRIMARY KEY (`dcID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Dumping data for table `dentalchart` (3 rows)
INSERT INTO `dentalchart` (`dcID`, `dcpatname`, `dcdoctor`, `dcpcontact`, `dcdentist`, `dcdcontact`, `dcvisit`, `dcq1`, `dcq2`, `dcqe2`, `dcq3`, `dcqe3`, `dcq4`, `dcqe4`, `dcq5`, `dcqe5`, `dcq6`, `dcq7`, `dcqe7`, `dcq8`, `dcqe8`, `dcq9`, `dcqe9`, `is_deleted`) VALUES
(1, 'HEYY', 'Yo', '12345678901', 'Yo', '12345678901', NULL, 'Yes', 'Yes', 'das', 'Yes', 'das', 'Yes', 'das', 'Yes', 'das', 'Yes', NULL, NULL, NULL, NULL, NULL, NULL, 0),
(2, 'loe', 'yo', '09166532911', 'yo', '12345678901', NULL, 'Yes', 'Yes', '12', 'Yes', '12', 'Yes', '12', 'Yes', '12', 'Yes', NULL, NULL, NULL, NULL, NULL, NULL, 0),
(3, 'TEST', '', '12345678901', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', 0);

-- Table structure for table `inventory`
DROP TABLE IF EXISTS `inventory`;
CREATE TABLE `inventory` (
  `invid` int NOT NULL AUTO_INCREMENT,
  `invname` varchar(255) DEFAULT NULL,
  `invquantity` int DEFAULT NULL,
  `invdoe` date DEFAULT NULL,
  `invtype` varchar(255) DEFAULT NULL,
  `invremarks` varchar(255) DEFAULT NULL,
  `is_deleted` tinyint DEFAULT '0',
  PRIMARY KEY (`invid`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Dumping data for table `inventory` (1 rows)
INSERT INTO `inventory` (`invid`, `invname`, `invquantity`, `invdoe`, `invtype`, `invremarks`, `is_deleted`) VALUES
(4, 'dsad', 22, NULL, 'Equipment', '', 0);

-- Table structure for table `patients`
DROP TABLE IF EXISTS `patients`;
CREATE TABLE `patients` (
  `patId` int NOT NULL AUTO_INCREMENT,
  `patname` varchar(100) NOT NULL,
  `patemail` varchar(100) DEFAULT NULL,
  `pataddress` varchar(255) DEFAULT NULL,
  `patcityzipcode` varchar(20) DEFAULT NULL,
  `patcontact` varchar(20) DEFAULT NULL,
  `patreligion` varchar(50) DEFAULT NULL,
  `patdob` date DEFAULT NULL,
  `patgender` varchar(10) DEFAULT NULL,
  `patage` int DEFAULT NULL,
  `patoccupation` varchar(100) DEFAULT NULL,
  `patallergies` varchar(255) DEFAULT NULL,
  `is_deleted` tinyint(1) DEFAULT '0',
  `last_visit` date DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`patId`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Dumping data for table `patients` (3 rows)
INSERT INTO `patients` (`patId`, `patname`, `patemail`, `pataddress`, `patcityzipcode`, `patcontact`, `patreligion`, `patdob`, `patgender`, `patage`, `patoccupation`, `patallergies`, `is_deleted`, `last_visit`, `created_at`) VALUES
(1, 'HEYY', 'hey@gmail.com', '#20 SAMPAGUITA, INDUSTRIAL VALLEY COMPLEX, MARIKINA CITY', '1802', '12345678901', 'RC', '2001-11-06 00:00:00', 'Male', NULL, 'hello', '11', 0, NULL, '2025-07-01 11:27:17'),
(2, 'loe', 'loe@yahoo.com', 'Marikina', '1802', '09166532911', 'RC', '2001-02-22 00:00:00', 'Male', 22, 'FAKE', 'RC', 0, NULL, '2025-07-02 12:38:51'),
(3, 'TEST', 'hey@gmail.com', '#20 SAMPAGUITA, INDUSTRIAL VALLEY COMPLEX, MARIKINA CITY', '1802', '12345678901', 'RC', '2001-11-06 00:00:00', 'Male', 22, 'FAKE', 'RC', 0, NULL, '2025-07-03 17:48:31');

-- Table structure for table `rappointment`
DROP TABLE IF EXISTS `rappointment`;
CREATE TABLE `rappointment` (
  `rappid` int NOT NULL,
  `rapppatient` varchar(255) DEFAULT NULL,
  `rapptime` varchar(255) DEFAULT NULL,
  `rappdate` date DEFAULT NULL,
  `rappnewtime` varchar(255) DEFAULT NULL,
  `rappnewdate` date DEFAULT NULL,
  `rappreason` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`rappid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- No data for table `rappointment`

-- Table structure for table `reports`
DROP TABLE IF EXISTS `reports`;
CREATE TABLE `reports` (
  `repid` int NOT NULL,
  `reppatient` varchar(255) DEFAULT NULL,
  `repdate` date DEFAULT NULL,
  `repprescription` varchar(255) DEFAULT NULL,
  `repcleaning` int DEFAULT NULL,
  `repextraction` int DEFAULT NULL,
  `reprootcanal` int DEFAULT NULL,
  `repbraces` int DEFAULT NULL,
  `repdentures` int DEFAULT NULL,
  `repdentist` varchar(255) DEFAULT NULL,
  `repothers` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`repid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- No data for table `reports`

-- Table structure for table `teeth`
DROP TABLE IF EXISTS `teeth`;
CREATE TABLE `teeth` (
  `tID` int NOT NULL,
  `tpatname` varchar(255) DEFAULT NULL,
  `l1` varchar(255) DEFAULT NULL,
  `l2` varchar(255) DEFAULT NULL,
  `l3` varchar(255) DEFAULT NULL,
  `l4` varchar(255) DEFAULT NULL,
  `l5` varchar(255) DEFAULT NULL,
  `l6` varchar(255) DEFAULT NULL,
  `l7` varchar(255) DEFAULT NULL,
  `l8` varchar(255) DEFAULT NULL,
  `l9` varchar(255) DEFAULT NULL,
  `l10` varchar(255) DEFAULT NULL,
  `l11` varchar(255) DEFAULT NULL,
  `l12` varchar(255) DEFAULT NULL,
  `l13` varchar(255) DEFAULT NULL,
  `l14` varchar(255) DEFAULT NULL,
  `l15` varchar(255) DEFAULT NULL,
  `l16` varchar(255) DEFAULT NULL,
  `l17` varchar(255) DEFAULT NULL,
  `l18` varchar(255) DEFAULT NULL,
  `l19` varchar(255) DEFAULT NULL,
  `l20` varchar(255) DEFAULT NULL,
  `l21` varchar(255) DEFAULT NULL,
  `l22` varchar(255) DEFAULT NULL,
  `l23` varchar(255) DEFAULT NULL,
  `l24` varchar(255) DEFAULT NULL,
  `l25` varchar(255) DEFAULT NULL,
  `l26` varchar(255) DEFAULT NULL,
  `l27` varchar(255) DEFAULT NULL,
  `l28` varchar(255) DEFAULT NULL,
  `l29` varchar(255) DEFAULT NULL,
  `l30` varchar(255) DEFAULT NULL,
  `l31` varchar(255) DEFAULT NULL,
  `l32` varchar(255) DEFAULT NULL,
  `is_deleted` tinyint DEFAULT '0',
  PRIMARY KEY (`tID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Dumping data for table `teeth` (3 rows)
INSERT INTO `teeth` (`tID`, `tpatname`, `l1`, `l2`, `l3`, `l4`, `l5`, `l6`, `l7`, `l8`, `l9`, `l10`, `l11`, `l12`, `l13`, `l14`, `l15`, `l16`, `l17`, `l18`, `l19`, `l20`, `l21`, `l22`, `l23`, `l24`, `l25`, `l26`, `l27`, `l28`, `l29`, `l30`, `l31`, `l32`, `is_deleted`) VALUES
(1, 'HEYY', 'extracted', 'root-canal', 'caries', 'crown', 'implant', 'healthy', 'filled', 'root-canal', 'crown', 'filled', 'caries', 'healthy', 'crown', 'crown', 'implant', 'crown', 'crown', 'caries', 'filled', 'extracted', 'filled', 'extracted', 'crown', 'filled', 'caries', 'crown', 'root-canal', 'extracted', 'filled', 'crown', 'crown', 'extracted', 0),
(2, 'loe', 'filled', 'root-canal', 'root-canal', 'caries', 'implant', 'caries', 'crown', 'root-canal', 'crown', 'filled', 'healthy', 'healthy', 'extracted', 'root-canal', 'crown', 'healthy', 'root-canal', 'extracted', 'filled', 'healthy', 'extracted', 'crown', 'healthy', 'healthy', 'root-canal', 'filled', 'crown', 'crown', 'filled', 'filled', 'filled', 'root-canal', 0),
(3, 'TEST', 'healthy', 'caries', 'filled', 'healthy', 'crown', 'implant', 'crown', 'healthy', 'filled', 'healthy', 'root-canal', 'crown', 'healthy', 'caries', 'healthy', 'healthy', 'extracted', 'healthy', 'root-canal', 'healthy', 'healthy', 'crown', 'healthy', 'crown', 'healthy', 'filled', 'caries', 'extracted', 'crown', 'healthy', 'implant', 'healthy', 0);

-- Table structure for table `user_logs`
DROP TABLE IF EXISTS `user_logs`;
CREATE TABLE `user_logs` (
  `log_id` int NOT NULL AUTO_INCREMENT,
  `user_id` int DEFAULT NULL,
  `action` varchar(255) DEFAULT NULL,
  `timestamp` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `details` text,
  PRIMARY KEY (`log_id`)
) ENGINE=InnoDB AUTO_INCREMENT=262 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Dumping data for table `user_logs` (261 rows)
INSERT INTO `user_logs` (`log_id`, `user_id`, `action`, `timestamp`, `details`) VALUES
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
(21, 1, 'Update Tooth Condition', '2025-07-01 03:27:37', 'Updated tooth #4 condition to "crown" for patient HEYY'),
(22, 1, 'Update Tooth Condition', '2025-07-01 03:27:38', 'Updated tooth #8 condition to "root-canal" for patient HEYY'),
(23, 1, 'Update Tooth Condition', '2025-07-01 03:27:39', 'Updated tooth #27 condition to "root-canal" for patient HEYY'),
(24, 1, 'Update Tooth Condition', '2025-07-01 03:27:40', 'Updated tooth #26 condition to "crown" for patient HEYY'),
(25, 1, 'Update Tooth Condition', '2025-07-01 03:27:42', 'Updated tooth #30 condition to "crown" for patient HEYY'),
(26, 1, 'Update Tooth Condition', '2025-07-01 03:27:43', 'Updated tooth #25 condition to "caries" for patient HEYY'),
(27, 1, 'Update Tooth Condition', '2025-07-01 03:27:44', 'Updated tooth #1 condition to "extracted" for patient HEYY'),
(28, 1, 'Update Tooth Condition', '2025-07-01 03:27:45', 'Updated tooth #5 condition to "implant" for patient HEYY'),
(29, 1, 'Update Tooth Condition', '2025-07-01 03:27:46', 'Updated tooth #17 condition to "crown" for patient HEYY'),
(30, 1, 'Update Tooth Condition', '2025-07-01 03:27:49', 'Updated tooth #28 condition to "extracted" for patient HEYY'),
(31, 1, 'Update Tooth Condition', '2025-07-01 03:27:50', 'Updated tooth #32 condition to "extracted" for patient HEYY'),
(32, 1, 'Update Tooth Condition', '2025-07-01 03:27:51', 'Updated tooth #31 condition to "crown" for patient HEYY'),
(33, 1, 'Update Tooth Condition', '2025-07-01 03:27:53', 'Updated tooth #29 condition to "filled" for patient HEYY'),
(34, 1, 'Update Tooth Condition', '2025-07-01 03:27:54', 'Updated tooth #9 condition to "crown" for patient HEYY'),
(35, 1, 'Update Tooth Condition', '2025-07-01 03:27:55', 'Updated tooth #13 condition to "crown" for patient HEYY'),
(36, 1, 'Update Tooth Condition', '2025-07-01 03:27:56', 'Updated tooth #21 condition to "filled" for patient HEYY'),
(37, 1, 'Update Tooth Condition', '2025-07-01 03:27:57', 'Updated tooth #18 condition to "caries" for patient HEYY'),
(38, 1, 'Update Tooth Condition', '2025-07-01 03:27:58', 'Updated tooth #22 condition to "extracted" for patient HEYY'),
(39, 1, 'Update Tooth Condition', '2025-07-01 03:27:59', 'Updated tooth #14 condition to "crown" for patient HEYY'),
(40, 1, 'Update Tooth Condition', '2025-07-01 03:28:00', 'Updated tooth #10 condition to "filled" for patient HEYY'),
(41, 1, 'Update Tooth Condition', '2025-07-01 03:28:01', 'Updated tooth #11 condition to "caries" for patient HEYY'),
(42, 1, 'Update Tooth Condition', '2025-07-01 03:28:02', 'Updated tooth #15 condition to "implant" for patient HEYY'),
(43, 1, 'Update Tooth Condition', '2025-07-01 03:28:03', 'Updated tooth #19 condition to "healthy" for patient HEYY'),
(44, 1, 'Update Tooth Condition', '2025-07-01 03:28:04', 'Updated tooth #23 condition to "crown" for patient HEYY'),
(45, 1, 'Update Tooth Condition', '2025-07-01 03:28:05', 'Updated tooth #19 condition to "filled" for patient HEYY'),
(46, 1, 'Update Tooth Condition', '2025-07-01 03:28:06', 'Updated tooth #16 condition to "crown" for patient HEYY'),
(47, 1, 'Update Tooth Condition', '2025-07-01 03:28:07', 'Updated tooth #12 condition to "healthy" for patient HEYY'),
(48, 1, 'Update Tooth Condition', '2025-07-01 03:28:08', 'Updated tooth #20 condition to "extracted" for patient HEYY'),
(49, 1, 'Update Tooth Condition', '2025-07-01 03:28:09', 'Updated tooth #24 condition to "filled" for patient HEYY'),
(50, 1, 'Update Dental Chart', '2025-07-01 03:28:39', 'Updated dental chart for patient HEYY'),
(51, 1, 'Print Dental Chart', '2025-07-01 03:28:41', 'Printed dental chart for HEYY (ID: PAT-001)'),
(52, 1, 'Logout', '2025-07-01 03:39:49', 'User loe logged out'),
(53, 1, 'Password Reset Verification', '2025-07-01 03:40:01', 'Identity verified for password reset: loe (loe)'),
(54, 1, 'Password Reset Completed', '2025-07-01 03:40:22', 'Password successfully reset for: loe (loe)'),
(55, 1, 'Login', '2025-07-01 03:40:29', 'User loe logged in successfully'),
(56, 0, 'Failed Login', '2025-07-01 04:10:18', 'Failed login attempt for username: loe (Attempt 1/3)'),
(57, 0, 'Failed Login', '2025-07-01 04:10:21', 'Failed login attempt for username: loe (Attempt 2/3)'),
(58, 0, 'Failed Login', '2025-07-01 04:10:22', 'Failed login attempt for username: loe (Attempt 3/3)'),
(59, 1, 'Password Reset Verification', '2025-07-01 04:10:36', 'Identity verified for password reset: loe (loe)'),
(60, 1, 'Password Reset Completed', '2025-07-01 04:10:48', 'Password successfully reset for: loe (loe)'),
(61, 1, 'Login', '2025-07-01 04:10:55', 'User loe logged in successfully'),
(62, 1, 'Logout', '2025-07-01 04:11:27', 'User loe logged out'),
(63, 1, 'Login', '2025-07-01 04:11:30', 'User loe logged in successfully'),
(64, 1, 'Logout', '2025-07-01 04:11:42', 'User loe logged out'),
(65, 0, 'Login', '2025-07-01 04:11:45', 'Hardcoded admin logged in successfully'),
(66, 0, 'Create Inventory', '2025-07-01 04:12:03', 'Added new inventory item: drug (Quantity: 11)'),
(67, 0, 'Print Inventory Report', '2025-07-01 04:12:07', 'Generated inventory report: 1 items (Filter: All Items)'),
(68, 0, 'Create Inventory', '2025-07-01 04:12:22', 'Added new inventory item: drug (Quantity: 23)'),
(69, 0, 'Update Inventory', '2025-07-01 04:13:40', 'Updated inventory item: drug -> drug (Quantity: 11 -> 11)'),
(70, 1, 'Login', '2025-07-01 04:15:27', 'User loe logged in successfully'),
(71, 1, 'Update Inventory', '2025-07-01 04:15:36', 'Updated inventory item: drug -> drug (Quantity: 11 -> 12)'),
(72, 1, 'Update Inventory', '2025-07-01 04:15:47', 'Updated inventory item: drug -> drug (Quantity: 12 -> 12)'),
(73, 1, 'Delete Inventory', '2025-07-01 04:16:10', 'Deleted inventory item: drug (Quantity: 23)'),
(74, 0, 'Login', '2025-07-01 08:17:15', 'Hardcoded admin logged in successfully'),
(75, 0, 'Login', '2025-07-01 11:01:14', 'Hardcoded admin logged in successfully'),
(76, 0, 'Create Inventory', '2025-07-01 11:01:30', 'Added new inventory item: dasd (Quantity: 22)'),
(77, 0, 'Delete Inventory', '2025-07-01 11:01:32', 'Deleted inventory item: dasd (Quantity: 22)'),
(78, 0, 'Delete Inventory', '2025-07-01 11:01:36', 'Deleted inventory item: drug (Quantity: 12)'),
(79, 0, 'Create Inventory', '2025-07-01 11:01:43', 'Added new inventory item: dsad (Quantity: 123)'),
(80, 0, 'Update Inventory', '2025-07-01 11:01:49', 'Updated inventory item: dsad -> dsad (Quantity: 123 -> 22)'),
(81, 0, 'Update Inventory', '2025-07-01 11:01:52', 'Updated inventory item: dsad -> dsad (Quantity: 22 -> 22)'),
(82, 0, 'Login', '2025-07-01 12:41:18', 'Hardcoded admin logged in successfully'),
(83, 0, 'Print Inventory Report', '2025-07-01 12:41:26', 'Generated inventory report: 1 items (Status: All Items (Active & Inactive))'),
(84, 0, 'Print Inventory Report', '2025-07-01 12:41:42', 'Generated inventory report: 1 items (Status: Active Items Only)'),
(85, 0, 'Deactivate Inventory', '2025-07-01 12:42:26', 'Deactivated inventory item: dsad (Quantity: 22)'),
(86, 0, 'Reactivate Inventory', '2025-07-01 12:42:31', 'Reactivated inventory item: dsad (Quantity: 22)'),
(87, 0, 'Login', '2025-07-02 03:59:42', 'Hardcoded admin logged in successfully'),
(88, 0, 'Print Inventory Report', '2025-07-02 03:59:48', 'Generated inventory report: 0 items (Status: Active Items Only, Category: Medicines Only)'),
(89, 0, 'Create Appointment', '2025-07-02 04:00:42', 'Created appointment for HEYY on 2025-07-02 at 07:00'),
(90, 0, 'Login', '2025-07-02 04:01:32', 'Hardcoded admin logged in successfully'),
(91, 0, 'Failed Login', '2025-07-02 04:11:56', 'Failed login attempt for username: login (Attempt 1/3)'),
(92, 0, 'Login', '2025-07-02 04:12:00', 'Hardcoded admin logged in successfully'),
(93, 0, 'Login', '2025-07-02 04:12:34', 'Hardcoded admin logged in successfully'),
(94, 0, 'Login', '2025-07-02 04:15:13', 'Hardcoded admin logged in successfully'),
(95, 0, 'Update Patient', '2025-07-02 04:34:43', 'Updated patient: HEYY -> HEYY (ID: PAT-001)'),
(96, 0, 'Complete Appointment', '2025-07-02 04:35:09', 'Marked appointment as completed for HEYY on 2025-07-02 at 07:00'),
(97, 0, 'Complete Appointment', '2025-07-02 04:35:19', 'Marked appointment as completed for HEYY on 2025-07-02 at 07:00'),
(98, 0, 'Create Appointment', '2025-07-02 04:35:41', 'Created appointment for HEYY on 2025-07-02 at 01:00'),
(99, 0, 'Complete Appointment', '2025-07-02 04:35:45', 'Marked appointment as completed for HEYY on 2025-07-02 at 01:00'),
(100, 0, 'Complete Appointment', '2025-07-02 04:36:39', 'Marked appointment as completed for HEYY on 2025-07-02 at 07:00');

INSERT INTO `user_logs` (`log_id`, `user_id`, `action`, `timestamp`, `details`) VALUES
(101, 0, 'Cancel Appointment', '2025-07-02 04:36:41', 'Cancelled appointment for HEYY on 2025-07-02 at 07:00'),
(102, 0, 'Print Patients Report', '2025-07-02 04:38:38', 'Generated patients report: 1 patients (Status: Active Patients Only)'),
(103, 0, 'Create Patient', '2025-07-02 04:38:52', 'Created new patient: loe (ID: PAT-002)'),
(104, 0, 'Create Dental Chart', '2025-07-02 04:39:00', 'Created dental chart for loe (ID: PAT-002)'),
(105, 0, 'Update Dental Chart', '2025-07-02 04:39:04', 'Updated dental chart for patient loe'),
(106, 0, 'Login', '2025-07-02 04:50:28', 'Hardcoded admin logged in successfully'),
(107, 0, 'Update Dental Chart', '2025-07-02 04:50:46', 'Updated complete dental chart for patient HEYY'),
(108, 0, 'Update Dental Chart', '2025-07-02 04:50:47', 'Updated complete dental chart for patient HEYY'),
(109, 0, 'Update Dental Chart', '2025-07-02 04:50:48', 'Updated complete dental chart for patient HEYY'),
(110, 0, 'Update Dental Chart', '2025-07-02 04:50:48', 'Updated complete dental chart for patient HEYY'),
(111, 0, 'Update Dental Chart', '2025-07-02 04:50:48', 'Updated complete dental chart for patient HEYY'),
(112, 0, 'Update Dental Chart', '2025-07-02 04:50:49', 'Updated complete dental chart for patient HEYY'),
(113, 0, 'Update Dental Chart', '2025-07-02 04:50:49', 'Updated complete dental chart for patient HEYY'),
(114, 0, 'Update Dental Chart', '2025-07-02 04:50:52', 'Updated complete dental chart for patient HEYY'),
(115, 0, 'Update Dental Chart', '2025-07-02 04:50:55', 'Updated complete dental chart for patient HEYY'),
(116, 0, 'Update Tooth Condition', '2025-07-02 04:51:26', 'Updated tooth #2 condition to "root-canal" for patient loe'),
(117, 0, 'Update Dental Chart', '2025-07-02 04:51:27', 'Updated complete dental chart for patient loe'),
(118, 0, 'Update Tooth Condition', '2025-07-02 04:51:31', 'Updated tooth #3 condition to "root-canal" for patient loe'),
(119, 0, 'Update Tooth Condition', '2025-07-02 04:51:32', 'Updated tooth #7 condition to "crown" for patient loe'),
(120, 0, 'Update Tooth Condition', '2025-07-02 04:51:33', 'Updated tooth #4 condition to "caries" for patient loe'),
(121, 0, 'Update Tooth Condition', '2025-07-02 04:51:34', 'Updated tooth #8 condition to "root-canal" for patient loe'),
(122, 0, 'Update Tooth Condition', '2025-07-02 04:51:35', 'Updated tooth #26 condition to "filled" for patient loe'),
(123, 0, 'Update Tooth Condition', '2025-07-02 04:51:37', 'Updated tooth #29 condition to "filled" for patient loe'),
(124, 0, 'Update Tooth Condition', '2025-07-02 04:51:38', 'Updated tooth #1 condition to "filled" for patient loe'),
(125, 0, 'Update Tooth Condition', '2025-07-02 04:51:39', 'Updated tooth #6 condition to "caries" for patient loe'),
(126, 0, 'Update Tooth Condition', '2025-07-02 04:51:40', 'Updated tooth #5 condition to "implant" for patient loe'),
(127, 0, 'Update Tooth Condition', '2025-07-02 04:51:41', 'Updated tooth #27 condition to "crown" for patient loe'),
(128, 0, 'Update Tooth Condition', '2025-07-02 04:51:42', 'Updated tooth #30 condition to "filled" for patient loe'),
(129, 0, 'Update Tooth Condition', '2025-07-02 04:51:44', 'Updated tooth #25 condition to "root-canal" for patient loe'),
(130, 0, 'Update Tooth Condition', '2025-07-02 04:51:45', 'Updated tooth #31 condition to "filled" for patient loe'),
(131, 0, 'Update Tooth Condition', '2025-07-02 04:51:46', 'Updated tooth #28 condition to "crown" for patient loe'),
(132, 0, 'Update Tooth Condition', '2025-07-02 04:51:47', 'Updated tooth #32 condition to "root-canal" for patient loe'),
(133, 0, 'Update Tooth Condition', '2025-07-02 04:51:48', 'Updated tooth #13 condition to "extracted" for patient loe'),
(134, 0, 'Update Tooth Condition', '2025-07-02 04:51:48', 'Updated tooth #9 condition to "crown" for patient loe'),
(135, 0, 'Update Tooth Condition', '2025-07-02 04:51:49', 'Updated tooth #17 condition to "root-canal" for patient loe'),
(136, 0, 'Update Tooth Condition', '2025-07-02 04:51:50', 'Updated tooth #21 condition to "extracted" for patient loe'),
(137, 0, 'Update Tooth Condition', '2025-07-02 04:51:51', 'Updated tooth #10 condition to "filled" for patient loe'),
(138, 0, 'Update Tooth Condition', '2025-07-02 04:51:52', 'Updated tooth #18 condition to "extracted" for patient loe'),
(139, 0, 'Update Tooth Condition', '2025-07-02 04:52:02', 'Updated tooth #14 condition to "root-canal" for patient loe'),
(140, 0, 'Update Tooth Condition', '2025-07-02 04:52:04', 'Updated tooth #22 condition to "crown" for patient loe'),
(141, 0, 'Update Tooth Condition', '2025-07-02 04:52:05', 'Updated tooth #15 condition to "crown" for patient loe'),
(142, 0, 'Update Tooth Condition', '2025-07-02 04:52:06', 'Updated tooth #19 condition to "filled" for patient loe'),
(143, 0, 'Update Tooth Condition', '2025-07-02 04:52:07', 'Updated tooth #23 condition to "healthy" for patient loe'),
(144, 0, 'Update Tooth Condition', '2025-07-02 04:52:09', 'Updated tooth #20 condition to "healthy" for patient loe'),
(145, 0, 'Update Tooth Condition', '2025-07-02 04:52:10', 'Updated tooth #12 condition to "healthy" for patient loe'),
(146, 0, 'Update Dental Chart', '2025-07-02 04:52:12', 'Updated complete dental chart for patient loe'),
(147, 0, 'Login', '2025-07-02 08:48:24', 'Hardcoded admin logged in successfully'),
(148, 0, 'Logout', '2025-07-02 08:50:34', 'Hardcoded admin logged out'),
(149, 0, 'Failed Login', '2025-07-02 08:50:36', 'Failed login attempt for username: loe (Attempt 1/3)'),
(150, 0, 'Failed Login', '2025-07-02 08:50:38', 'Failed login attempt for username: loe (Attempt 2/3)'),
(151, 0, 'Login', '2025-07-02 08:50:42', 'Hardcoded admin logged in successfully'),
(152, 0, 'Update Staff', '2025-07-02 08:50:47', 'Updated staff member: loe -> loe (loe)'),
(153, 0, 'Logout', '2025-07-02 08:50:49', 'Hardcoded admin logged out'),
(154, 1, 'Login', '2025-07-02 08:50:50', 'User loe logged in successfully'),
(155, 0, 'Login', '2025-07-02 08:57:40', 'Hardcoded admin logged in successfully'),
(156, 0, 'View About Page', '2025-07-02 08:57:41', 'User System Administrator viewed system about page'),
(157, 0, 'View About Page', '2025-07-02 08:58:08', 'User System Administrator viewed system about page'),
(158, 0, 'View About Page', '2025-07-02 08:58:15', 'User System Administrator viewed system about page'),
(159, 0, 'View About Page', '2025-07-02 08:59:12', 'User System Administrator viewed system about page'),
(160, 0, 'Login', '2025-07-02 09:02:51', 'Hardcoded admin logged in successfully'),
(161, 0, 'View About Page', '2025-07-02 09:02:54', 'User System Administrator viewed system about page'),
(162, 0, 'View About Page', '2025-07-02 09:03:15', 'User System Administrator viewed system about page'),
(163, 0, 'Logout', '2025-07-02 09:03:16', 'Hardcoded admin logged out'),
(164, 0, 'Login', '2025-07-02 09:05:46', 'Hardcoded admin logged in successfully'),
(165, 0, 'Print Dental Chart', '2025-07-02 09:09:22', 'Printed dental chart for HEYY (ID: PAT-001)'),
(166, 0, 'Export Logs', '2025-07-02 09:09:31', 'User exported 165 log entries'),
(167, 2, 'User Registration', '2025-07-02 09:25:44', 'New user registered: 123 (123)'),
(168, 2, 'Login', '2025-07-02 09:26:05', 'User 123 logged in successfully'),
(169, 2, 'Logout', '2025-07-02 09:26:07', 'User 123 logged out'),
(170, 0, 'Login', '2025-07-02 09:31:52', 'Hardcoded admin logged in successfully'),
(171, 0, 'Login', '2025-07-03 05:20:37', 'Hardcoded admin logged in successfully'),
(172, 0, 'View About Page', '2025-07-03 05:20:41', 'User System Administrator viewed system about page'),
(173, 0, 'Login', '2025-07-03 05:31:37', 'Hardcoded admin logged in successfully'),
(174, 0, 'Deactivate Patient', '2025-07-03 05:31:42', 'Deactivated patient: HEYY (ID: PAT-001)'),
(175, 0, 'Reactivate Patient', '2025-07-03 05:31:51', 'Reactivated patient: HEYY (ID: PAT-001)'),
(176, 0, 'Update Dental Chart', '2025-07-03 05:31:58', 'Updated complete dental chart for patient HEYY'),
(177, 0, 'Update Dental Chart', '2025-07-03 05:31:59', 'Updated complete dental chart for patient HEYY'),
(178, 0, 'Reactivate Appointment', '2025-07-03 05:32:28', 'Reactivated appointment for HEYY on 2025-07-02 at 07:00'),
(179, 0, 'Complete Appointment', '2025-07-03 05:32:31', 'Marked appointment as completed for HEYY on 2025-07-02 at 07:00'),
(180, 0, 'Login', '2025-07-03 05:40:00', 'Hardcoded admin logged in successfully'),
(181, 0, 'Print Staff Report', '2025-07-03 05:40:33', 'Generated staff report: 2 staff members (Status: Active Staff Only)'),
(182, 0, 'Login', '2025-07-03 05:41:46', 'Hardcoded admin logged in successfully'),
(183, 0, 'Update Patient', '2025-07-03 05:41:53', 'Updated patient: HEYY -> HEYY (ID: PAT-001)'),
(184, 0, 'Login', '2025-07-03 05:51:17', 'Hardcoded admin logged in successfully'),
(185, 0, 'Create Appointment', '2025-07-03 05:52:43', 'Created appointment for loe on 2025-07-24 at 06:00'),
(186, 0, 'Create Appointment', '2025-07-03 05:53:01', 'Created appointment for loe on 2025-07-03 at 20:00'),
(187, 0, 'View About Page', '2025-07-03 05:53:35', 'User System Administrator viewed system about page'),
(188, 0, 'View About Page', '2025-07-03 05:53:37', 'User System Administrator viewed system about page'),
(189, 0, 'Login', '2025-07-03 06:12:33', 'Hardcoded admin logged in successfully'),
(190, 0, 'Login', '2025-07-03 09:40:50', 'Hardcoded admin logged in successfully'),
(191, 0, 'Create Patient', '2025-07-03 09:48:32', 'Created new patient: TEST (ID: PAT-003)'),
(192, 0, 'Create Dental Chart', '2025-07-03 09:50:55', 'Created dental chart for TEST (ID: PAT-003)'),
(193, 0, 'Update Tooth Condition', '2025-07-03 09:51:40', 'Updated tooth #3 condition to "filled" for patient TEST'),
(194, 0, 'Update Tooth Condition', '2025-07-03 09:51:41', 'Updated tooth #7 condition to "crown" for patient TEST'),
(195, 0, 'Update Tooth Condition', '2025-07-03 09:51:42', 'Updated tooth #2 condition to "caries" for patient TEST'),
(196, 0, 'Update Tooth Condition', '2025-07-03 09:51:43', 'Updated tooth #5 condition to "crown" for patient TEST'),
(197, 0, 'Update Tooth Condition', '2025-07-03 09:51:44', 'Updated tooth #6 condition to "implant" for patient TEST'),
(198, 0, 'Update Tooth Condition', '2025-07-03 09:51:44', 'Updated tooth #26 condition to "filled" for patient TEST'),
(199, 0, 'Update Tooth Condition', '2025-07-03 09:51:46', 'Updated tooth #29 condition to "crown" for patient TEST'),
(200, 0, 'Update Tooth Condition', '2025-07-03 09:51:47', 'Updated tooth #28 condition to "extracted" for patient TEST');

INSERT INTO `user_logs` (`log_id`, `user_id`, `action`, `timestamp`, `details`) VALUES
(201, 0, 'Update Tooth Condition', '2025-07-03 09:51:48', 'Updated tooth #27 condition to "caries" for patient TEST'),
(202, 0, 'Update Tooth Condition', '2025-07-03 09:51:49', 'Updated tooth #31 condition to "implant" for patient TEST'),
(203, 0, 'Update Tooth Condition', '2025-07-03 09:51:50', 'Updated tooth #17 condition to "extracted" for patient TEST'),
(204, 0, 'Update Tooth Condition', '2025-07-03 09:51:51', 'Updated tooth #9 condition to "filled" for patient TEST'),
(205, 0, 'Update Tooth Condition', '2025-07-03 09:51:52', 'Updated tooth #14 condition to "caries" for patient TEST'),
(206, 0, 'Update Tooth Condition', '2025-07-03 09:51:53', 'Updated tooth #11 condition to "root-canal" for patient TEST'),
(207, 0, 'Update Tooth Condition', '2025-07-03 09:51:54', 'Updated tooth #19 condition to "root-canal" for patient TEST'),
(208, 0, 'Update Tooth Condition', '2025-07-03 09:51:56', 'Updated tooth #18 condition to "healthy" for patient TEST'),
(209, 0, 'Update Tooth Condition', '2025-07-03 09:51:57', 'Updated tooth #22 condition to "crown" for patient TEST'),
(210, 0, 'Update Tooth Condition', '2025-07-03 09:51:58', 'Updated tooth #24 condition to "crown" for patient TEST'),
(211, 0, 'Update Tooth Condition', '2025-07-03 09:51:59', 'Updated tooth #12 condition to "crown" for patient TEST'),
(212, 0, 'Print Staff Report', '2025-07-03 10:10:10', 'Generated staff report: 2 staff members (Status: Active Staff Only)'),
(213, 0, 'Print Staff Report', '2025-07-03 10:10:41', 'Generated staff report: 2 staff members (Status: Active Staff Only)'),
(214, 0, 'Logout', '2025-07-03 10:11:42', 'Hardcoded admin logged out'),
(215, 0, 'Failed Login', '2025-07-03 10:15:53', 'Failed login attempt for username: admin (Attempt 1/3)'),
(216, 0, 'Failed Login', '2025-07-03 10:15:55', 'Failed login attempt for username: admin (Attempt 2/3)'),
(217, 0, 'Failed Login', '2025-07-03 10:15:56', 'Failed login attempt for username: admin (Attempt 3/3)'),
(218, 1, 'Password Reset Verification', '2025-07-03 10:18:57', 'Identity verified for password reset: loe (loe)'),
(219, 1, 'Password Reset Completed', '2025-07-03 10:19:06', 'Password successfully reset for: loe (loe)'),
(220, 0, 'Login', '2025-07-03 10:19:10', 'Hardcoded admin logged in successfully'),
(221, 0, 'Logout', '2025-07-03 10:19:13', 'Hardcoded admin logged out'),
(222, 0, 'Login', '2025-07-03 10:37:49', 'Hardcoded admin logged in successfully'),
(223, 0, 'Logout', '2025-07-03 10:38:18', 'Hardcoded admin logged out'),
(224, 1, 'Password Reset Verification', '2025-07-03 10:38:25', 'Identity verified for password reset: loe (loe)'),
(225, 1, 'Password Reset Completed', '2025-07-03 10:38:31', 'Password successfully reset for: loe (loe)'),
(226, 1, 'Password Reset Verification', '2025-07-03 10:39:56', 'Identity verified for password reset: loe (loe)'),
(227, 0, 'Login', '2025-07-03 10:42:05', 'Hardcoded admin logged in successfully'),
(228, 0, 'Database Restore', '2025-07-03 02:45:01', 'Restored database from backup: backup_20250703104256.sql'),
(229, 0, 'Failed Login', '2025-07-03 03:10:55', 'Failed login attempt for username: admin (Attempt 1/3)'),
(230, 0, 'Login', '2025-07-03 03:11:00', 'Hardcoded admin logged in successfully'),
(231, 0, 'View About Page', '2025-07-03 03:11:03', 'User System Administrator viewed system about page'),
(232, 0, 'Login', '2025-07-03 03:17:05', 'Hardcoded admin logged in successfully'),
(233, 0, 'View FAQ Page', '2025-07-03 03:17:06', 'User accessed FAQ and support page'),
(234, 0, 'Login', '2025-07-03 03:17:25', 'Hardcoded admin logged in successfully'),
(235, 0, 'View FAQ Page', '2025-07-03 03:17:29', 'User accessed FAQ and support page'),
(236, 0, 'Login', '2025-07-03 03:21:31', 'Hardcoded admin logged in successfully'),
(237, 0, 'View FAQ Page', '2025-07-03 03:21:32', 'User accessed FAQ and support page'),
(238, 0, 'Download User Manual', '2025-07-03 03:21:35', 'User downloaded the user manual PDF from: templates\\User Manual.pdf'),
(239, 0, 'Download User Manual', '2025-07-03 03:21:44', 'User downloaded the user manual PDF from: templates\\User Manual.pdf'),
(240, 0, 'Login', '2025-07-06 00:01:14', 'Hardcoded admin logged in successfully'),
(241, 0, 'View FAQ Page', '2025-07-06 00:27:01', 'User accessed FAQ and support page'),
(242, 0, 'View About Page', '2025-07-06 00:27:04', 'User System Administrator viewed system about page'),
(243, 0, 'View FAQ Page', '2025-07-06 00:27:06', 'User accessed FAQ and support page'),
(244, 0, 'View FAQ Page', '2025-07-06 00:27:53', 'User accessed FAQ and support page'),
(245, 0, 'View About Page', '2025-07-06 00:27:53', 'User System Administrator viewed system about page'),
(246, 0, 'View FAQ Page', '2025-07-06 00:27:55', 'User accessed FAQ and support page'),
(247, 0, 'Print Appointments Report', '2025-07-06 00:28:12', 'Generated appointments report: 0 appointments (Status: All Appointments, Date: July 06, 2025)'),
(248, 0, 'Login', '2025-07-06 00:37:10', 'Hardcoded admin logged in successfully'),
(249, 0, 'View FAQ Page', '2025-07-06 00:37:16', 'User accessed FAQ and support page'),
(250, 0, 'View About Page', '2025-07-06 00:37:17', 'User System Administrator viewed system about page'),
(251, 0, 'View About Page', '2025-07-06 00:37:20', 'User System Administrator viewed system about page'),
(252, 0, 'View FAQ Page', '2025-07-06 00:41:36', 'User accessed FAQ and support page'),
(253, 0, 'View FAQ Page', '2025-07-06 00:41:40', 'User accessed FAQ and support page'),
(254, 0, 'Login', '2025-07-06 00:44:14', 'Hardcoded admin logged in successfully'),
(255, 0, 'Print Patients Report', '2025-07-06 00:44:18', 'Generated patients report: 3 patients (Status: Active Patients Only)'),
(256, 0, 'Login', '2025-07-06 00:47:33', 'Hardcoded admin logged in successfully'),
(257, 0, 'View FAQ Page', '2025-07-06 00:47:52', 'User accessed FAQ and support page'),
(258, 0, 'View About Page', '2025-07-06 00:47:52', 'User System Administrator viewed system about page'),
(259, 0, 'View FAQ Page', '2025-07-06 00:47:54', 'User accessed FAQ and support page'),
(260, 0, 'View FAQ Page', '2025-07-06 00:49:01', 'User accessed FAQ and support page'),
(261, 0, 'View About Page', '2025-07-06 00:49:02', 'User System Administrator viewed system about page');

-- Table structure for table `users`
DROP TABLE IF EXISTS `users`;
CREATE TABLE `users` (
  `usersid` int NOT NULL AUTO_INCREMENT,
  `usersusername` varchar(255) NOT NULL,
  `userspassword` varchar(255) NOT NULL,
  `usersrealname` varchar(255) DEFAULT NULL,
  `usersemail` varchar(255) DEFAULT NULL,
  `usershomeaddress` varchar(255) DEFAULT NULL,
  `userscityzipcode` varchar(255) DEFAULT NULL,
  `userscontact` varchar(255) DEFAULT NULL,
  `usersreligion` varchar(255) DEFAULT NULL,
  `usersdob` date DEFAULT NULL,
  `usersgender` varchar(255) DEFAULT NULL,
  `usersage` int DEFAULT NULL,
  `usersoccupation` varchar(255) DEFAULT NULL,
  `usersaccess` varchar(255) DEFAULT NULL,
  `key` blob,
  `is_deleted` tinyint(1) NOT NULL DEFAULT '0',
  PRIMARY KEY (`usersid`),
  UNIQUE KEY `usersusername` (`usersusername`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Dumping data for table `users` (2 rows)
INSERT INTO `users` (`usersid`, `usersusername`, `userspassword`, `usersrealname`, `usersemail`, `usershomeaddress`, `userscityzipcode`, `userscontact`, `usersreligion`, `usersdob`, `usersgender`, `usersage`, `usersoccupation`, `usersaccess`, `key`, `is_deleted`) VALUES
(1, 'loe', '6c241236470212d37f015d5e4003ca0536d4f2b531361f440283c1e3aebeac5b', 'loe', 'loe@yahoo.com', 'Marikina', '1802', '09166532911', 'RC', '2001-11-06 00:00:00', 'Male', 23, 'Arsonist', 'user', NULL, 0),
(2, '123', 'a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3', '123', '123@yahoo.com', '#20 SAMPAGUITA, INDUSTRIAL VALLEY COMPLEX, MARIKINA CITY', '1802', '13123123123', 'RC', '2001-11-06 00:00:00', 'Male', 23, 'Arsonist', 'user', NULL, 0);

COMMIT;
SET FOREIGN_KEY_CHECKS=1;
SET SQL_MODE = '';
SET AUTOCOMMIT = 1;
-- Backup completed on 2025-07-06 08:49:05
