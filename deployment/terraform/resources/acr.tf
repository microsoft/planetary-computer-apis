data "azurerm_container_registry" "pctest" {
  name                = var.pc_test_resources_acr
  resource_group_name = var.pc_test_resources_rg
}

# add the role to the identity the kubernetes cluster was assigned
resource "azurerm_role_assignment" "attach_acr" {
  scope                = data.azurerm_container_registry.pctest.id
  role_definition_name = "AcrPull"
  principal_id         = azurerm_kubernetes_cluster.mqe.kubelet_identity[0].object_id
}
