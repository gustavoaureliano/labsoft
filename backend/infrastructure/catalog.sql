-- Initial catalog schema/roles; application tables are created by Alembic.
\set ON_ERROR_STOP on
\getenv migration_password CATALOG_MIGRATION_PASSWORD
\getenv runtime_password CATALOG_RUNTIME_PASSWORD
BEGIN;
CREATE ROLE aa_catalog_migration LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE PASSWORD :'migration_password';
CREATE ROLE aa_catalog_runtime LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE PASSWORD :'runtime_password';
SELECT format('GRANT CONNECT ON DATABASE %I TO aa_catalog_migration, aa_catalog_runtime', current_database()) \gexec
CREATE SCHEMA catalog AUTHORIZATION aa_catalog_migration;
REVOKE ALL ON SCHEMA catalog FROM PUBLIC;
GRANT USAGE ON SCHEMA catalog TO aa_catalog_runtime;
ALTER DEFAULT PRIVILEGES FOR ROLE aa_catalog_migration IN SCHEMA catalog GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO aa_catalog_runtime;
ALTER DEFAULT PRIVILEGES FOR ROLE aa_catalog_migration IN SCHEMA catalog GRANT USAGE, SELECT ON SEQUENCES TO aa_catalog_runtime;
SELECT format('ALTER ROLE aa_catalog_migration IN DATABASE %I SET search_path = catalog', current_database()) \gexec
SELECT format('ALTER ROLE aa_catalog_runtime IN DATABASE %I SET search_path = catalog', current_database()) \gexec
COMMIT;
