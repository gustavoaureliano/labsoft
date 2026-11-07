-- Initial checkout roles/schema. Business tables use Alembic.
\set ON_ERROR_STOP on
\getenv migration_password CHECKOUT_MIGRATION_PASSWORD
\getenv runtime_password CHECKOUT_RUNTIME_PASSWORD
BEGIN;
CREATE ROLE aa_checkout_migration LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE PASSWORD :'migration_password';
CREATE ROLE aa_checkout_runtime LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE PASSWORD :'runtime_password';
SELECT format('GRANT CONNECT ON DATABASE %I TO aa_checkout_migration, aa_checkout_runtime', current_database()) \gexec
CREATE SCHEMA checkout AUTHORIZATION aa_checkout_migration;
REVOKE ALL ON SCHEMA checkout FROM PUBLIC;
GRANT USAGE ON SCHEMA checkout TO aa_checkout_runtime;
ALTER DEFAULT PRIVILEGES FOR ROLE aa_checkout_migration IN SCHEMA checkout GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO aa_checkout_runtime;
ALTER DEFAULT PRIVILEGES FOR ROLE aa_checkout_migration IN SCHEMA checkout GRANT USAGE, SELECT ON SEQUENCES TO aa_checkout_runtime;
SELECT format('ALTER ROLE aa_checkout_migration IN DATABASE %I SET search_path = checkout', current_database()) \gexec
SELECT format('ALTER ROLE aa_checkout_runtime IN DATABASE %I SET search_path = checkout', current_database()) \gexec
COMMIT;
