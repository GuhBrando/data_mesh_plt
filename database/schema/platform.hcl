# =============================================================
# Platform Schema — Data & Control Ports
# Manages control port types/instances and data ports
# (input/output/internal), binding them to data products.
# =============================================================

schema "platform" {}

enum "port_role_type" {
  schema = schema.platform
  values = ["INPUT", "OUTPUT", "INTERNAL"]
}

enum "binding_status" {
  schema = schema.platform
  values = ["ACTIVE", "DISABLED"]
}

table "control_port_types" {
  schema = schema.platform

  column "id" {
    type    = uuid
    null    = false
    default = sql("gen_random_uuid()")
  }

  column "name" {
    type = text
    null = false
  }

  column "action_url" {
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

  unique "control_port_types_name_key" {
    columns = [column.name]
  }
}

table "control_ports" {
  schema = schema.platform

  column "id" {
    type    = uuid
    null    = false
    default = sql("gen_random_uuid()")
  }

  column "control_port_type_id" {
    type = uuid
    null = false
  }

  column "data_products_id" {
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

  foreign_key "control_ports_control_port_type_id_fkey" {
    columns     = [column.control_port_type_id]
    ref_columns = [table.control_port_types.column.id]
    on_update   = NO_ACTION
    on_delete   = RESTRICT
  }

  foreign_key "control_ports_data_products_id_fkey" {
    columns     = [column.data_products_id]
    ref_columns = [table.catalog_data_products.column.id]
    on_update   = NO_ACTION
    on_delete   = CASCADE
  }

  index "idx_control_ports_product" {
    columns = [column.data_products_id]
  }
}

table "data_ports_type" {
  schema = schema.platform

  column "id" {
    type    = uuid
    null    = false
    default = sql("gen_random_uuid()")
  }

  column "type" {
    type = text
    null = false
  }

  column "connection_ref" {
    type = text
    null = false
  }

  column "schema_ref" {
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
}

table "data_ports" {
  schema = schema.platform

  column "id" {
    type    = uuid
    null    = false
    default = sql("gen_random_uuid()")
  }

  column "port_role" {
    type = enum.port_role_type
    null = false
  }

  column "data_ports_type_id" {
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

  foreign_key "data_ports_data_ports_type_id_fkey" {
    columns     = [column.data_ports_type_id]
    ref_columns = [table.data_ports_type.column.id]
    on_update   = NO_ACTION
    on_delete   = RESTRICT
  }

  index "idx_data_ports_type" {
    columns = [column.data_ports_type_id]
  }
}

table "product_port_binding" {
  schema = schema.platform

  column "data_products_id" {
    type = uuid
    null = false
  }

  column "data_ports_id" {
    type = uuid
    null = false
  }

  column "status" {
    type = enum.binding_status
    null = false
  }

  primary_key {
    columns = [column.data_products_id, column.data_ports_id]
  }

  foreign_key "product_port_binding_data_products_id_fkey" {
    columns     = [column.data_products_id]
    ref_columns = [table.catalog_data_products.column.id]
    on_update   = NO_ACTION
    on_delete   = CASCADE
  }

  foreign_key "product_port_binding_data_ports_id_fkey" {
    columns     = [column.data_ports_id]
    ref_columns = [table.data_ports.column.id]
    on_update   = NO_ACTION
    on_delete   = RESTRICT
  }

  index "idx_binding_port" {
    columns = [column.data_ports_id]
  }
}
