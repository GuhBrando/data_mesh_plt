# =============================================================
# Catalog Schema — Data Product Catalog
# =============================================================

schema "catalog" {}

table "data_contracts" {
  schema = schema.catalog

  column "id" {
    type    = uuid
    null    = false
    default = sql("gen_random_uuid()")
  }

  column "title" {
    type    = text
    null    = false
    default = ""
  }

  column "version" {
    type    = text
    null    = false
    default = "1.0.0"
  }

  column "owner" {
    type    = text
    null    = false
    default = ""
  }

  column "domain" {
    type    = text
    null    = false
    default = ""
  }

  column "tier" {
    type    = int
    null    = false
    default = 4
  }

  column "status" {
    type    = text
    null    = false
    default = "draft"
  }

  column "models" {
    type    = jsonb
    null    = false
    default = sql(`'{"fields":[]}'::jsonb`)
  }

  column "servicelevels" {
    type    = jsonb
    null    = false
    default = sql(`'{"freshness":"","availability":"","retention":"","latency":""}'::jsonb`)
  }

  column "created_at" {
    type    = timestamptz
    null    = false
    default = sql("now()")
  }

  column "updated_at" {
    type    = timestamptz
    null    = false
    default = sql("now()")
  }

  primary_key {
    columns = [column.id]
  }

  check "chk_dc_tier" {
    expr = "tier BETWEEN 1 AND 4"
  }

  check "chk_dc_status" {
    expr = "status IN ('draft','in_review','active','deprecated')"
  }
}

table "data_products" {
  schema = schema.catalog

  column "id" {
    type    = uuid
    null    = false
    default = sql("gen_random_uuid()")
  }

  column "name" {
    type = text
    null = false
  }

  column "description" {
    type = text
    null = false
  }

  column "data_contracts_id" {
    type = uuid
    null = false
  }

  column "created_at" {
    type    = timestamptz
    null    = false
    default = sql("now()")
  }

  column "updated_at" {
    type    = timestamptz
    null    = false
    default = sql("now()")
  }

  primary_key {
    columns = [column.id]
  }

  foreign_key "data_products_data_contracts_id_fkey" {
    columns     = [column.data_contracts_id]
    ref_columns = [table.data_contracts.column.id]
    on_update   = CASCADE
    on_delete   = RESTRICT
  }

  index "idx_data_products_contract" {
    columns = [column.data_contracts_id]
  }
}
