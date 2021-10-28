output "environment" {
    value = var.environment
}

output "location" {
    value = local.location
}

output "cluster_name" {
  value = azurerm_kubernetes_cluster.pqe.name
}

output "resource_group" {
  value = azurerm_resource_group.pqe.name
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

## Application Insights
output "instrumentation_key" {
  value = azurerm_application_insights.pqe_application_insights.instrumentation_key
}
