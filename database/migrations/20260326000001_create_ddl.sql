CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- =====================================================
-- SCHEMAS
-- =====================================================

CREATE SCHEMA IF NOT EXISTS iam;
CREATE SCHEMA IF NOT EXISTS catalog;
CREATE SCHEMA IF NOT EXISTS platform;
CREATE SCHEMA IF NOT EXISTS governance;

-- =====================================================
-- ENUM TYPES
-- =====================================================

-- IAM
CREATE TYPE iam.principal_type AS ENUM (
    'USER',
    'GROUP',
    'SERVICE'
);

-- GOVERNANCE
CREATE TYPE governance.permission_type AS ENUM (
    'READ',
    'WRITE',
    'ADMIN'
);

CREATE TYPE governance.resource_type AS ENUM (
    'DATA_PRODUCT',
    'DATA_CONTRACT',
    'DATA_PORT'
);

CREATE TYPE governance.grant_status AS ENUM (
    'ACTIVE',
    'REVOKED',
    'EXPIRED'
);

-- PLATFORM
CREATE TYPE platform.port_role_type AS ENUM (
    'INPUT',
    'OUTPUT',
    'INTERNAL'
);

CREATE TYPE platform.binding_status AS ENUM (
    'ACTIVE',
    'DISABLED'
);

-- =====================================================
-- IAM
-- =====================================================

CREATE TABLE iam.users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE iam.principals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    type iam.principal_type NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE iam.principal_memberships (
    users_id UUID NOT NULL,
    principals_id UUID NOT NULL,
    PRIMARY KEY (users_id, principals_id),
    FOREIGN KEY (users_id)
        REFERENCES iam.users(id)
        ON DELETE CASCADE,
    FOREIGN KEY (principals_id)
        REFERENCES iam.principals(id)
        ON DELETE CASCADE
);

CREATE INDEX idx_membership_principal
ON iam.principal_memberships(principals_id);

-- =====================================================
-- CATALOG
-- =====================================================

CREATE TABLE catalog.data_contracts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    obj JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE catalog.data_products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    data_contracts_id UUID NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    FOREIGN KEY (data_contracts_id)
        REFERENCES catalog.data_contracts(id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE
);

CREATE INDEX idx_data_products_contract
ON catalog.data_products(data_contracts_id);

-- =====================================================
-- PLATFORM
-- =====================================================

CREATE TABLE platform.control_port_types (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL UNIQUE,
    action_url TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE platform.control_ports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    control_port_type_id UUID NOT NULL,
    data_products_id UUID NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    FOREIGN KEY (control_port_type_id)
        REFERENCES platform.control_port_types(id)
        ON DELETE RESTRICT,
    FOREIGN KEY (data_products_id)
        REFERENCES catalog.data_products(id)
        ON DELETE CASCADE
);

CREATE INDEX idx_control_ports_product
ON platform.control_ports(data_products_id);

CREATE TABLE platform.data_ports_type (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    type TEXT NOT NULL,
    connection_ref TEXT NOT NULL,
    schema_ref TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE platform.data_ports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    port_role platform.port_role_type NOT NULL,
    data_ports_type_id UUID NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    FOREIGN KEY (data_ports_type_id)
        REFERENCES platform.data_ports_type(id)
        ON DELETE RESTRICT
);

CREATE INDEX idx_data_ports_type
ON platform.data_ports(data_ports_type_id);

CREATE TABLE platform.product_port_binding (
    data_products_id UUID NOT NULL,
    data_ports_id UUID NOT NULL,
    status platform.binding_status NOT NULL,
    PRIMARY KEY (data_products_id, data_ports_id),
    FOREIGN KEY (data_products_id)
        REFERENCES catalog.data_products(id)
        ON DELETE CASCADE,
    FOREIGN KEY (data_ports_id)
        REFERENCES platform.data_ports(id)
        ON DELETE RESTRICT
);

CREATE INDEX idx_binding_port
ON platform.product_port_binding(data_ports_id);

-- =====================================================
-- GOVERNANCE
-- =====================================================

CREATE TABLE governance.access_grant (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    resource_type governance.resource_type NOT NULL,
    resource_id UUID NOT NULL,
    principals_id UUID NOT NULL,
    permission governance.permission_type NOT NULL,
    status governance.grant_status NOT NULL,
    granted_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    FOREIGN KEY (principals_id)
        REFERENCES iam.principals(id)
        ON DELETE CASCADE,
    CHECK (expires_at IS NULL OR expires_at > granted_at)
);

CREATE INDEX idx_access_grant_principal
ON governance.access_grant(principals_id);

CREATE INDEX idx_access_grant_resource
ON governance.access_grant(resource_type, resource_id);
