-- Initial subscription schema/roles; business tables use Alembic.
\set ON_ERROR_STOP on
\getenv migration_password SUBSCRIPTION_MIGRATION_PASSWORD
\getenv runtime_password SUBSCRIPTION_RUNTIME_PASSWORD
BEGIN;
CREATE ROLE aa_subscription_migration LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE PASSWORD :'migration_password';
CREATE ROLE aa_subscription_runtime LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE PASSWORD :'runtime_password';
SELECT format('GRANT CONNECT ON DATABASE %I TO aa_subscription_migration, aa_subscription_runtime', current_database()) \gexec
CREATE SCHEMA subscription AUTHORIZATION aa_subscription_migration;
REVOKE ALL ON SCHEMA subscription FROM PUBLIC;
GRANT USAGE ON SCHEMA subscription TO aa_subscription_runtime;
ALTER DEFAULT PRIVILEGES FOR ROLE aa_subscription_migration IN SCHEMA subscription GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO aa_subscription_runtime;
ALTER DEFAULT PRIVILEGES FOR ROLE aa_subscription_migration IN SCHEMA subscription GRANT USAGE, SELECT ON SEQUENCES TO aa_subscription_runtime;
SELECT format('ALTER ROLE aa_subscription_migration IN DATABASE %I SET search_path = subscription', current_database()) \gexec
SELECT format('ALTER ROLE aa_subscription_runtime IN DATABASE %I SET search_path = subscription', current_database()) \gexec
COMMIT;
