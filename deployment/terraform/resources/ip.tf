resource "azurerm_public_ip" "pc" {
  name                = "${local.prefix}-pc-ip"
  domain_name_label   = "pct-apis-${var.environment}1" # TODO: revert "1" from name
  resource_group_name = azurerm_kubernetes_cluster.pc.node_resource_group
  location            = azurerm_resource_group.pc.location
  allocation_method   = "Static"
  sku                 = "Standard"

  tags = {
    environment = var.environment
  }

  lifecycle {
    ignore_changes = [
      # Ignore changes to tags, e.g. because a management agent
      # updates these based on some ruleset managed elsewhere.
      tags,
    ]
  }
}