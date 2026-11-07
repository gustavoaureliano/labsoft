-- Initial provisioning in the integration database; application tables use Alembic.
\set ON_ERROR_STOP on
\getenv migration_password IDENTITY_MIGRATION_PASSWORD
\getenv runtime_password IDENTITY_RUNTIME_PASSWORD

BEGIN;
CREATE ROLE aa_identity_migration LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE PASSWORD :'migration_password';
CREATE ROLE aa_identity_runtime LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE PASSWORD :'runtime_password';
SELECT format('GRANT CONNECT ON DATABASE %I TO aa_identity_migration, aa_identity_runtime', current_database()) \gexec
CREATE SCHEMA identity AUTHORIZATION aa_identity_migration;
REVOKE ALL ON SCHEMA identity FROM PUBLIC;
GRANT USAGE ON SCHEMA identity TO aa_identity_runtime;
ALTER DEFAULT PRIVILEGES FOR ROLE aa_identity_migration IN SCHEMA identity
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO aa_identity_runtime;
ALTER DEFAULT PRIVILEGES FOR ROLE aa_identity_migration IN SCHEMA identity
    GRANT USAGE, SELECT ON SEQUENCES TO aa_identity_runtime;
SELECT format('ALTER ROLE aa_identity_migration IN DATABASE %I SET search_path = identity', current_database()) \gexec
SELECT format('ALTER ROLE aa_identity_runtime IN DATABASE %I SET search_path = identity', current_database()) \gexec
COMMIT;
