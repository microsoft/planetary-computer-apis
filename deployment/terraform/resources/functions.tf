resource "azurerm_service_plan" "pc" {
  name                = "app-plan-${local.prefix}"
  location            = azurerm_resource_group.pc.location
  resource_group_name = azurerm_resource_group.pc.name
  os_type             = "Linux"

  sku_name = "EP1"

}

resource "azurerm_linux_function_app" "pcfuncs" {
  name                 = "func-${local.prefix}"
  location             = azurerm_resource_group.pc.location
  resource_group_name  = azurerm_resource_group.pc.name
  service_plan_id      = azurerm_service_plan.pc.id
  storage_account_name = azurerm_storage_account.pc.name

  virtual_network_subnet_id = azurerm_subnet.function_subnet.id

  ftp_publish_basic_authentication_enabled       = false
  webdeploy_publish_basic_authentication_enabled = false


  storage_uses_managed_identity = true
  https_only                    = true

  identity {
    type = "SystemAssigned"
  }

  app_settings = {
    "FUNCTIONS_WORKER_RUNTIME" = "python",
    "APP_INSIGHTS_IKEY"        = azurerm_application_insights.pc_application_insights.instrumentation_key,

    # Remote build
    "BUILD_FLAGS"                    = "UseExpressBuild",
    "ENABLE_ORYX_BUILD"              = "true"
    "SCM_DO_BUILD_DURING_DEPLOYMENT" = "1",
    "XDG_CACHE_HOME"                 = "/tmp/.cache"
    "AzureWebJobsDisableHomepage"    = true,

    # Animation Function
    "ANIMATION_OUTPUT_STORAGE_URL"       = var.animation_output_storage_url,
    "ANIMATION_API_ROOT_URL"             = var.funcs_data_api_url,
    "ANIMATION_TILE_REQUEST_CONCURRENCY" = tostring(var.funcs_tile_request_concurrency),

    # Image Function
    "IMAGE_OUTPUT_STORAGE_URL"       = var.image_output_storage_url,
    "IMAGE_API_ROOT_URL"             = var.funcs_data_api_url,
    "IMAGE_TILE_REQUEST_CONCURRENCY" = tostring(var.funcs_tile_request_concurrency),

    # IPBan function
    "STORAGE_ACCOUNT_URL"        = var.func_storage_account_url,
    "BANNED_IP_TABLE"            = var.banned_ip_table,
    "LOG_ANALYTICS_WORKSPACE_ID" = var.prod_log_analytics_workspace_id,
  }

  site_config {
    vnet_route_all_enabled   = true
    application_insights_key = azurerm_application_insights.pc_application_insights.instrumentation_key
    ftps_state               = "Disabled"

    cors {
      allowed_origins = ["*"]
    }
    application_stack {
      python_version = "3.9"
    }
  }
  lifecycle {
    ignore_changes = [
      tags
    ]
  }
}



resource "azurerm_role_assignment" "function-app-storage-account-access" {
  scope                = azurerm_storage_account.pc.id
  role_definition_name = "Storage Blob Data Owner"
  principal_id         = azurerm_linux_function_app.pcfuncs.identity[0].principal_id
}

resource "azurerm_role_assignment" "function-app-animation-container-access" {
  scope                = data.azurerm_storage_account.output-storage-account.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = azurerm_linux_function_app.pcfuncs.identity[0].principal_id

  depends_on = [
    azurerm_linux_function_app.pcfuncs
  ]
}

resource "azurerm_role_assignment" "function-app-storage-table-data-contributor" {
  scope                = azurerm_storage_account.pc.id
  role_definition_name = "Storage Table Data Contributor"
  principal_id         = azurerm_linux_function_app.pcfuncs.identity[0].principal_id

  depends_on = [
    azurerm_linux_function_app.pcfuncs
  ]
}

data "azurerm_log_analytics_workspace" "prod_log_analytics_workspace" {
  provider            = azurerm.planetary_computer_subscription
  name                = var.prod_log_analytics_workspace_name
  resource_group_name = var.pc_resources_rg
}

resource "azurerm_role_assignment" "function-app-log-analytics-access" {
  scope                = data.azurerm_log_analytics_workspace.prod_log_analytics_workspace.id
  role_definition_name = "Log Analytics Reader"
  principal_id         = azurerm_linux_function_app.pcfuncs.identity[0].principal_id

  depends_on = [
    azurerm_linux_function_app.pcfuncs
  ]
}
