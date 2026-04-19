-- Grant admin full access to all application schemas and their objects
GRANT ALL PRIVILEGES ON SCHEMA iam, catalog, platform, governance TO admin;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA iam, catalog, platform, governance TO admin;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA iam, catalog, platform, governance TO admin;

-- Ensure future tables are also accessible by admin
ALTER DEFAULT PRIVILEGES IN SCHEMA iam GRANT ALL PRIVILEGES ON TABLES TO admin;
ALTER DEFAULT PRIVILEGES IN SCHEMA catalog GRANT ALL PRIVILEGES ON TABLES TO admin;
ALTER DEFAULT PRIVILEGES IN SCHEMA platform GRANT ALL PRIVILEGES ON TABLES TO admin;
ALTER DEFAULT PRIVILEGES IN SCHEMA governance GRANT ALL PRIVILEGES ON TABLES TO admin;
