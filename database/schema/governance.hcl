# =============================================================
# Governance Schema — Access Control & Permissions
# Tracks access grants given to principals over resources
# (data products, contracts, and ports), with expiry support.
# =============================================================

schema "governance" {}

enum "resource_type" {
  schema = schema.governance
  values = ["DATA_PRODUCT", "DATA_CONTRACT", "DATA_PORT"]
}

enum "permission_type" {
  schema = schema.governance
  values = ["READ", "WRITE", "ADMIN"]
}

enum "grant_status" {
  schema = schema.governance
  values = ["ACTIVE", "REVOKED", "EXPIRED"]
}

table "access_grant" {
  schema = schema.governance

  column "id" {
    type    = uuid
    null    = false
    default = sql("gen_random_uuid()")
  }

  column "resource_type" {
    type = enum.resource_type
    null = false
  }

  column "resource_id" {
    type = uuid
    null = false
  }

  column "principals_id" {
    type = uuid
    null = false
  }

  column "permission" {
    type = enum.permission_type
    null = false
  }

  column "status" {
    type = enum.grant_status
    null = false
  }

  column "granted_at" {
    type    = timestamptz
    null    = false
    default = sql("now()")
  }

  column "expires_at" {
    type = timestamptz
    null = true
  }

  column "created_at" {
    type    = timestamptz
    null    = false
    default = sql("now()")
  }

  primary_key {
    columns = [column.id]
  }

  foreign_key "access_grant_principals_id_fkey" {
    columns     = [column.principals_id]
    ref_columns = [table.iam_principals.column.id]
    on_update   = NO_ACTION
    on_delete   = CASCADE
  }

  check "access_grant_check" {
    expr = "(expires_at IS NULL OR expires_at > granted_at)"
  }

  index "idx_access_grant_principal" {
    columns = [column.principals_id]
  }

  index "idx_access_grant_resource" {
    columns = [column.resource_type, column.resource_id]
  }
}
