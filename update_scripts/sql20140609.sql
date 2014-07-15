DO $$ 
    BEGIN
        BEGIN
            alter table question add long_answer boolean not null default false;
        EXCEPTION
            WHEN duplicate_column THEN RAISE NOTICE 'column long_answer already exists.';
        END;
        CREATE TABLE userreview (
            id SERIAL NOT NULL, 
            user_id INTEGER NOT NULL, 
            event_id INTEGER, 
            rating INTEGER NOT NULL, 
            active BOOLEAN NOT NULL, 
            date_created TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
            creator_user_id INTEGER NOT NULL, 
            review VARCHAR(5000), 
            PRIMARY KEY (id), 
            CONSTRAINT "Rating is negative" CHECK (rating>=0), 
            CONSTRAINT "Rating is greater than 5" CHECK (rating<=5), 
            FOREIGN KEY(user_id) REFERENCES "user" (id), 
            FOREIGN KEY(event_id) REFERENCES event (id), 
            FOREIGN KEY(creator_user_id) REFERENCES "user" (id)
       );
    END;
$$
