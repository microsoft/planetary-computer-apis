resource "azurerm_app_service_plan" "pc" {
  name                = "plan-${local.prefix}"
  location            = azurerm_resource_group.pc.location
  resource_group_name = azurerm_resource_group.pc.name
  kind                = "functionapp"
  reserved            = true

  sku {
    tier = "Dynamic"
    size = "Y1"
  }
}

resource "azurerm_linux_function_app" "pcfuncs" {
  name                          = "func-${local.prefix}"
  location                      = azurerm_resource_group.pc.location
  resource_group_name           = azurerm_resource_group.pc.name
  service_plan_id               = azurerm_app_service_plan.pc.id
  storage_account_name          = azurerm_storage_account.pc.name
  storage_uses_managed_identity = true
  https_only                    = true

  identity {
    type = "SystemAssigned"
  }

  app_settings = {
    "ENABLE_ORYX_BUILD"              = "true",
    "SCM_DO_BUILD_DURING_DEPLOYMENT" = "true",
    "FUNCTIONS_WORKER_RUNTIME"       = "python",
    "APP_INSIGHTS_IKEY"              = azurerm_application_insights.pc_application_insights.instrumentation_key,
    "APPINSIGHTS_INSTRUMENTATIONKEY" = azurerm_application_insights.pc_application_insights.instrumentation_key,
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

# Note: this must be in the same subscription as the rest of the deployed infrastructure
data "azurerm_storage_container" "output" {
  name                 = var.output_container_name
  storage_account_name = var.output_storage_account_name
}

resource "azurerm_role_assignment" "function-app-storage-account-access" {
  scope                = azurerm_storage_account.pc.id
  role_definition_name = "Storage Blob Data Owner"
  principal_id         = azurerm_linux_function_app.pcfuncs.identity[0].principal_id
}

resource "azurerm_role_assignment" "function-app-animation-container-access" {
  scope                = data.azurerm_storage_container.output.resource_manager_id
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