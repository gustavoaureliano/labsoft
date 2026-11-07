-- Initial payment roles/schema. Business tables use Alembic.
\set ON_ERROR_STOP on
\getenv migration_password PAYMENT_MIGRATION_PASSWORD
\getenv runtime_password PAYMENT_RUNTIME_PASSWORD
BEGIN;
CREATE ROLE aa_payment_migration LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE PASSWORD :'migration_password';
CREATE ROLE aa_payment_runtime LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE PASSWORD :'runtime_password';
SELECT format('GRANT CONNECT ON DATABASE %I TO aa_payment_migration, aa_payment_runtime', current_database()) \gexec
CREATE SCHEMA payment AUTHORIZATION aa_payment_migration;
REVOKE ALL ON SCHEMA payment FROM PUBLIC;
GRANT USAGE ON SCHEMA payment TO aa_payment_runtime;
ALTER DEFAULT PRIVILEGES FOR ROLE aa_payment_migration IN SCHEMA payment GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO aa_payment_runtime;
ALTER DEFAULT PRIVILEGES FOR ROLE aa_payment_migration IN SCHEMA payment GRANT USAGE, SELECT ON SEQUENCES TO aa_payment_runtime;
SELECT format('ALTER ROLE aa_payment_migration IN DATABASE %I SET search_path = payment', current_database()) \gexec
SELECT format('ALTER ROLE aa_payment_runtime IN DATABASE %I SET search_path = payment', current_database()) \gexec
COMMIT;
