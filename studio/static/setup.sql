-- Run ONCE in a fresh MariaDB schema as its owner, using a SQL client.
-- Choose/create the schema in your provider first (suggested name: magics).
-- Studio is read-only: setup statements belong in your admin SQL client.
-- These names are intentionally unique to this tutorial; no existing data is deleted.
CREATE TABLE studio_documents (
    id INT PRIMARY KEY,
    title VARCHAR(120) NOT NULL,
    embedding VECTOR(3) NOT NULL,
    VECTOR INDEX (embedding) M=8 DISTANCE=cosine
);
INSERT INTO studio_documents VALUES
    (1, 'SQL and databases', VEC_FromText('[1,0,0]')),
    (2, 'Related database topic', VEC_FromText('[0.9,0.1,0]')),
    (3, 'A different topic', VEC_FromText('[0,1,0]'));

CREATE TABLE studio_history (
    id INT PRIMARY KEY,
    name VARCHAR(80),
    salary INT
) WITH SYSTEM VERSIONING;
INSERT INTO studio_history VALUES (1, 'Olivia Chen', 100000);
-- Remember the instant before the change, in this SQL session.
SET @before_raise = NOW(6);
DO SLEEP(1);
UPDATE studio_history SET salary = 125000 WHERE id = 1;
-- Copy this timestamp into Studio's Time travel form, including microseconds.
SELECT @before_raise AS use_this_as_of, @@session.time_zone AS database_time_zone;
SELECT * FROM studio_history FOR SYSTEM_TIME AS OF @before_raise;
-- Expected salary: 100000. Current salary: 125000.
SELECT id, name, salary, ROW_START, ROW_END
FROM studio_history FOR SYSTEM_TIME ALL ORDER BY ROW_START;
