resource "azurerm_application_insights" "pqe_application_insights" {
  name                = "${local.prefix}-app-insights"
  location            = azurerm_resource_group.mqe.location
  resource_group_name = azurerm_resource_group.mqe.name
  application_type    = "web"
}