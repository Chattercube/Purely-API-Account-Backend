CREATE TABLE UserData (
    
    user_id INTEGER PRIMARY KEY,
    data TEXT NOT NULL,
    inventory TEXT NOT NULL,

    -- add other columns where necessary

    FOREIGN KEY (user_id) REFERENCES Users(user_id)
);   

