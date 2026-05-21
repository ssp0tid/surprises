-- Employees and Departments Sample Database

CREATE TABLE IF NOT EXISTS employees (
    id INTEGER PRIMARY KEY,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    email TEXT UNIQUE,
    department_id INTEGER,
    salary INTEGER,
    hire_date TEXT,
    FOREIGN KEY (department_id) REFERENCES departments(id)
);

CREATE TABLE IF NOT EXISTS departments (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    budget INTEGER,
    manager_id INTEGER
);

INSERT INTO departments VALUES (1, 'Engineering', 500000, NULL);
INSERT INTO departments VALUES (2, 'Marketing', 200000, NULL);
INSERT INTO departments VALUES (3, 'Sales', 300000, NULL);
INSERT INTO departments VALUES (4, 'Human Resources', 150000, NULL);

INSERT INTO employees VALUES (1, 'John', 'Doe', 'john.doe@example.com', 1, 75000, '2019-01-15');
INSERT INTO employees VALUES (2, 'Jane', 'Smith', 'jane.smith@example.com', 1, 82000, '2018-03-22');
INSERT INTO employees VALUES (3, 'Bob', 'Johnson', 'bob.johnson@example.com', 2, 65000, '2020-06-10');
INSERT INTO employees VALUES (4, 'Alice', 'Williams', 'alice.williams@example.com', 3, 70000, '2017-11-05');
INSERT INTO employees VALUES (5, 'Charlie', 'Brown', 'charlie.brown@example.com', 1, 78000, '2019-08-20');
INSERT INTO employees VALUES (6, 'Diana', 'Miller', 'diana.miller@example.com', 4, 62000, '2021-02-14');
INSERT INTO employees VALUES (7, 'Edward', 'Davis', 'edward.davis@example.com', 3, 68000, '2018-09-30');
INSERT INTO employees VALUES (8, 'Fiona', 'Garcia', 'fiona.garcia@example.com', 2, 71000, '2020-04-18');
INSERT INTO employees VALUES (9, 'George', 'Martinez', 'george.martinez@example.com', 1, 85000, '2016-12-01');
INSERT INTO employees VALUES (10, 'Hannah', 'Anderson', 'hannah.anderson@example.com', 4, 60000, '2022-01-10');