resource "azurerm_storage_account" "pc" {
  name                            = "${local.nodash_prefix}sa"
  resource_group_name             = azurerm_resource_group.pc.name
  location                        = azurerm_resource_group.pc.location
  account_tier                    = "Standard"
  account_replication_type        = "LRS"
  min_tls_version                 = "TLS1_2"
  allow_nested_items_to_be_public = false

  network_rules {
    default_action             = "Deny"
    virtual_network_subnet_ids = [azurerm_subnet.node_subnet.id, azurerm_subnet.function_subnet.id, data.azurerm_subnet.sas_node_subnet.id]
  }

  # Disabling shared access keys breaks terraform's ability to do subsequent
  # resource fetching during terraform plan. As a result, this property is
  # ignored and managed outside of this apply session, via the deploy script.
  # https://github.com/hashicorp/terraform-provider-azurerm/issues/25218

  # shared_access_key_enabled = false
  lifecycle {
    ignore_changes = [
      shared_access_key_enabled,
    ]
  }
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

# Output storage account for function app, "pcfilestest"
data "azurerm_storage_account" "output-storage-account" {
  name                = var.output_storage_account_name
  resource_group_name = var.pc_test_resources_rg

}

resource "azurerm_storage_account_network_rules" "pcfunc-vnet-access" {
  storage_account_id = data.azurerm_storage_account.output-storage-account.id

  default_action             = "Deny"
  virtual_network_subnet_ids = [azurerm_subnet.function_subnet.id]
}
