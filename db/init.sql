CREATE TABLE IF NOT EXISTS notes (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS files (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    person_name TEXT NOT NULL,
    date_of_birth DATE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


INSERT INTO notes (title) VALUES ('Hello from Postgres + Docker!');

INSERT INTO files (title, person_name, date_of_birth)
VALUES ('Erste Akte', 'Max Mustermann', '1990-05-15');