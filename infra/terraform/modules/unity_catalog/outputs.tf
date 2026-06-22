output "catalog_names" {
  value = { for k, c in databricks_catalog.this : k => c.name }
}
output "metastore_id" { value = databricks_metastore.this.id }
