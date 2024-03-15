resource "azurerm_resource_group" "pc" {
  name     = "${local.prefix}_rg"
  location = var.region

  tags = {
    "ringValue" = "r0"
  }
}
