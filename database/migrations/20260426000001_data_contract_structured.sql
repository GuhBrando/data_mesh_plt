-- Existing contracts are dev data; clear them before changing the schema.
TRUNCATE catalog.data_products CASCADE;
TRUNCATE catalog.data_contracts CASCADE;

-- Remove the generic blob column.
ALTER TABLE catalog.data_contracts DROP COLUMN obj;

-- Add structured metadata columns.
ALTER TABLE catalog.data_contracts
    ADD COLUMN title         TEXT    NOT NULL DEFAULT '',
    ADD COLUMN version       TEXT    NOT NULL DEFAULT '1.0.0',
    ADD COLUMN owner         TEXT    NOT NULL DEFAULT '',
    ADD COLUMN domain        TEXT    NOT NULL DEFAULT '',
    ADD COLUMN tier          INT     NOT NULL DEFAULT 4
                             CONSTRAINT chk_dc_tier
                             CHECK (tier BETWEEN 1 AND 4),
    ADD COLUMN status        TEXT    NOT NULL DEFAULT 'draft'
                             CONSTRAINT chk_dc_status
                             CHECK (status IN ('draft','in_review','active','deprecated')),
    ADD COLUMN models        JSONB   NOT NULL DEFAULT '{"fields":[]}',
    ADD COLUMN servicelevels JSONB   NOT NULL DEFAULT '{"freshness":"","availability":"","retention":"","latency":""}';
