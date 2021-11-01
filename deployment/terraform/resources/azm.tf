resource "azurerm_log_analytics_workspace" "pc_azm_workspace" {
  name                = "${local.prefix}-azm-ws"
  location            = azurerm_resource_group.pc.location
  resource_group_name = azurerm_resource_group.pc.name
  sku                 = "PerGB2018"
  retention_in_days   = 30
}