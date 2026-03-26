# 1. Definição das variáveis (buscando do ENV do Docker/Sistema)
variable "admin_password" {
  type    = string
  default = getenv("ADMIN_PASSWORD")
}

variable "app_user_password" {
  type    = string
  default = getenv("APP_USER_PASSWORD")
}

variable "readonly_password" {
  type    = string
  default = getenv("USER_PASSWORD")
}

# 2. Transforma a pasta migrations em um Template
data "template_dir" "migrations" {
  path = "migrations"
  vars = {
    admin_password    = var.admin_password
    app_user_password = var.app_user_password
    readonly_password = var.readonly_password
  }
}

# 3. Configuração do ambiente
env "local" {
  url = "postgres://postgres:${getenv("POSTGRES_PASSWORD")}@postgres_db:5432/data_mesh_plt?sslmode=disable"
  
  migration {
    dir = data.template_dir.migrations.url
  }
}