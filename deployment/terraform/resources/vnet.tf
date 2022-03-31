resource "azurerm_virtual_network" "pc" {
  name                = "${local.prefix}-network"
  location            = azurerm_resource_group.pc.location
  resource_group_name = azurerm_resource_group.pc.name
  address_space       = ["10.0.0.0/8"]
}

resource "azurerm_subnet" "node_subnet" {
  name                 = "${local.prefix}-node-subnet"
  virtual_network_name = azurerm_virtual_network.pc.name
  resource_group_name  = azurerm_resource_group.pc.name
  address_prefixes     = ["10.1.0.0/16"]
  service_endpoints = [
    "Microsoft.Sql",
    "Microsoft.Storage",
    "Microsoft.KeyVault",
    "Microsoft.ContainerRegistry",
  ]
}

resource "azurerm_subnet" "cache_subnet" {
  name                 = "${local.prefix}-cache-subnet"
  virtual_network_name = azurerm_virtual_network.pc.name
  resource_group_name  = azurerm_resource_group.pc.name
  address_prefixes     = ["10.2.0.0/16"]
  service_endpoints = []
}

resource "azurerm_network_security_group" "pc" {
  name                = "${local.prefix}-security-group"
  location            = azurerm_resource_group.pc.location
  resource_group_name = azurerm_resource_group.pc.name

  security_rule {
    name                       = "nsg-rule"
    priority                   = 100
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "*"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }
}

resource "azurerm_subnet_network_security_group_association" "pc" {
  subnet_id                 = azurerm_subnet.node_subnet.id
  network_security_group_id = azurerm_network_security_group.pc.id
}

resource "azurerm_subnet_network_security_group_association" "pc-cache" {
  subnet_id                 = azurerm_subnet.cache_subnet.id
  network_security_group_id = azurerm_network_security_group.pc.id
}