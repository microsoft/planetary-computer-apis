resource "azurerm_public_ip" "pqe" {
  name                = "${local.prefix}-pqe-ip"
  domain_name_label   = "pct-pqe-${var.environment}"
  resource_group_name = azurerm_kubernetes_cluster.pqe.node_resource_group
  location            = azurerm_resource_group.pqe.location
  allocation_method   = "Static"
  sku                 = "Standard"

  tags = {
    environment = var.environment
  }
}