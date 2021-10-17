output "environment" {
    value = var.environment
}

output "location" {
    value = local.location
}

output "cluster_name" {
  value = azurerm_kubernetes_cluster.mqe.name
}

output "resource_group" {
  value = azurerm_resource_group.mqe.name
}

output "image_registry" {
  value = data.azurerm_container_registry.pctest.name
}

# -- Postgres

output "pg_host" {
  value = var.pg_host
}

output "pg_port" {
  value = var.pg_port
}

output "pg_user" {
  value = var.pg_user
}

output "pg_database" {
  value = var.pg_database
}

output "pg_password" {
    value = data.azurerm_key_vault_secret.db_admin_password.value
    sensitive = true
}

# -- Cosmos DB

output "cosmos_url" {
    value = var.cosmos_url
}

output "cosmos_db_name" {
    value = var.cosmos_db_name
}

output "cosmos_key" {
    value = data.azurerm_key_vault_secret.cosmos_key.value
    sensitive = true
}

# -- SAS delegation service principal

output "sas_tenant_id" {
    value = data.azurerm_key_vault_secret.sas_tenant_id.value
    sensitive = true
}

output "sas_client_id" {
    value = data.azurerm_key_vault_secret.sas_client_id.value
    sensitive = true
}

output "sas_client_secret" {
    value = data.azurerm_key_vault_secret.sas_client_secret.value
    sensitive = true
}


# Helm pass-through vars

output "cluster_cert_issuer" {
  value = var.cluster_cert_issuer
}

output "cluster_cert_server" {
  value = var.cluster_cert_server
}

## Ingress

output "ingress_ip" {
  value = azurerm_public_ip.pqe.ip_address
}

output "dns_label" {
  value = azurerm_public_ip.pqe.domain_name_label
}

## MQE

output "mqe_replica_count" {
  value = var.mqe_replica_count
}

## DQE

output "dqe_replica_count" {
  value = var.dqe_replica_count
}

## SAS

output "sas_replica_count" {
  value = var.sas_replica_count
}

output "sas_expiry_within_datacenter" {
  value = var.sas_expiry_within_datacenter
}
output "sas_expiry_out_of_datacenter" {
  value = var.sas_expiry_out_of_datacenter
}
output "sas_expiry_auth_within_datacenter" {
  value = var.sas_expiry_auth_within_datacenter
}
output "sas_expiry_auth_out_of_datacenter" {
  value = var.sas_expiry_auth_out_of_datacenter
}

## API Management
output "api_management_name" {
  value = azurerm_api_management.pqe_apim.name
}

## Application Insights
output "instrumentation_key" {
  value = azurerm_application_insights.pqe_application_insights.instrumentation_key
}
