resource "azurerm_resource_group" "mqe" {
  name     = "${local.prefix}_rg"
  location = var.region
}