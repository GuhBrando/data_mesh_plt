-- 1. ADMIN
DO $$ BEGIN RAISE NOTICE 'Injetando senha: %', '{{ .admin_password }}'; END $$;

DO $$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'admin') THEN
      EXECUTE format('CREATE ROLE admin WITH LOGIN PASSWORD %L', '{{ .admin_password }}');
   ELSE
      EXECUTE format('ALTER ROLE admin WITH PASSWORD %L', '{{ .admin_password }}');
   END IF;
END
$$;

-- 2. APP_USER
DO $$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'app_user') THEN
      EXECUTE format('CREATE ROLE app_user WITH LOGIN PASSWORD %L', '{{ .app_user_password }}');
   ELSE
      EXECUTE format('ALTER ROLE app_user WITH PASSWORD %L', '{{ .app_user_password }}');
   END IF;
END
$$;

-- 3. READONLY_USER
DO $$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'readonly_user') THEN
      EXECUTE format('CREATE ROLE readonly_user WITH LOGIN PASSWORD %L', '{{ .readonly_password }}');
   ELSE
      EXECUTE format('ALTER ROLE readonly_user WITH PASSWORD %L', '{{ .readonly_password }}');
   END IF;
END
$$;

-- Permissões
GRANT ALL PRIVILEGES ON DATABASE data_mesh_plt TO admin;
GRANT USAGE ON SCHEMA iam TO app_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA iam TO app_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA iam GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO app_user;
ALTER ROLE app_user SET search_path TO iam, public;
GRANT USAGE ON SCHEMA iam TO readonly_user;
GRANT SELECT ON ALL TABLES IN SCHEMA iam TO readonly_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA iam GRANT SELECT ON TABLES TO readonly_user;
REVOKE ALL ON SCHEMA iam FROM PUBLIC;