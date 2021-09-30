resource "azurerm_api_management" "pqe_apim" {
  name                = "${local.pqe_stack_id}-${local.location}-${var.environment}-apim"
  location            = azurerm_resource_group.mqe.location
  resource_group_name = azurerm_resource_group.mqe.name
  publisher_name      = "Microsoft"
  publisher_email     = "planetarycomputer@microsoft.com"

  # Starting off with the Developer tier while we test things out,
  # but will likely want to move up one of: Basic, Standard, or Premium
  sku_name = "Developer_1"
}

resource "azurerm_api_management_api" "pqe_api" {
  description           = "Planetary Query API"
  display_name          = "Planetary Query API"
  name                  = "planetary-query-api"
  protocols             = ["https"]
  api_management_name   = azurerm_api_management.pqe_apim.name
  resource_group_name   = azurerm_resource_group.mqe.name
  revision              = "1"
  path                  = ""
  subscription_required = false
}


resource "azurerm_api_management_backend" "pqe" {
  name                = "pqe-backend"
  resource_group_name = azurerm_resource_group.mqe.name
  api_management_name = azurerm_api_management.pqe_apim.name
  protocol            = "http"
  url                 = "https://${local.pqe_dns}/"
  tls {
    validate_certificate_chain = false
    validate_certificate_name  = false
  }
}

resource "azurerm_api_management_logger" "pqe" {
  name                = "pqe-logger"
  api_management_name = azurerm_api_management.pqe_apim.name
  resource_group_name = azurerm_resource_group.mqe.name

  application_insights {
    instrumentation_key = azurerm_application_insights.pqe_application_insights.instrumentation_key
  }
}

resource "azurerm_api_management_diagnostic" "pqe" {
  identifier               = "applicationinsights"
  resource_group_name      = azurerm_resource_group.mqe.name
  api_management_name      = azurerm_api_management.pqe_apim.name
  api_management_logger_id = azurerm_api_management_logger.pqe.id
}

# Get all the public IP ranges for the location we're concerned with.
# This is used in the SAS token policy for rate limiting based on
# whether the traffic is coming from within or outside of the datacenter.
data "azurerm_network_service_tags" "in_datacenter_service_tags" {
  service         = "AzureCloud"
  location        = "eastus"
  location_filter = local.location
}

resource "azurerm_api_management_api_operation" "root_head_op" {
  operation_id        = "rootheadop"
  api_name            = azurerm_api_management_api.pqe_api.name
  api_management_name = azurerm_api_management.pqe_apim.name
  resource_group_name = azurerm_resource_group.mqe.name
  display_name        = "Root HEAD Operation"
  method              = "HEAD"
  url_template        = "/"
  description         = "API Root HEAD Operation"
}

# The return-response policy aborts pipeline execution and returns a
# default 200 OK with no body if no other elements provided between
# the return-response tags
# HEAD operations sent to the root of the API will just return 200 OK
# so that this won't get to the backend, since there is no API designed
# for requesting root
resource "azurerm_api_management_api_operation_policy" "root_head_op_policy" {
  api_name            = azurerm_api_management_api.pqe_api.name
  api_management_name = azurerm_api_management.pqe_apim.name
  resource_group_name = azurerm_resource_group.mqe.name
  operation_id        = azurerm_api_management_api_operation.root_head_op.operation_id
  xml_content         = <<XML
                <policies>
                    <inbound>
                        <return-response>
                        </return-response>
                    </inbound>
                    <outbound>
                        <base />
                    </outbound>
                </policies>
                XML
}

resource "azurerm_api_management_api_operation" "sas_get_op" {
  operation_id        = "sastokengetop"
  api_name            = azurerm_api_management_api.pqe_api.name
  api_management_name = azurerm_api_management.pqe_apim.name
  resource_group_name = azurerm_resource_group.mqe.name
  display_name        = "SAS GET Operation"
  method              = "GET"
  url_template        = "/sas/*"
  description         = "Calls SAS GET Operation"
}

resource "azurerm_api_management_api_operation_policy" "sas_get_op_policy" {
  api_name            = azurerm_api_management_api.pqe_api.name
  api_management_name = azurerm_api_management.pqe_apim.name
  resource_group_name = azurerm_resource_group.mqe.name
  operation_id        = azurerm_api_management_api_operation.sas_get_op.operation_id
  xml_content = templatefile("../policies/SASToken.xml", {
    # cidrs = join("\", \"", data.azurerm_network_service_tags.in_datacenter_service_tags.address_prefixes)
    cidrs = ""
  })
}

resource "azurerm_api_management_api_operation" "pqe_api_stac_get_op" {
  operation_id        = "stacgetop"
  api_name            = azurerm_api_management_api.pqe_api.name
  api_management_name = azurerm_api_management.pqe_apim.name
  resource_group_name = azurerm_resource_group.mqe.name
  display_name        = "STAC GET Operation"
  method              = "GET"
  url_template        = "/stac/*"
  description         = "Calls a STAC GET Operation"
}

resource "azurerm_api_management_api_operation_policy" "pqe_api_stac_get_op_policy" {
  api_name            = azurerm_api_management_api.pqe_api.name
  api_management_name = azurerm_api_management.pqe_apim.name
  resource_group_name = azurerm_resource_group.mqe.name
  operation_id        = azurerm_api_management_api_operation.pqe_api_stac_get_op.operation_id
  xml_content         = <<XML
                <policies>
                    <inbound>
                        <base />
                        <set-backend-service backend-id="pqe-backend" />
                        <set-header name="host" exists-action="override">
                            <value>@(context.Request.OriginalUrl.ToUri().Host)</value>
                        </set-header>
                    </inbound>
                    <outbound>
                        <base />
                    </outbound>
                </policies>
                XML
}

resource "azurerm_api_management_api_operation" "pqe_api_data_get_op" {
  operation_id        = "datagetop"
  api_name            = azurerm_api_management_api.pqe_api.name
  api_management_name = azurerm_api_management.pqe_apim.name
  resource_group_name = azurerm_resource_group.mqe.name
  display_name        = "Data GET Operation"
  method              = "GET"
  url_template        = "/data/*"
  description         = "Calls a Data GET Operation"
}

resource "azurerm_api_management_api_operation_policy" "pqe_api_data_get_op_policy" {
  api_name            = azurerm_api_management_api.pqe_api.name
  api_management_name = azurerm_api_management.pqe_apim.name
  resource_group_name = azurerm_resource_group.mqe.name
  operation_id        = azurerm_api_management_api_operation.pqe_api_data_get_op.operation_id
  xml_content         = <<XML
                <policies>
                    <inbound>
                        <base />
                        <set-backend-service backend-id="pqe-backend" />
                        <set-header name="host" exists-action="override">
                            <value>@(context.Request.OriginalUrl.ToUri().Host)</value>
                        </set-header>
                    </inbound>
                    <outbound>
                        <base />
                    </outbound>
                </policies>
                XML
}
