data "azurerm_key_vault" "deploy_secrets" {
  name                = var.pc_test_resources_kv
  resource_group_name = var.pc_test_resources_rg
}

data "azurerm_key_vault_secret" "db_admin_password" {
  name         = var.pg_password_secret_name
  key_vault_id = data.azurerm_key_vault.deploy_secrets.id
}

data "azurerm_key_vault_secret" "pc_sdk_subscription_key" {
  name         = var.pc_sdk_subscription_key_secret_name
  key_vault_id = data.azurerm_key_vault.deploy_secrets.id
}
