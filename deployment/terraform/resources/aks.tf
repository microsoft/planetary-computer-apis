resource "azurerm_kubernetes_cluster" "pc" {
  name                = "${local.prefix}-cluster"
  location            = azurerm_resource_group.pc.location
  resource_group_name = azurerm_resource_group.pc.name
  dns_prefix          = "${local.prefix}-cluster"
  kubernetes_version  = var.k8s_version

  key_vault_secrets_provider {
    secret_rotation_enabled = true
  }
  oidc_issuer_enabled = true

   # https://learn.microsoft.com/en-us/azure/aks/auto-upgrade-cluster#use-cluster-auto-upgrade
  automatic_channel_upgrade = "rapid"

  # https://learn.microsoft.com/en-us/azure/aks/auto-upgrade-node-os-image
  node_os_channel_upgrade = "NodeImage"

  image_cleaner_enabled = true

  default_node_pool {
    name                 = "agentpool"
    os_sku               = "AzureLinux"
    vm_size              = "Standard_DS2_v2"
    node_count           = var.aks_node_count
    vnet_subnet_id       = azurerm_subnet.node_subnet.id
    orchestrator_version = var.k8s_version
  }

  identity {
    type = "SystemAssigned"
  }

  azure_active_directory_role_based_access_control {
    managed            = true
    azure_rbac_enabled = true
  }

  tags = {
    Environment = var.environment
    ManagedBy   = "AI4E"
  }
}

# add the role to the identity the kubernetes cluster was assigned
resource "azurerm_role_assignment" "network" {
  scope                = azurerm_resource_group.pc.id
  role_definition_name = "Network Contributor"
  principal_id         = azurerm_kubernetes_cluster.pc.identity[0].principal_id
}

resource "azurerm_federated_identity_credential" "cluster" {
  name                = "federated-id-${local.prefix}-${var.environment}"
  resource_group_name = azurerm_kubernetes_cluster.pc.node_resource_group
  audience            = ["api://AzureADTokenExchange"]
  issuer              = azurerm_kubernetes_cluster.pc.oidc_issuer_url
  subject             = "system:serviceaccount:pc:nginx-ingress-ingress-nginx"
  parent_id           = "/subscriptions/a84a690d-585b-4c7c-80d9-851a48af5a50/resourceGroups/MC_pct-apis-westeurope-staging_rg_pct-apis-westeurope-staging-cluster_westeurope/providers/Microsoft.ManagedIdentity/userAssignedIdentities/azurekeyvaultsecretsprovider-pct-apis-westeurope-staging-cluster"
  timeouts {}
}

# If you add a second azurerm provider and use a data block to reference this key vault
# then the identity that deploys this has to have permissions over both subscriptions
# This role assignment was created manually but the resource is left here as a reminder
# resource "azurerm_role_assignment" "certificateAccess" {
#   scope                = #REDACTED
#   role_definition_name = #REDACTED
#   principal_id         = azurerm_kubernetes_cluster.pc.key_vault_secrets_provider[0].secret_identity[0].object_id
# }
