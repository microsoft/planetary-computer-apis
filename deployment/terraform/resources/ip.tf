## -- TODO: Delete these two IPs
#       They are attached to ingress controllers
#       and so can't be deleted from terraform
#       until those ingress controllers are
#       manually uninstalled.

resource "azurerm_public_ip" "mqe" {
  name                = "${local.prefix}-mqe-ip"
  domain_name_label   = "pct-mqe-${var.environment}"
  resource_group_name = azurerm_kubernetes_cluster.mqe.node_resource_group
  location            = azurerm_resource_group.mqe.location
  allocation_method   = "Static"
  sku                 = "Standard"

  tags = {
    environment = var.environment
  }
}

resource "azurerm_public_ip" "dqe" {
  name                = "${local.prefix}-dqe-ip"
  domain_name_label   = "pct-dqe-${var.environment}"
  resource_group_name = azurerm_kubernetes_cluster.mqe.node_resource_group
  location            = azurerm_resource_group.mqe.location
  allocation_method   = "Static"
  sku                 = "Standard"

  tags = {
    environment = var.environment
  }
}
## ---

resource "azurerm_public_ip" "pqe" {
  name                = "${local.prefix}-pqe-ip"
  domain_name_label   = "pct-pqe-${var.environment}"
  resource_group_name = azurerm_kubernetes_cluster.mqe.node_resource_group
  location            = azurerm_resource_group.mqe.location
  allocation_method   = "Static"
  sku                 = "Standard"

  tags = {
    environment = var.environment
  }
}