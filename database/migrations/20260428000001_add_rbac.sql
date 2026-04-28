-- Add platform role to users (defaults every existing and future user to DATA_CONSUMER)
ALTER TABLE iam.users
    ADD COLUMN role TEXT NOT NULL DEFAULT 'DATA_CONSUMER'
    CHECK (role IN ('PLATFORM_ADMIN', 'DATA_OWNER', 'DATA_STEWARD', 'DATA_CONSUMER'));

-- Associate contracts with a domain (nullable so existing contracts don't break)
ALTER TABLE catalog.data_contracts
    ADD COLUMN domain_id UUID REFERENCES iam.principals(id) ON DELETE RESTRICT;

-- Stakeholders assigned to a specific contract by a Steward
CREATE TABLE catalog.contract_stakeholders (
    contract_id UUID NOT NULL REFERENCES catalog.data_contracts(id) ON DELETE CASCADE,
    user_id     UUID NOT NULL REFERENCES iam.users(id) ON DELETE CASCADE,
    assigned_by UUID REFERENCES iam.users(id) ON DELETE SET NULL,
    assigned_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (contract_id, user_id)
);

-- Create indexes for better query performance
CREATE INDEX idx_contract_stakeholders_user_id ON catalog.contract_stakeholders(user_id);
CREATE INDEX idx_contract_stakeholders_assigned_by ON catalog.contract_stakeholders(assigned_by);
CREATE INDEX idx_data_contracts_domain_id ON catalog.data_contracts(domain_id);

-- Grant permissions to app_user
GRANT SELECT, INSERT, UPDATE, DELETE ON iam.users TO app_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON catalog.data_contracts TO app_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON catalog.contract_stakeholders TO app_user;

-- Rollback:
-- DROP TABLE catalog.contract_stakeholders;
-- DROP INDEX idx_data_contracts_domain_id;
-- ALTER TABLE catalog.data_contracts DROP COLUMN domain_id;
-- ALTER TABLE iam.users DROP COLUMN role;
-- REVOKE SELECT, INSERT, UPDATE, DELETE ON iam.users FROM app_user;
-- REVOKE SELECT, INSERT, UPDATE, DELETE ON catalog.data_contracts FROM app_user;
-- REVOKE SELECT, INSERT, UPDATE, DELETE ON catalog.contract_stakeholders FROM app_user;
