data "azurerm_key_vault" "deploy_secrets" {
  name                = var.pc_test_resources_kv
  resource_group_name = var.pc_test_resources_rg
}

# Postgres

data "azurerm_key_vault_secret" "db_admin_password" {
  name         = var.pg_password_secret_name
  key_vault_id = data.azurerm_key_vault.deploy_secrets.id
}

# Cosmos DB

data "azurerm_key_vault_secret" "cosmos_key" {
  name         = "${local.deploy_secrets_prefix}--cosmos-key"
  key_vault_id = data.azurerm_key_vault.deploy_secrets.id
}

# SAS delegation service principal

data "azurerm_key_vault_secret" "sas_tenant_id" {
  name         = "sas-delegation-sp-tenant-id"
  key_vault_id = data.azurerm_key_vault.deploy_secrets.id
}

data "azurerm_key_vault_secret" "sas_client_id" {
  name         = "sas-delegation-sp-client-id"
  key_vault_id = data.azurerm_key_vault.deploy_secrets.id
}

data "azurerm_key_vault_secret" "sas_client_secret" {
  name         = "sas-delegation-sp-client-secret"
  key_vault_id = data.azurerm_key_vault.deploy_secrets.id
}
