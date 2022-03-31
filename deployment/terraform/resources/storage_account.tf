resource "azurerm_storage_account" "pc" {
  name                     = "${local.nodash_prefix}sa"
  resource_group_name      = azurerm_resource_group.pc.name
  location                 = azurerm_resource_group.pc.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
}

# Tables

resource "azurerm_storage_table" "collectionconfig" {
  name                 = "collectionconfig"
  storage_account_name = azurerm_storage_account.pc.name
}

resource "azurerm_storage_table" "containerconfig" {
  name                 = "containerconfig"
  storage_account_name = azurerm_storage_account.pc.name
}

resource "azurerm_storage_table" "ipexceptionlist" {
  name                 = "ipexceptionlist"
  storage_account_name = azurerm_storage_account.pc.name
}