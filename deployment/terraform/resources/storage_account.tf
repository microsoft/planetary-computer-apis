resource "azurerm_storage_account" "pc" {
  name                            = "${local.nodash_prefix}sa"
  resource_group_name             = azurerm_resource_group.pc.name
  location                        = azurerm_resource_group.pc.location
  account_tier                    = "Standard"
  account_replication_type        = "LRS"
  min_tls_version                 = "TLS1_2"
  allow_nested_items_to_be_public = false
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

resource "azurerm_storage_table" "blobstoragebannedip" {
  name                 = "blobstoragebannedip"
  storage_account_name = azurerm_storage_account.pc.name
}