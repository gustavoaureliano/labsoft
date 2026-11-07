-- Run once as administrator in a new integration database, never at app startup.
-- psql reads passwords from the environment; do not pass them on the command line.
\set ON_ERROR_STOP on
\getenv migration_password LEARNING_MIGRATION_PASSWORD
\getenv runtime_password LEARNING_RUNTIME_PASSWORD

BEGIN;
CREATE ROLE aa_learning_migration LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE PASSWORD :'migration_password';
CREATE ROLE aa_learning_runtime LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE PASSWORD :'runtime_password';
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
SELECT format('REVOKE ALL ON DATABASE %I FROM PUBLIC', current_database()) \gexec
SELECT format('GRANT CONNECT ON DATABASE %I TO aa_learning_migration, aa_learning_runtime', current_database()) \gexec
CREATE SCHEMA learning AUTHORIZATION aa_learning_migration;
REVOKE ALL ON SCHEMA learning FROM PUBLIC;
GRANT USAGE ON SCHEMA learning TO aa_learning_runtime;
ALTER DEFAULT PRIVILEGES FOR ROLE aa_learning_migration IN SCHEMA learning
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO aa_learning_runtime;
ALTER DEFAULT PRIVILEGES FOR ROLE aa_learning_migration IN SCHEMA learning
    GRANT USAGE, SELECT ON SEQUENCES TO aa_learning_runtime;
SELECT format('ALTER ROLE aa_learning_migration IN DATABASE %I SET search_path = learning', current_database()) \gexec
SELECT format('ALTER ROLE aa_learning_runtime IN DATABASE %I SET search_path = learning', current_database()) \gexec
COMMIT;
