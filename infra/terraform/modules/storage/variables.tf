variable "resource_group_name" { type = string }
variable "location" { type = string }
variable "tags" { type = map(string) }
variable "containers" {
  type        = list(string)
  description = "Container names, one per catalog (dev/pre/pro)."
}
