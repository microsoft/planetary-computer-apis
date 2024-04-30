resource "azurerm_kubernetes_cluster" "pc" {
  name                = "${local.prefix}-cluster"
  location            = azurerm_resource_group.pc.location
  resource_group_name = azurerm_resource_group.pc.name
  dns_prefix          = "${local.prefix}-cluster"
  kubernetes_version  = var.k8s_version

  key_vault_secrets_provider {
    secret_rotation_enabled = true
  }

  oidc_issuer_enabled       = true
  workload_identity_enabled = true

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

  maintenance_window {
    allowed {
      day = "Saturday"
      hours = [10, 11, 12, 13, 14, 15, 16, 17, 18]
    }
    # not_allowed {
    #   start = ISO8601
    #   end = ISO8601
    # }
  }

  # Recommendation is to make it at least 4 hours long
  # https://learn.microsoft.com/en-us/azure/aks/planned-maintenance?tabs=json-file#creating-a-maintenance-window
  maintenance_window_auto_upgrade {
    frequency = "Weekly"
    day_of_week = "Saturday"
    interval = 1
    duration = 4
    utc_offset = "+00:00"
    start_time = "10:00" # UTC
  }

  maintenance_window_node_os {
    frequency = "Weekly"
    day_of_week = "Saturday"
    interval = 1
    duration = 4
    utc_offset = "+00:00"
    start_time = "14:00" # UTC
  }

  tags = {
    Environment = var.environment
    ManagedBy   = "AI4E"
  }
}

# Workload Identity for tiler access to the Azure Maps account
resource "azurerm_user_assigned_identity" "tiler" {
  name                = "id-${local.prefix}"
  location            = var.region
  resource_group_name = azurerm_resource_group.pc.name
}

resource "azurerm_federated_identity_credential" "tiler" {
  name                = "federated-id-${local.prefix}"
  resource_group_name = azurerm_resource_group.pc.name
  audience            = ["api://AzureADTokenExchange"]
  issuer              = azurerm_kubernetes_cluster.pc.oidc_issuer_url
  subject             = "system:serviceaccount:pc:planetary-computer-tiler"
  parent_id           = azurerm_user_assigned_identity.tiler.id
  timeouts {}
}

resource "azurerm_role_assignment" "cluster-identity-maps-render-token" {
  scope                = azurerm_maps_account.azmaps.id
  role_definition_name = "Azure Maps Search and Render Data Reader"
  principal_id         = azurerm_user_assigned_identity.tiler.principal_id

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
