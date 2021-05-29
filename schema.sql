-- DROP TABLE tbleventupdates;
-- DROP TABLE tblpollvotes;
-- DROP TABLE tblpolloptions;
-- DROP TABLE tblavailability;
-- DROP TABLE tbldatetime;
-- DROP TABLE tblinvitations;
-- DROP TABLE tblevents;
-- DROP TABLE tblpolls;
-- DROP TABLE tblaccounts;

CREATE TABLE tblaccounts (
	username varchar(30) NOT NULL,
	email varchar(320) NOT NULL,
	displayName varchar(50) NOT NULL,
	password varchar(300) NOT NULL,
	PRIMARY KEY (username)
);

CREATE TABLE tblpolls (
	pollID int(10) unsigned NOT NULL,
	title varchar(100) NOT NULL,
	chooseMany int(1) NOT NULL DEFAULT 0,
	PRIMARY KEY (pollID)
);

CREATE TABLE tblevents (
	eventID int(10) unsigned NOT NULL AUTO_INCREMENT,
	creator varchar(30) NOT NULL,
	eventName varchar(50) NOT NULL,
	description varchar(250),
	tag1 varchar(20),
	tag2 varchar(20),
	tag3 varchar(20),
	pollID int(10) unsigned,
	locationName varchar(50),
	locationDescription varchar(250),
	PRIMARY KEY (eventID),
	FOREIGN KEY (creator) REFERENCES tblaccounts(username),
	FOREIGN KEY (pollID) REFERENCES tblpolls(pollID)
);

CREATE TABLE tblinvitations (
	invitationID int(10) unsigned NOT NULL AUTO_INCREMENT,
	eventID int(10) unsigned NOT NULL,
	invitee varchar(30) NOT NULL,
	viewed char(1) NOT NULL DEFAULT 0,
	PRIMARY KEY (invitationID),
	FOREIGN KEY (eventID) REFERENCES tblevents(eventID),
	FOREIGN KEY (invitee) REFERENCES tblaccounts(username)
);

CREATE TABLE tbldatetime (
	dateTimeID int(10) unsigned NOT NULL AUTO_INCREMENT,
	eventID int(10) unsigned NOT NULL,
	date varchar(10) NOT NULL,
	startTime varchar(5),
	endTime varchar(5),
	PRIMARY KEY (dateTimeID),
	FOREIGN KEY (eventID) REFERENCES tblevents(eventID)
);

CREATE TABLE tblavailability (
	dateTimeID int(10) unsigned NOT NULL,
	invitationID int(10) unsigned NOT NULL,
	availability char(1) NOT NULL,
	PRIMARY KEY (dateTimeID, invitationID),
	FOREIGN KEY (dateTimeID) REFERENCES tbldatetime(dateTimeID),
	FOREIGN KEY (invitationID) REFERENCES tblinvitations(invitationID)
);

CREATE TABLE tblpolloptions (
	pollID int(10) unsigned NOT NULL,
	optionNo int(4) unsigned NOT NULL,
	optionText varchar(30),
	PRIMARY KEY (pollID, optionNo),
	FOREIGN KEY (pollID) REFERENCES tblpolls(pollID)
);

CREATE TABLE tblpollvotes (
	voteID int(10) unsigned NOT NULL AUTO_INCREMENT,
	pollID int(10) unsigned NOT NULL,
	invitationID int(10) unsigned NOT NULL,
	optionNo int(4) unsigned NOT NULL,
	PRIMARY KEY (voteID),
	FOREIGN KEY (pollID) REFERENCES tblpolls(pollID),
	FOREIGN KEY (invitationID) REFERENCES tblinvitations(invitationID)
);

CREATE TABLE tbleventupdates (
	updateID int(10) unsigned NOT NULL AUTO_INCREMENT,
	eventID int(10) unsigned NOT NULL,
	invitee varchar(30),
	updateCode int(2) NOT NULL,
	updateTime timestamp NOT NULL,
	viewed int(1) NOT NULL DEFAULT 0,
	PRIMARY KEY (updateID),
	FOREIGN KEY (eventID) REFERENCES tblevents(eventID),
	FOREIGN KEY (invitee) REFERENCES tblaccounts(username)
);

-- DROP USER 'appuser'@'localhost';
CREATE USER 'appuser'@'localhost' IDENTIFIED BY 'password';
GRANT ALL PRIVILEGES ON appdata.* TO 'appuser'@'localhost';
REVOKE DROP ON appdata.* FROM 'appuser'@'localhost';