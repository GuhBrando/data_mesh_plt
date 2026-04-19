# =============================================================
# Catalog Schema — Data Product Catalog
# Stores data contracts (as flexible JSONB) and data products
# that reference those contracts.
# =============================================================

schema "catalog" {}

table "data_contracts" {
  schema = schema.catalog

  column "id" {
    type    = uuid
    null    = false
    default = sql("gen_random_uuid()")
  }

  column "obj" {
    type = jsonb
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
