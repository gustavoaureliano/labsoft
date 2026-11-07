-- Initial engagement schema/roles; application tables use Alembic.
\set ON_ERROR_STOP on
\getenv migration_password ENGAGEMENT_MIGRATION_PASSWORD
\getenv runtime_password ENGAGEMENT_RUNTIME_PASSWORD
BEGIN;
CREATE ROLE aa_engagement_migration LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE PASSWORD :'migration_password';
CREATE ROLE aa_engagement_runtime LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE PASSWORD :'runtime_password';
SELECT format('GRANT CONNECT ON DATABASE %I TO aa_engagement_migration, aa_engagement_runtime', current_database()) \gexec
CREATE SCHEMA engagement AUTHORIZATION aa_engagement_migration;
REVOKE ALL ON SCHEMA engagement FROM PUBLIC;
GRANT USAGE ON SCHEMA engagement TO aa_engagement_runtime;
ALTER DEFAULT PRIVILEGES FOR ROLE aa_engagement_migration IN SCHEMA engagement GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO aa_engagement_runtime;
ALTER DEFAULT PRIVILEGES FOR ROLE aa_engagement_migration IN SCHEMA engagement GRANT USAGE, SELECT ON SEQUENCES TO aa_engagement_runtime;
SELECT format('ALTER ROLE aa_engagement_migration IN DATABASE %I SET search_path = engagement', current_database()) \gexec
SELECT format('ALTER ROLE aa_engagement_runtime IN DATABASE %I SET search_path = engagement', current_database()) \gexec
COMMIT;
