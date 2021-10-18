resource "azurerm_virtual_network" "pqe" {
  name                = "${local.prefix}-network"
  location            = azurerm_resource_group.pqe.location
  resource_group_name = azurerm_resource_group.pqe.name
  address_space       = ["10.0.0.0/8"]
}

resource "azurerm_subnet" "node_subnet" {
  name                 = "${local.prefix}-node-subnet"
  virtual_network_name = azurerm_virtual_network.pqe.name
  resource_group_name  = azurerm_resource_group.pqe.name
  address_prefixes     = ["10.1.0.0/16"]
  service_endpoints = [
    "Microsoft.Sql",
    "Microsoft.Storage",
    "Microsoft.KeyVault",
    "Microsoft.ContainerRegistry",
  ]
}