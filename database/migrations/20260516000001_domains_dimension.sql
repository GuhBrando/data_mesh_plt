-- =============================================================================
-- Introduce catalog.domains + catalog.domain_members as a proper star-schema
-- dimension table, replacing the iam.principals(type='GROUP') overload.
-- data_contracts.domain_id FK is re-pointed here; the denormalized `domain`
-- TEXT column is dropped (name is now always obtained by JOIN).
-- iam.principals GROUP rows are preserved (governance FK cascades off them).
-- Atlas manages the transaction; do NOT add explicit BEGIN/COMMIT here.
-- =============================================================================

-- 1. Dimension table
CREATE TABLE catalog.domains (
    id          UUID        NOT NULL DEFAULT gen_random_uuid(),
    name        TEXT        NOT NULL,
    description TEXT        NOT NULL DEFAULT '',
    owner_id    UUID        REFERENCES iam.users(id) ON DELETE SET NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT domains_pkey PRIMARY KEY (id),
    CONSTRAINT domains_name_key UNIQUE (name)
);

-- 2. Membership table
CREATE TABLE catalog.domain_members (
    domain_id UUID NOT NULL REFERENCES catalog.domains(id) ON DELETE CASCADE,
    user_id   UUID NOT NULL REFERENCES iam.users(id)    ON DELETE CASCADE,
    role      TEXT NOT NULL DEFAULT 'member'
              CONSTRAINT chk_domain_member_role CHECK (role IN ('maintainer', 'member')),
    CONSTRAINT domain_members_pkey PRIMARY KEY (domain_id, user_id)
);
CREATE INDEX idx_domain_members_user ON catalog.domain_members(user_id);

-- 3. Migrate domains from iam.principals, preserving UUIDs so that existing
--    data_contracts.domain_id values remain valid after the FK is re-pointed.
INSERT INTO catalog.domains (id, name, description, owner_id, created_at, updated_at)
SELECT p.id,
       p.name,
       COALESCE(p.description, ''),
       p.owner_id,
       p.created_at,
       COALESCE(p.updated_at, p.created_at)
FROM iam.principals p
WHERE p.type = 'GROUP'
ON CONFLICT (id) DO NOTHING;

-- 4. Migrate memberships (GROUP principals only)
INSERT INTO catalog.domain_members (domain_id, user_id, role)
SELECT pm.principals_id, pm.users_id, COALESCE(pm.role, 'member')
FROM iam.principal_memberships pm
JOIN iam.principals p ON p.id = pm.principals_id AND p.type = 'GROUP'
ON CONFLICT (domain_id, user_id) DO NOTHING;

-- 5. Drop the old FK (→ iam.principals) BEFORE backfilling domain_id so that
--    new catalog.domains UUIDs (not in iam.principals) pass validation.
--    Immediately re-add it pointing to catalog.domains ON DELETE RESTRICT.
DO $$
DECLARE c text;
BEGIN
    SELECT conname INTO c
    FROM pg_constraint
    WHERE conrelid  = 'catalog.data_contracts'::regclass
      AND contype   = 'f'
      AND confrelid = 'iam.principals'::regclass;
    IF c IS NOT NULL THEN
        EXECUTE format('ALTER TABLE catalog.data_contracts DROP CONSTRAINT %I', c);
    END IF;
END $$;

ALTER TABLE catalog.data_contracts
    ADD CONSTRAINT data_contracts_domain_id_fkey
    FOREIGN KEY (domain_id) REFERENCES catalog.domains(id) ON DELETE RESTRICT
    NOT VALID;   -- skip scanning existing NULLs; validated after backfill

-- 6. Create catalog.domains rows for any remaining distinct domain-name strings
--    in data_contracts that have no matching domain (e.g. contracts created via
--    GitHub sync that only have the text `domain` field set).
INSERT INTO catalog.domains (name)
SELECT DISTINCT dc.domain
FROM catalog.data_contracts dc
WHERE dc.domain_id IS NULL
  AND dc.domain <> ''
  AND NOT EXISTS (SELECT 1 FROM catalog.domains d WHERE d.name = dc.domain)
ON CONFLICT (name) DO NOTHING;

-- 7. Backfill domain_id for contracts linked only by the text `domain` column.
UPDATE catalog.data_contracts dc
SET domain_id = d.id
FROM catalog.domains d
WHERE dc.domain_id IS NULL AND dc.domain = d.name;

-- 8. Sentinel domain for any remaining NULL rows (empty `domain` text).
--    This ensures NOT NULL can be applied without data loss.
INSERT INTO catalog.domains (name)
SELECT 'unassigned'
WHERE EXISTS (SELECT 1 FROM catalog.data_contracts WHERE domain_id IS NULL)
ON CONFLICT (name) DO NOTHING;

UPDATE catalog.data_contracts
SET domain_id = (SELECT id FROM catalog.domains WHERE name = 'unassigned')
WHERE domain_id IS NULL;

-- Validate the FK now that all rows have a valid domain_id.
ALTER TABLE catalog.data_contracts
    VALIDATE CONSTRAINT data_contracts_domain_id_fkey;

-- 9. Enforce NOT NULL and drop the denormalized text column.
ALTER TABLE catalog.data_contracts ALTER COLUMN domain_id SET NOT NULL;
ALTER TABLE catalog.data_contracts DROP COLUMN domain;

-- 10. Grants
GRANT SELECT, INSERT, UPDATE, DELETE ON catalog.domains        TO app_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON catalog.domain_members TO app_user;

-- =============================================================================
-- ROLLBACK (run manually if needed):
-- ALTER TABLE catalog.data_contracts ADD COLUMN domain TEXT NOT NULL DEFAULT '';
-- UPDATE catalog.data_contracts dc SET domain = d.name FROM catalog.domains d WHERE dc.domain_id = d.id;
-- ALTER TABLE catalog.data_contracts ALTER COLUMN domain_id DROP NOT NULL;
-- ALTER TABLE catalog.data_contracts DROP CONSTRAINT data_contracts_domain_id_fkey;
-- ALTER TABLE catalog.data_contracts ADD CONSTRAINT data_contracts_domain_id_fkey
--     FOREIGN KEY (domain_id) REFERENCES iam.principals(id) ON DELETE RESTRICT;
-- DROP TABLE catalog.domain_members;
-- DROP TABLE catalog.domains;
-- =============================================================================
