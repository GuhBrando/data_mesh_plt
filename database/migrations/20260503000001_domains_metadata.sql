-- Add domain metadata columns to iam.principals
ALTER TABLE iam.principals
    ADD COLUMN IF NOT EXISTS description TEXT NOT NULL DEFAULT '',
    ADD COLUMN IF NOT EXISTS owner_id UUID REFERENCES iam.users(id) ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT now();

-- Add role to memberships (member or maintainer)
ALTER TABLE iam.principal_memberships
    ADD COLUMN IF NOT EXISTS role TEXT NOT NULL DEFAULT 'member';

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'pm_role_check'
          AND conrelid = 'iam.principal_memberships'::regclass
    ) THEN
        ALTER TABLE iam.principal_memberships
            ADD CONSTRAINT pm_role_check CHECK (role IN ('maintainer', 'member'));
    END IF;
END $$;

-- Rollback:
-- ALTER TABLE iam.principal_memberships DROP CONSTRAINT pm_role_check, DROP COLUMN role;
-- ALTER TABLE iam.principals DROP COLUMN description, DROP COLUMN owner_id, DROP COLUMN updated_at;
