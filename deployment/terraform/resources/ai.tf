resource "azurerm_application_insights" "pc_application_insights" {
  name                = "${local.prefix}-app-insights"
  location            = azurerm_resource_group.pc.location
  resource_group_name = azurerm_resource_group.pc.name
  application_type    = "web"

  lifecycle {
    ignore_changes = [
      workspace_id
    ]
  }
}