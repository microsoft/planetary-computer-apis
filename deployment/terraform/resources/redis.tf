resource "azurerm_redis_cache" "pc" {
  name                = "${local.prefix}-cache"
  location            = azurerm_resource_group.pc.location
  resource_group_name = azurerm_resource_group.pc.name
  capacity            = 1
  family              = "P"
  sku_name            = "Premium"
  enable_non_ssl_port = false
  minimum_tls_version = "1.2"

  subnet_id = azurerm_subnet.cache_subnet.id

  redis_configuration {
  }
}