CREATE TABLE `member` (
    `id` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
    `name` varchar(50) NOT NULL,
    `gender` enum('M','F') NOT NULL,
    `address` text,
    `phone` varchar(20) DEFAULT NULL,
    `mobile` varchar(20) DEFAULT NULL,
    `email` varchar(30) DEFAULT NULL,
    `occupation` varchar(20) DEFAULT NULL,
    `birth_date` date DEFAULT NULL,
    `photo` varchar(100) DEFAULT NULL,
    `parent_id` mediumint(8) unsigned DEFAULT NULL,
    `added_date` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `parent_id` (`parent_id`)
) ENGINE=InnoDB;
