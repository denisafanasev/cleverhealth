create table users(
	doc_id INT PRIMARY KEY UNIQUE,
	login VARCHAR ( 15 ) UNIQUE NOT NULL,
	password VARCHAR ( 50 ),
	email VARCHAR ( 50 ) UNIQUE NOT NULL,
	role VARCHAR ( 15 ) NOT NULL,
	name VARCHAR ( 50 ) NOT NULL,
	created_date TIMESTAMP NOT NULL,
	education_module_expiration_date TIMESTAMP NOT NULL,
	probationers_number INT NOT NULL,
	active BOOLEAN DEFAULT FALSE,
	email_confirmed BOOLEAN DEFAULT FALSE,
	token VARCHAR ( 255 )
);

create table action(
	doc_id INT PRIMARY KEY UNIQUE ,
	user_id INT NOT NULL,
	action VARCHAR ( 200 ) NOT NULL,
	comment_action VARCHAR ( 250 ) NOT NULL,
	created_date TIMESTAMP NOT NULL
);

create table courses_list
(
    doc_id      INT PRIMARY KEY,
    name        VARCHAR(150) NOT NULL,
    description TEXT         NOT NULL,
    type        VARCHAR(20)  NOT NULL,
    image       VARCHAR(200) NOT NULL
);

create table modules
(
    doc_id    INT PRIMARY KEY,
    id_course INT          NOT NULL,
    name      VARCHAR(150) NOT NULL
);

create table lessons
(
    doc_id    INT PRIMARY KEY,
    id_module INT          NOT NULL,
    name      VARCHAR(150) NOT NULL,
    materials VARCHAR(100)[],
    task      TEXT         NULL,
    text      TEXT         NULL,
    link      jsonb[]
);

create table homeworks
(
    doc_id           INT PRIMARY KEY,
    id_lesson        INT       NOT NULL,
    id_user          INT       NOT NULL,
    users_files_list VARCHAR(100)[],
    text             TEXT      NOT NULL,
    status           BOOLEAN   NULL,
    date_delivery    TIMESTAMP NOT NULL
);

create table homework_chat
(
    doc_id    INT PRIMARY KEY,
    id_lesson INT NOT NULL,
    id_user   INT NOT NULL
);

create table message
(
    doc_id           INT PRIMARY KEY,
    id_user          INT       NOT NULL,
    text             TEXT      NOT NULL,
    date_send        TIMESTAMP NOT NULL,
    id_homework_chat INT       NOT NULL,
    read             BOOLEAN   NOT NULL
)