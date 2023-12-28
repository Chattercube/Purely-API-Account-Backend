CREATE TABLE Users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(50) NOT NULL,
    password VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL
);

CREATE TABLE Sessions (
    session_id VARCHAR(50) PRIMARY KEY,
    user_id INTEGER NOT NULL,
    start_time DATETIME NOT NULL,
    FOREIGN KEY (user_id) REFERENCES Users(user_id)
);

CREATE TABLE SessionData (
    session_id VARCHAR(50) PRIMARY KEY,
    ip_address VARCHAR(50) NOT NULL,
    user_agent VARCHAR(255) NOT NULL,
    FOREIGN KEY (session_id) REFERENCES Sessions(session_id)
);

CREATE TABLE EmailVerify (
    email VARCHAR(100) PRIMARY KEY,
    code TEXT NOT NULL,
    creation_time DATETIME NOT NULL
);