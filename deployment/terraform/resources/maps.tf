resource "azurerm_maps_account" "azmaps" {
  name                = "azmaps-${local.prefix}"
  resource_group_name = azurerm_resource_group.pc.name
  sku_name            = "G2"
}
