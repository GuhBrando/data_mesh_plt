CREATE SCHEMA IF NOT EXISTS data_mesh_plt;

-- USERS
CREATE TABLE data_mesh_plt.users (
    id INT PRIMARY KEY,
    name VARCHAR(45) NOT NULL,
    email VARCHAR(45) NOT NULL,
    created_at TIMESTAMP NOT NULL
);

-- DATA CONTRACTS
CREATE TABLE data_mesh_plt.data_contracts (
    id INT PRIMARY KEY,
    obj JSONB NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);

-- DATA PRODUCTS
-- Bloqueia delete do contract se houver product vinculado
CREATE TABLE data_mesh_plt.data_products (
    id INT PRIMARY KEY,
    name VARCHAR(45) NOT NULL,
    description VARCHAR(255) NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    data_contracts_id INT NOT NULL,
    CONSTRAINT fk_data_products_data_contracts
        FOREIGN KEY (data_contracts_id)
        REFERENCES data_mesh_plt.data_contracts(id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE
);

-- CONTROL PORT TYPES
CREATE TABLE data_mesh_plt.control_port_types (
    id INT PRIMARY KEY,
    name VARCHAR(45) NOT NULL,
    action_url VARCHAR(45) NOT NULL,
    created_at TIMESTAMP NOT NULL
);

-- CONTROL PORTS
-- Remove automaticamente se product for deletado
CREATE TABLE data_mesh_plt.control_ports (
    id INT PRIMARY KEY,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    data_sources_id INT NOT NULL,
    data_products_id INT NOT NULL,
    CONSTRAINT fk_control_ports_data_sources
        FOREIGN KEY (data_sources_id)
        REFERENCES data_mesh_plt.control_port_types(id)
        ON DELETE RESTRICT,
    CONSTRAINT fk_control_ports_data_products
        FOREIGN KEY (data_products_id)
        REFERENCES data_mesh_plt.data_products(id)
        ON DELETE CASCADE
);

-- DATA PORTS TYPE
CREATE TABLE data_mesh_plt.data_ports_type (
    id INT PRIMARY KEY,
    type VARCHAR(45) NOT NULL,
    connection_ref VARCHAR(100) NOT NULL,
    schema_ref VARCHAR(100) NOT NULL,
    created_at TIMESTAMP NOT NULL
);

-- DATA PORTS
CREATE TABLE data_mesh_plt.data_ports (
    id INT PRIMARY KEY,
    port_role VARCHAR(45) NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    data_ports_type_id INT NOT NULL,
    CONSTRAINT fk_data_ports_type
        FOREIGN KEY (data_ports_type_id)
        REFERENCES data_mesh_plt.data_ports_type(id)
        ON DELETE RESTRICT
);

-- PRODUCT PORT BINDING
-- Remove binding se product for deletado
-- Bloqueia delete de data_port se estiver vinculado
CREATE TABLE data_mesh_plt.product_port_binding (
    data_products_id INT NOT NULL,
    data_ports_id INT NOT NULL,
    status VARCHAR(45) NOT NULL,
    PRIMARY KEY (data_products_id, data_ports_id),
    CONSTRAINT fk_binding_product
        FOREIGN KEY (data_products_id)
        REFERENCES data_mesh_plt.data_products(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_binding_port
        FOREIGN KEY (data_ports_id)
        REFERENCES data_mesh_plt.data_ports(id)
        ON DELETE RESTRICT
);

-- PRINCIPALS
CREATE TABLE data_mesh_plt.principals (
    id INT PRIMARY KEY,
    name VARCHAR(45) NOT NULL,
    type VARCHAR(45) NOT NULL
);

-- ACCESS GRANT
-- Remove automaticamente se principal for deletado
CREATE TABLE data_mesh_plt.access_grant (
    id INT PRIMARY KEY,
    resource_type VARCHAR(45) NOT NULL,
    resource_id VARCHAR(45) NOT NULL,
    principals_id INT NOT NULL,
    permission VARCHAR(45) NOT NULL,
    granted_at TIMESTAMP NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    status VARCHAR(45) NOT NULL,
    CONSTRAINT fk_access_grant_principal
        FOREIGN KEY (principals_id)
        REFERENCES data_mesh_plt.principals(id)
        ON DELETE CASCADE
);

-- PRINCIPAL MEMBERSHIPS
-- Remove automaticamente se user ou principal for deletado
CREATE TABLE data_mesh_plt.principal_memberships (
    users_id INT NOT NULL,
    principals_id INT NOT NULL,
    PRIMARY KEY (users_id, principals_id),
    CONSTRAINT fk_membership_user
        FOREIGN KEY (users_id)
        REFERENCES data_mesh_plt.users(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_membership_principal
        FOREIGN KEY (principals_id)
        REFERENCES data_mesh_plt.principals(id)
        ON DELETE CASCADE
);
