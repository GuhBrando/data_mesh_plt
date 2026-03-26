-- Bloco para o ADMIN
DO $$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'admin') THEN
      EXECUTE format('CREATE ROLE admin WITH LOGIN PASSWORD %L', '{{ var "admin_password" }}');
   END IF;
END
$$;

-- Bloco para o APP_USER
DO $$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'app_user') THEN
      EXECUTE format('CREATE ROLE app_user WITH LOGIN PASSWORD %L', '{{ var "app_user_password" }}');
   END IF;
END
$$;

-- Bloco para o READONLY_USER
DO $$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'readonly_user') THEN
      EXECUTE format('CREATE ROLE readonly_user WITH LOGIN PASSWORD %L', '{{ var "readonly_password" }}');
   END IF;
END
$$;

-- Permissões GERAIS
GRANT ALL PRIVILEGES ON DATABASE data_mesh_plt TO admin;

-- Permissões IAM para APP_USER
GRANT USAGE ON SCHEMA iam TO app_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA iam TO app_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA iam GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO app_user;
ALTER ROLE app_user SET search_path TO iam, public;

-- Permissões IAM para READONLY_USER
GRANT USAGE ON SCHEMA iam TO readonly_user;
GRANT SELECT ON ALL TABLES IN SCHEMA iam TO readonly_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA iam GRANT SELECT ON TABLES TO readonly_user;

-- Segurança
REVOKE ALL ON SCHEMA iam FROM PUBLIC;