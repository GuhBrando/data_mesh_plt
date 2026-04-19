# =============================================================
# IAM Schema — Identity & Access Management
# Manages users, principals (users/groups/services),
# and their memberships.
# =============================================================

schema "iam" {}

enum "principal_type" {
  schema = schema.iam
  values = ["USER", "GROUP", "SERVICE"]
}

table "users" {
  schema = schema.iam

  column "id" {
    type    = uuid
    null    = false
    default = sql("gen_random_uuid()")
  }

  column "name" {
    type = text
    null = false
  }

  column "email" {
    type = text
    null = false
  }

  column "created_at" {
    type    = timestamptz
    null    = false
    default = sql("now()")
  }

  primary_key {
    columns = [column.id]
  }

  unique "users_email_key" {
    columns = [column.email]
  }
}

table "principals" {
  schema = schema.iam

  column "id" {
    type    = uuid
    null    = false
    default = sql("gen_random_uuid()")
  }

  column "name" {
    type = text
    null = false
  }

  column "type" {
    type = enum.principal_type
    null = false
  }

  column "created_at" {
    type    = timestamptz
    null    = false
    default = sql("now()")
  }

  primary_key {
    columns = [column.id]
  }
}

table "principal_memberships" {
  schema = schema.iam

  column "users_id" {
    type = uuid
    null = false
  }

  column "principals_id" {
    type = uuid
    null = false
  }

  primary_key {
    columns = [column.users_id, column.principals_id]
  }

  foreign_key "principal_memberships_users_id_fkey" {
    columns     = [column.users_id]
    ref_columns = [table.users.column.id]
    on_update   = NO_ACTION
    on_delete   = CASCADE
  }

  foreign_key "principal_memberships_principals_id_fkey" {
    columns     = [column.principals_id]
    ref_columns = [table.principals.column.id]
    on_update   = NO_ACTION
    on_delete   = CASCADE
  }

  index "idx_membership_principal" {
    columns = [column.principals_id]
  }
}
