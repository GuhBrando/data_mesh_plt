-- =============================================================================
-- Add nullable repo_url column to catalog.data_products to store the URL of the
-- dedicated GitHub repository provisioned for each data product. Nullable so
-- existing rows are valid and so warn-only provisioning failures leave the row
-- in a recoverable state (the lazy-backfill path will fill it on next access).
-- =============================================================================

ALTER TABLE catalog.data_products
    ADD COLUMN repo_url TEXT;
