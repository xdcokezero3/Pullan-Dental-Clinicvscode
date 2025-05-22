-- Database Backup for: pullandentalclinic
-- Generated on: 2025-05-22 12:10:11
-- By: Pullan Dental Clinic Management System

SET FOREIGN_KEY_CHECKS=0;

DROP DATABASE IF EXISTS `pullandentalclinic`;
CREATE DATABASE `pullandentalclinic` CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
USE `pullandentalclinic`;

DROP TABLE IF EXISTS `appointment`;
CREATE TABLE `appointment` (
  `appid` int NOT NULL AUTO_INCREMENT,
  `apppatient` varchar(255) DEFAULT NULL,
  `apptime` varchar(255) DEFAULT NULL,
  `appdate` date DEFAULT NULL,
  PRIMARY KEY (`appid`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

INSERT INTO `appointment` (`appid`, `apppatient`, `apptime`, `appdate`) VALUES
(4, 'Abdul', '06:55', '2025-06-18 00:00:00'),
(5, 'Averion', '15:50', '2025-05-30 00:00:00'),
(6, 'Averion', '17:30', '2025-05-30 00:00:00'),
(7, 'Abdul', '16:00', '2025-05-30 00:00:00');

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
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

INSERT INTO `inventory` (`invid`, `invname`, `invquantity`, `invdoe`, `invtype`, `invremarks`, `is_deleted`) VALUES
(1, 'Film', 50, '2024-07-10 00:00:00', 'None', 'None', 0),
(2, 'Films', 10, '2024-07-10 00:00:00', 'Equipment', 'None', 1),
(3, 'dd', 99, NULL, 'Equipment', '', 0);

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
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

INSERT INTO `patients` (`patId`, `patname`, `patemail`, `pataddress`, `patcityzipcode`, `patcontact`, `patreligion`, `patdob`, `patgender`, `patage`, `patoccupation`, `patallergies`, `is_deleted`, `last_visit`, `created_at`) VALUES
(1, 'Louie', 'qlmfvaverion@tip.edu.ph', 'Marikina City', '1902', '09166532911', 'Catholic', '2001-06-11 00:00:00', 'Male', 23, 'Conductor', 'Penicilin', 0, NULL, '2025-04-15 15:15:30'),
(2, 'Averion', 'qlmfvaverion@tip.edu.ph', 'Marikina City', '1902', '09166532911', 'Catholic', '2001-06-11 00:00:00', 'Male', 23, 'Cobra', 'Penicilin', 0, NULL, '2025-04-21 08:14:24'),
(3, 'Martin', 'dd@yahoo.com', 'Marikina City', '1902', '09166532911', 'Catholic', '2001-06-11 00:00:00', 'Male', 23, 'Teacher', 'Penicilin', 0, NULL, '2025-04-21 08:14:50'),
(4, 'Abdul', 'abdul@yahoo.com', 'Marikina City', '1202', '09166532911', 'Catholic', '2001-06-11 00:00:00', 'Male', 23, 'Conductor', 'Peanuts', 0, NULL, '2025-04-21 11:05:59');

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

INSERT INTO `rappointment` (`rappid`, `rapppatient`, `rapptime`, `rappdate`, `rappnewtime`, `rappnewdate`, `rappreason`) VALUES
(1, 'Averion', '10:00PM', '2024-07-25 00:00:00', '11:59AM', '2024-07-27 00:00:00', 'dasdas'),
(2, 'Louie', '7:00AM', '2024-07-26 00:00:00', '9:00AM', '2024-07-30 00:00:00', 'dsa'),
(3, 'Averion', '1:00AM', '2024-07-25 00:00:00', '5:30AM', '2024-07-25 00:00:00', 'dsad'),
(4, 'Averion', '5:30AM', '2024-07-25 00:00:00', '5:45AM', '2024-07-31 00:00:00', 'dasdsa'),
(5, 'Averion', '10:30', '2025-08-29 00:00:00', '17:30', '2025-05-30 00:00:00', 'WAOW');

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

INSERT INTO `reports` (`repid`, `reppatient`, `repdate`, `repprescription`, `repcleaning`, `repextraction`, `reprootcanal`, `repbraces`, `repdentures`, `repdentist`, `repothers`) VALUES
(1, 'Louie', '2024-07-10 00:00:00', 'dd', 0, 0, 0, 0, 0, 'dd', 'ddd');

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

DROP TABLE IF EXISTS `user_logs`;
CREATE TABLE `user_logs` (
  `log_id` int NOT NULL AUTO_INCREMENT,
  `user_id` int DEFAULT NULL,
  `action` varchar(255) DEFAULT NULL,
  `timestamp` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `details` text,
  PRIMARY KEY (`log_id`)
) ENGINE=InnoDB AUTO_INCREMENT=56 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

INSERT INTO `user_logs` (`log_id`, `user_id`, `action`, `timestamp`, `details`) VALUES
(1, 1, 'LOGIN', '2024-07-02 16:02:51', 'User logged in successfully.'),
(2, 1, 'LOGIN', '2024-07-02 16:03:02', 'User logged in successfully.'),
(3, 0, 'ADD_INVENTORY', '2024-07-02 16:13:50', 'Inventory item added: Dba'),
(4, 1, 'LOGIN', '2024-07-02 16:29:49', 'User logged in successfully.'),
(5, 1, 'LOGIN', '2024-07-02 16:33:11', 'User logged in successfully.'),
(6, 1, 'LOGIN', '2024-07-02 16:42:12', 'User logged in successfully.'),
(7, 0, 'ADD_INVENTORY', '2024-07-02 16:44:32', 'Inventory item added: xx'),
(8, 0, 'ADD_INVENTORY', '2024-07-02 16:44:42', 'Inventory item added: Ethanol'),
(9, 0, 'Edit_INVENTORY', '2024-07-02 16:47:02', 'Inventory item edited: dd'),
(10, 0, 'EDIT_INVENTORY', '2024-07-03 13:45:28', 'Inventory item edited: cccccc'),
(11, 0, 'ADD_INVENTORY', '2024-07-03 13:51:28', 'Inventory item added: Film'),
(12, 0, 'ADD_INVENTORY', '2024-07-03 13:54:38', 'Inventory item added: Films'),
(13, 1, 'LOGIN', '2024-07-03 14:14:42', 'User logged in successfully.'),
(14, 1, 'LOGIN', '2024-07-03 14:19:32', 'User logged in successfully.'),
(15, 0, 'EDIT_INVENTORY', '2024-07-03 14:32:17', 'Inventory item edited: Film'),
(16, 0, 'EDIT_INVENTORY', '2024-07-03 14:32:42', 'Inventory item edited: Film'),
(17, 0, 'EDIT_INVENTORY', '2024-07-03 14:32:53', 'Inventory item edited: Film'),
(18, 0, 'EDIT_INVENTORY', '2024-07-03 14:32:57', 'Inventory item edited: Film'),
(19, 1, 'LOGIN', '2024-07-03 14:37:11', 'User logged in successfully.'),
(20, 2, 'LOGIN', '2024-07-03 14:40:11', 'User logged in successfully.'),
(21, 3, 'LOGIN', '2024-07-03 14:40:18', 'User logged in successfully.'),
(22, 2, 'LOGIN', '2024-07-03 14:40:36', 'User logged in successfully.'),
(23, 1, 'LOGIN', '2024-07-03 14:54:25', 'User logged in successfully.'),
(24, 1, 'LOGIN', '2024-07-03 15:56:34', 'User logged in successfully.'),
(25, 1, 'LOGIN', '2024-07-03 17:36:19', 'User logged in successfully.'),
(26, 1, 'LOGIN', '2024-07-03 22:19:49', 'User logged in successfully.'),
(27, 2, 'LOGIN', '2024-07-04 08:32:43', 'User logged in successfully.'),
(28, 1, 'LOGIN', '2024-07-04 09:01:59', 'User logged in successfully.'),
(29, 2, 'LOGIN', '2024-07-04 09:10:38', 'User logged in successfully.'),
(30, 2, 'LOGIN', '2024-07-04 09:11:08', 'User logged in successfully.'),
(31, 2, 'LOGIN', '2024-07-04 09:11:38', 'User logged in successfully.'),
(32, -1, 'LOGIN_FAILED', '2024-07-05 21:57:03', 'User login failed.'),
(33, -1, 'LOGIN_FAILED', '2024-07-05 21:57:08', 'User login failed.'),
(34, -1, 'LOGIN_FAILED', '2024-07-05 21:57:09', 'User login failed.'),
(35, 1, 'LOGIN_FAILED', '2024-07-06 10:50:59', 'User login failed.'),
(36, 1, 'LOGIN_FAILED', '2024-07-06 10:57:58', 'User login failed.'),
(37, 1, 'LOGIN_FAILED', '2024-07-06 10:58:00', 'User login failed.'),
(38, 1, 'LOGIN', '2024-07-06 11:00:22', 'User logged in successfully.'),
(39, -1, 'LOGIN_FAILED', '2024-07-06 11:01:11', 'User login failed.'),
(40, -1, 'LOGIN_FAILED', '2024-07-06 11:01:13', 'User login failed.'),
(41, -1, 'LOGIN_FAILED', '2024-07-06 11:01:14', 'User login failed.'),
(42, 1, 'LOGIN', '2024-07-06 11:06:11', 'User logged in successfully.'),
(43, -1, 'LOGIN_FAILED', '2024-07-07 12:52:05', 'User login failed.'),
(44, -1, 'LOGIN_FAILED', '2024-07-07 12:52:09', 'User login failed.'),
(45, 1, 'LOGIN', '2024-07-07 12:56:05', 'User logged in successfully.'),
(46, 1, 'LOGIN', '2024-07-07 14:20:50', 'User logged in successfully.'),
(47, -1, 'LOGIN_FAILED', '2024-07-07 15:14:08', 'User login failed.'),
(48, -1, 'LOGIN_FAILED', '2024-07-07 15:14:09', 'User login failed.'),
(49, -1, 'LOGIN_FAILED', '2024-07-07 15:14:11', 'User login failed.'),
(50, 1, 'LOGIN', '2024-07-07 15:14:32', 'User logged in successfully.'),
(51, 1, 'LOGIN', '2024-07-11 13:36:16', 'User logged in successfully.'),
(52, 1, 'LOGIN', '2024-07-11 13:39:11', 'User logged in successfully.'),
(53, -1, 'LOGIN_FAILED', '2025-03-03 13:30:21', 'User login failed.'),
(54, 1, 'LOGIN_FAILED', '2025-03-03 13:30:47', 'User login failed.'),
(55, 1, 'LOGIN_FAILED', '2025-03-03 13:30:52', 'User login failed.');

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
  PRIMARY KEY (`usersid`),
  UNIQUE KEY `usersusername` (`usersusername`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

INSERT INTO `users` (`usersid`, `usersusername`, `userspassword`, `usersrealname`, `usersemail`, `usershomeaddress`, `userscityzipcode`, `userscontact`, `usersreligion`, `usersdob`, `usersgender`, `usersage`, `usersoccupation`, `usersaccess`, `key`) VALUES
(1, 'tintin', '123', 'tintin', 'tintin@yahoo.com', 'MC', '2222', '2222222222', '222', '2001-06-11 00:00:00', 'Male', 22, 'tin', 'admin', NULL),
(2, 'tin', '123', 'Tin User', 'tin@example.com', '123 Main St', '12345', '555-1234', 'None', '1990-01-01 00:00:00', 'Other', 35, 'Magician', 'user', NULL),
(3, 'loe', '123', 'Averion Louie', 'qlmfvaverion@tip.edu.ph', '', '', '11111111111', '', NULL, 'Male', 35, 'Killer', 'admin', NULL),
(4, 'da', '123', 'DA', 'qlmfvaverion@tip.edu.ph', '', '', 'DA', '', NULL, 'Male', 35, 'Teacher', 'user', NULL),
(5, 'abc', '123', 'abc', 'abcdsad@yahoo.com', 'Marikina', '1234', '12345678909', 'Roman Catholic', '1999-11-11 00:00:00', 'Other', 25, 'Prophet', 'admin', NULL);

SET FOREIGN_KEY_CHECKS=1;
