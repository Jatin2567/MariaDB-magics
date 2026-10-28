-- The image created studio_reader for this fresh local database.
REVOKE ALL PRIVILEGES ON magics.* FROM 'studio_reader'@'%';
GRANT SELECT ON magics.* TO 'studio_reader'@'%';
