output "environment" {
    value = var.environment
}

output "location" {
    value = local.location
}

output "cluster_name" {
  value = azurerm_kubernetes_cluster.pc.name
}

output "resource_group" {
  value = azurerm_resource_group.pc.name
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

# Helm pass-through vars

output "cluster_cert_issuer" {
  value = var.cluster_cert_issuer
}

output "cluster_cert_server" {
  value = var.cluster_cert_server
}

## Ingress

output "ingress_ip" {
  value = azurerm_public_ip.pc.ip_address
}

output "dns_label" {
  value = azurerm_public_ip.pc.domain_name_label
}

## STAC API

output "stac_replica_count" {
  value = var.stac_replica_count
}

## TILER

output "tiler_replica_count" {
  value = var.tiler_replica_count
}

## Application Insights
output "instrumentation_key" {
  value = azurerm_application_insights.pc_application_insights.instrumentation_key
}
