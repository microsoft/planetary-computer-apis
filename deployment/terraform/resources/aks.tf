resource "azurerm_kubernetes_cluster" "pc" {
  name                = "${local.prefix}-cluster"
  location            = azurerm_resource_group.pc.location
  resource_group_name = azurerm_resource_group.pc.name
  dns_prefix          = "${local.prefix}-cluster"
  kubernetes_version  = var.k8s_version

  default_node_pool {
    name                 = "agentpool"
    vm_size              = "Standard_DS2_v2"
    max_count            = var.aks_max_node_count
    min_count            = var.aks_min_node_count
    node_count           = var.aks_node_count
    vnet_subnet_id       = azurerm_subnet.node_subnet.id
    orchestrator_version = var.k8s_version
    enable_auto_scaling  = true
  }

  monitor_metrics {
    annotations_allowed = var.metric_annotations_allowlist
    labels_allowed = var.metric_labels_allowlist
  }

  network_profile {
    network_plugin    = "azure"
    network_policy    = "azure"
    load_balancer_sku = "standard"
  }

  identity {
    type = "SystemAssigned"
  }

  azure_active_directory_role_based_access_control {
    managed = true
    azure_rbac_enabled = true
  }

  aci_connector_linux {
    subnet_name = azurerm_subnet.aci.name
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

resource "azurerm_monitor_data_collection_endpoint" "dce" {
  name                          = "MSProm-${azurerm_kubernetes_cluster.pc.name}"
  resource_group_name           = azurerm_resource_group.pc.name
  location                      = var.monitor_workspace_location
  kind                          = "Linux"
}

resource "azurerm_monitor_data_collection_rule" "dcr" {
  name                = "MSProm-${azurerm_kubernetes_cluster.pc.name}"
  resource_group_name = azurerm_resource_group.pc.name
  location            = var.monitor_workspace_location
  data_collection_endpoint_id = azurerm_monitor_data_collection_endpoint.dce.id
  kind                          = "Linux"

  destinations {
    monitor_account {
      monitor_account_id = var.monitor_workspace_id
      name = "MonitoringAccount${local.prefix}"
    }
  }

  data_flow {
    streams      = ["Microsoft-PrometheusMetrics"]
    destinations = ["MonitoringAccount${local.prefix}"]
  }


  data_sources {
    prometheus_forwarder {
      streams                       = ["Microsoft-PrometheusMetrics"]
      name                          = "PrometheusDataSource"
    }
  }

  description = "DCR for Azure Monitor Metrics Profile (Managed Prometheus)"
  depends_on = [
    azurerm_monitor_data_collection_endpoint.dce
  ]
}


resource "azurerm_monitor_data_collection_rule_association" "dcra" {
  name                        = "MSProm-${azurerm_kubernetes_cluster.pc.name}"
  target_resource_id          = azurerm_kubernetes_cluster.pc.id
  data_collection_rule_id     = azurerm_monitor_data_collection_rule.dcr.id
  description                 = "Association of data collection rule. Deleting this association will break the data collection for this AKS Cluster."
  depends_on = [
    azurerm_monitor_data_collection_rule.dcr
  ]
}

resource "azurerm_dashboard_grafana" "grafana" {
  name                              = var.grafana_name
  resource_group_name               = azurerm_resource_group.pc.name
  location                          = var.grafana_location

  identity {
    type = "SystemAssigned"
  }

  azure_monitor_workspace_integrations {
    resource_id  = var.monitor_workspace_id
  }
}


resource "azurerm_role_assignment" "datareaderrole" {
  scope              = var.monitor_workspace_id
  role_definition_id = "/subscriptions/${split("/",var.monitor_workspace_id)[2]}/providers/Microsoft.Authorization/roleDefinitions/b0d8363b-8ddd-447d-831f-62ca05bff136"
  principal_id       = azurerm_dashboard_grafana.grafana.identity.0.principal_id
}

resource "azapi_resource" "NodeRecordingRulesRuleGroup" {
  type = "Microsoft.AlertsManagement/prometheusRuleGroups@2023-03-01"
  name = "NodeRecordingRulesRuleGroup-${azurerm_kubernetes_cluster.pc.name}"
  location = var.monitor_workspace_location
  parent_id = azurerm_resource_group.pc.id
  body = jsonencode({
      "properties": {
        "scopes": [
          var.monitor_workspace_id
        ],
        "clusterName": "${azurerm_kubernetes_cluster.pc.name}",
        "interval": "PT1M",
        "rules": [
          {
            "record": "instance:node_num_cpu:sum",
            "expression": "count without (cpu, mode) (  node_cpu_seconds_total{job=\"node\",mode=\"idle\"})"
          },
          {
            "record": "instance:node_cpu_utilisation:rate5m",
            "expression": "1 - avg without (cpu) (  sum without (mode) (rate(node_cpu_seconds_total{job=\"node\", mode=~\"idle|iowait|steal\"}[5m])))"
          },
          {
            "record": "instance:node_load1_per_cpu:ratio",
            "expression": "(  node_load1{job=\"node\"}/  instance:node_num_cpu:sum{job=\"node\"})"
          },
          {
            "record": "instance:node_memory_utilisation:ratio",
            "expression": "1 - (  (    node_memory_MemAvailable_bytes{job=\"node\"}    or    (      node_memory_Buffers_bytes{job=\"node\"}      +      node_memory_Cached_bytes{job=\"node\"}      +      node_memory_MemFree_bytes{job=\"node\"}      +      node_memory_Slab_bytes{job=\"node\"}    )  )/  node_memory_MemTotal_bytes{job=\"node\"})"
          },
          {
            "record": "instance:node_vmstat_pgmajfault:rate5m",
            "expression": "rate(node_vmstat_pgmajfault{job=\"node\"}[5m])"
          },
          {
            "record": "instance_device:node_disk_io_time_seconds:rate5m",
            "expression": "rate(node_disk_io_time_seconds_total{job=\"node\", device!=\"\"}[5m])"
          },
          {
            "record": "instance_device:node_disk_io_time_weighted_seconds:rate5m",
            "expression": "rate(node_disk_io_time_weighted_seconds_total{job=\"node\", device!=\"\"}[5m])"
          },
          {
            "record": "instance:node_network_receive_bytes_excluding_lo:rate5m",
            "expression": "sum without (device) (  rate(node_network_receive_bytes_total{job=\"node\", device!=\"lo\"}[5m]))"
          },
          {
            "record": "instance:node_network_transmit_bytes_excluding_lo:rate5m",
            "expression": "sum without (device) (  rate(node_network_transmit_bytes_total{job=\"node\", device!=\"lo\"}[5m]))"
          },
          {
            "record": "instance:node_network_receive_drop_excluding_lo:rate5m",
            "expression": "sum without (device) (  rate(node_network_receive_drop_total{job=\"node\", device!=\"lo\"}[5m]))"
          },
          {
            "record": "instance:node_network_transmit_drop_excluding_lo:rate5m",
            "expression": "sum without (device) (  rate(node_network_transmit_drop_total{job=\"node\", device!=\"lo\"}[5m]))"
          }
        ]
      }
  })

  schema_validation_enabled = false
  ignore_missing_property   = false
}

resource "azapi_resource" "KubernetesReccordingRulesRuleGroup" {
  type = "Microsoft.AlertsManagement/prometheusRuleGroups@2023-03-01"
  name = "KubernetesReccordingRulesRuleGroup-${azurerm_kubernetes_cluster.pc.name}"
  location = var.monitor_workspace_location
  parent_id = azurerm_resource_group.pc.id
  body = jsonencode({
      "properties": {
        "scopes": [
          var.monitor_workspace_id
        ],
        "clusterName": "${azurerm_kubernetes_cluster.pc.name}",
        "interval": "PT1M",
        "rules": [
          {
            "record": "node_namespace_pod_container:container_cpu_usage_seconds_total:sum_irate",
            "expression": "sum by (cluster, namespace, pod, container) (  irate(container_cpu_usage_seconds_total{job=\"cadvisor\", image!=\"\"}[5m])) * on (cluster, namespace, pod) group_left(node) topk by (cluster, namespace, pod) (  1, max by(cluster, namespace, pod, node) (kube_pod_info{node!=\"\"}))"
          },
          {
            "record": "node_namespace_pod_container:container_memory_working_set_bytes",
            "expression": "container_memory_working_set_bytes{job=\"cadvisor\", image!=\"\"}* on (namespace, pod) group_left(node) topk by(namespace, pod) (1,  max by(namespace, pod, node) (kube_pod_info{node!=\"\"}))"
          },
          {
            "record": "node_namespace_pod_container:container_memory_rss",
            "expression": "container_memory_rss{job=\"cadvisor\", image!=\"\"}* on (namespace, pod) group_left(node) topk by(namespace, pod) (1,  max by(namespace, pod, node) (kube_pod_info{node!=\"\"}))"
          },
          {
            "record": "node_namespace_pod_container:container_memory_cache",
            "expression": "container_memory_cache{job=\"cadvisor\", image!=\"\"}* on (namespace, pod) group_left(node) topk by(namespace, pod) (1,  max by(namespace, pod, node) (kube_pod_info{node!=\"\"}))"
          },
          {
            "record": "node_namespace_pod_container:container_memory_swap",
            "expression": "container_memory_swap{job=\"cadvisor\", image!=\"\"}* on (namespace, pod) group_left(node) topk by(namespace, pod) (1,  max by(namespace, pod, node) (kube_pod_info{node!=\"\"}))"
          },
          {
            "record": "cluster:namespace:pod_memory:active:kube_pod_container_resource_requests",
            "expression": "kube_pod_container_resource_requests{resource=\"memory\",job=\"kube-state-metrics\"}  * on (namespace, pod, cluster)group_left() max by (namespace, pod, cluster) (  (kube_pod_status_phase{phase=~\"Pending|Running\"} == 1))"
          },
          {
            "record": "namespace_memory:kube_pod_container_resource_requests:sum",
            "expression": "sum by (namespace, cluster) (    sum by (namespace, pod, cluster) (        max by (namespace, pod, container, cluster) (          kube_pod_container_resource_requests{resource=\"memory\",job=\"kube-state-metrics\"}        ) * on(namespace, pod, cluster) group_left() max by (namespace, pod, cluster) (          kube_pod_status_phase{phase=~\"Pending|Running\"} == 1        )    ))"
          },
          {
            "record": "cluster:namespace:pod_cpu:active:kube_pod_container_resource_requests",
            "expression": "kube_pod_container_resource_requests{resource=\"cpu\",job=\"kube-state-metrics\"}  * on (namespace, pod, cluster)group_left() max by (namespace, pod, cluster) (  (kube_pod_status_phase{phase=~\"Pending|Running\"} == 1))"
          },
          {
            "record": "namespace_cpu:kube_pod_container_resource_requests:sum",
            "expression": "sum by (namespace, cluster) (    sum by (namespace, pod, cluster) (        max by (namespace, pod, container, cluster) (          kube_pod_container_resource_requests{resource=\"cpu\",job=\"kube-state-metrics\"}        ) * on(namespace, pod, cluster) group_left() max by (namespace, pod, cluster) (          kube_pod_status_phase{phase=~\"Pending|Running\"} == 1        )    ))"
          },
          {
            "record": "cluster:namespace:pod_memory:active:kube_pod_container_resource_limits",
            "expression": "kube_pod_container_resource_limits{resource=\"memory\",job=\"kube-state-metrics\"}  * on (namespace, pod, cluster)group_left() max by (namespace, pod, cluster) (  (kube_pod_status_phase{phase=~\"Pending|Running\"} == 1))"
          },
          {
            "record": "namespace_memory:kube_pod_container_resource_limits:sum",
            "expression": "sum by (namespace, cluster) (    sum by (namespace, pod, cluster) (        max by (namespace, pod, container, cluster) (          kube_pod_container_resource_limits{resource=\"memory\",job=\"kube-state-metrics\"}        ) * on(namespace, pod, cluster) group_left() max by (namespace, pod, cluster) (          kube_pod_status_phase{phase=~\"Pending|Running\"} == 1        )    ))"
          },
          {
            "record": "cluster:namespace:pod_cpu:active:kube_pod_container_resource_limits",
            "expression": "kube_pod_container_resource_limits{resource=\"cpu\",job=\"kube-state-metrics\"}  * on (namespace, pod, cluster)group_left() max by (namespace, pod, cluster) ( (kube_pod_status_phase{phase=~\"Pending|Running\"} == 1) )"
          },
          {
            "record": "namespace_cpu:kube_pod_container_resource_limits:sum",
            "expression": "sum by (namespace, cluster) (    sum by (namespace, pod, cluster) (        max by (namespace, pod, container, cluster) (          kube_pod_container_resource_limits{resource=\"cpu\",job=\"kube-state-metrics\"}        ) * on(namespace, pod, cluster) group_left() max by (namespace, pod, cluster) (          kube_pod_status_phase{phase=~\"Pending|Running\"} == 1        )    ))"
          },
          {
            "record": "namespace_workload_pod:kube_pod_owner:relabel",
            "expression": "max by (cluster, namespace, workload, pod) (  label_replace(    label_replace(      kube_pod_owner{job=\"kube-state-metrics\", owner_kind=\"ReplicaSet\"},      \"replicaset\", \"$1\", \"owner_name\", \"(.*)\"    ) * on(replicaset, namespace) group_left(owner_name) topk by(replicaset, namespace) (      1, max by (replicaset, namespace, owner_name) (        kube_replicaset_owner{job=\"kube-state-metrics\"}      )    ),    \"workload\", \"$1\", \"owner_name\", \"(.*)\"  ))",
            "labels": {
              "workload_type": "deployment"
            }
          },
          {
            "record": "namespace_workload_pod:kube_pod_owner:relabel",
            "expression": "max by (cluster, namespace, workload, pod) (  label_replace(    kube_pod_owner{job=\"kube-state-metrics\", owner_kind=\"DaemonSet\"},    \"workload\", \"$1\", \"owner_name\", \"(.*)\"  ))",
            "labels": {
              "workload_type": "daemonset"
            }
          },
          {
            "record": "namespace_workload_pod:kube_pod_owner:relabel",
            "expression": "max by (cluster, namespace, workload, pod) (  label_replace(    kube_pod_owner{job=\"kube-state-metrics\", owner_kind=\"StatefulSet\"},    \"workload\", \"$1\", \"owner_name\", \"(.*)\"  ))",
            "labels": {
              "workload_type": "statefulset"
            }
          },
          {
            "record": "namespace_workload_pod:kube_pod_owner:relabel",
            "expression": "max by (cluster, namespace, workload, pod) (  label_replace(    kube_pod_owner{job=\"kube-state-metrics\", owner_kind=\"Job\"},    \"workload\", \"$1\", \"owner_name\", \"(.*)\"  ))",
            "labels": {
              "workload_type": "job"
            }
          },
          {
            "record": ":node_memory_MemAvailable_bytes:sum",
            "expression": "sum(  node_memory_MemAvailable_bytes{job=\"node\"} or  (    node_memory_Buffers_bytes{job=\"node\"} +    node_memory_Cached_bytes{job=\"node\"} +    node_memory_MemFree_bytes{job=\"node\"} +    node_memory_Slab_bytes{job=\"node\"}  )) by (cluster)"
          },
          {
            "record": "cluster:node_cpu:ratio_rate5m",
            "expression": "sum(rate(node_cpu_seconds_total{job=\"node\",mode!=\"idle\",mode!=\"iowait\",mode!=\"steal\"}[5m])) by (cluster) /count(sum(node_cpu_seconds_total{job=\"node\"}) by (cluster, instance, cpu)) by (cluster)"
          }
        ]
      }
  })

  schema_validation_enabled = false
  ignore_missing_property   = false
}

resource "azapi_resource" "NodeRecordingRulesRuleGroupWin" {
  type = "Microsoft.AlertsManagement/prometheusRuleGroups@2023-03-01"
  name = "NodeRecordingRulesRuleGroup-Win-${azurerm_kubernetes_cluster.pc.name}"
  location = var.monitor_workspace_location
  parent_id = azurerm_resource_group.pc.id
  body = jsonencode({
      "properties": {
        "scopes": [
          var.monitor_workspace_id
        ],
        "clusterName": "${azurerm_kubernetes_cluster.pc.name}",
        "interval": "PT1M",
        "rules": [
          {
            "record": "node:windows_node:sum",
            "expression": "count (windows_system_system_up_time{job=\"windows-exporter\"})"
          },
          {
            "record": "node:windows_node_num_cpu:sum",
            "expression": "count by (instance) (sum by (instance, core) (windows_cpu_time_total{job=\"windows-exporter\"}))"
          },
          {
            "record": ":windows_node_cpu_utilisation:avg5m",
            "expression": "1 - avg(rate(windows_cpu_time_total{job=\"windows-exporter\",mode=\"idle\"}[5m]))"
          },
          {
            "record": "node:windows_node_cpu_utilisation:avg5m",
            "expression": "1 - avg by (instance) (rate(windows_cpu_time_total{job=\"windows-exporter\",mode=\"idle\"}[5m]))"
          },
          {
            "record": ":windows_node_memory_utilisation:",
            "expression": "1 -sum(windows_memory_available_bytes{job=\"windows-exporter\"})/sum(windows_os_visible_memory_bytes{job=\"windows-exporter\"})"
          },
          {
            "record": ":windows_node_memory_MemFreeCached_bytes:sum",
            "expression": "sum(windows_memory_available_bytes{job=\"windows-exporter\"} + windows_memory_cache_bytes{job=\"windows-exporter\"})"
          },
          {
            "record": "node:windows_node_memory_totalCached_bytes:sum",
            "expression": "(windows_memory_cache_bytes{job=\"windows-exporter\"} + windows_memory_modified_page_list_bytes{job=\"windows-exporter\"} + windows_memory_standby_cache_core_bytes{job=\"windows-exporter\"} + windows_memory_standby_cache_normal_priority_bytes{job=\"windows-exporter\"} + windows_memory_standby_cache_reserve_bytes{job=\"windows-exporter\"})"
          },
          {
            "record": ":windows_node_memory_MemTotal_bytes:sum",
            "expression": "sum(windows_os_visible_memory_bytes{job=\"windows-exporter\"})"
          },
          {
            "record": "node:windows_node_memory_bytes_available:sum",
            "expression": "sum by (instance) ((windows_memory_available_bytes{job=\"windows-exporter\"}))"
          },
          {
            "record": "node:windows_node_memory_bytes_total:sum",
            "expression": "sum by (instance) (windows_os_visible_memory_bytes{job=\"windows-exporter\"})"
          },
          {
            "record": "node:windows_node_memory_utilisation:ratio",
            "expression": "(node:windows_node_memory_bytes_total:sum - node:windows_node_memory_bytes_available:sum) / scalar(sum(node:windows_node_memory_bytes_total:sum))"
          },
          {
            "record": "node:windows_node_memory_utilisation:",
            "expression": "1 - (node:windows_node_memory_bytes_available:sum / node:windows_node_memory_bytes_total:sum)"
          },
          {
            "record": "node:windows_node_memory_swap_io_pages:irate",
            "expression": "irate(windows_memory_swap_page_operations_total{job=\"windows-exporter\"}[5m])"
          },
          {
            "record": ":windows_node_disk_utilisation:avg_irate",
            "expression": "avg(irate(windows_logical_disk_read_seconds_total{job=\"windows-exporter\"}[5m]) + irate(windows_logical_disk_write_seconds_total{job=\"windows-exporter\"}[5m]))"
          },
          {
            "record": "node:windows_node_disk_utilisation:avg_irate",
            "expression": "avg by (instance) ((irate(windows_logical_disk_read_seconds_total{job=\"windows-exporter\"}[5m]) + irate(windows_logical_disk_write_seconds_total{job=\"windows-exporter\"}[5m])))"
          }
        ]
      }
  })
  schema_validation_enabled = false
  ignore_missing_property   = false
}


resource "azapi_resource" "NodeAndKubernetesRecordingRulesRuleGroupWin" {
  type = "Microsoft.AlertsManagement/prometheusRuleGroups@2023-03-01"
  name = "NodeAndKubernetesRecordingRulesRuleGroup-Win-${azurerm_kubernetes_cluster.pc.name}"
  location = var.monitor_workspace_location
  parent_id = azurerm_resource_group.pc.id
  body = jsonencode({
      "properties": {
        "scopes": [
          var.monitor_workspace_id
        ],
        "clusterName": "[variables('clusterName')]",
        "interval": "PT1M",
        "rules": [
          {
            "record": "node:windows_node_filesystem_usage:",
            "expression": "max by (instance,volume)((windows_logical_disk_size_bytes{job=\"windows-exporter\"} - windows_logical_disk_free_bytes{job=\"windows-exporter\"}) / windows_logical_disk_size_bytes{job=\"windows-exporter\"})"
          },
          {
            "record": "node:windows_node_filesystem_avail:",
            "expression": "max by (instance, volume) (windows_logical_disk_free_bytes{job=\"windows-exporter\"} / windows_logical_disk_size_bytes{job=\"windows-exporter\"})"
          },
          {
            "record": ":windows_node_net_utilisation:sum_irate",
            "expression": "sum(irate(windows_net_bytes_total{job=\"windows-exporter\"}[5m]))"
          },
          {
            "record": "node:windows_node_net_utilisation:sum_irate",
            "expression": "sum by (instance) ((irate(windows_net_bytes_total{job=\"windows-exporter\"}[5m])))"
          },
          {
            "record": ":windows_node_net_saturation:sum_irate",
            "expression": "sum(irate(windows_net_packets_received_discarded_total{job=\"windows-exporter\"}[5m])) + sum(irate(windows_net_packets_outbound_discarded_total{job=\"windows-exporter\"}[5m]))"
          },
          {
            "record": "node:windows_node_net_saturation:sum_irate",
            "expression": "sum by (instance) ((irate(windows_net_packets_received_discarded_total{job=\"windows-exporter\"}[5m]) + irate(windows_net_packets_outbound_discarded_total{job=\"windows-exporter\"}[5m])))"
          },
          {
            "record": "windows_pod_container_available",
            "expression": "windows_container_available{job=\"windows-exporter\"} * on(container_id) group_left(container, pod, namespace) max(kube_pod_container_info{job=\"kube-state-metrics\"}) by(container, container_id, pod, namespace)"
          },
          {
            "record": "windows_container_total_runtime",
            "expression": "windows_container_cpu_usage_seconds_total{job=\"windows-exporter\"} * on(container_id) group_left(container, pod, namespace) max(kube_pod_container_info{job=\"kube-state-metrics\"}) by(container, container_id, pod, namespace)"
          },
          {
            "record": "windows_container_memory_usage",
            "expression": "windows_container_memory_usage_commit_bytes{job=\"windows-exporter\"} * on(container_id) group_left(container, pod, namespace) max(kube_pod_container_info{job=\"kube-state-metrics\"}) by(container, container_id, pod, namespace)"
          },
          {
            "record": "windows_container_private_working_set_usage",
            "expression": "windows_container_memory_usage_private_working_set_bytes{job=\"windows-exporter\"} * on(container_id) group_left(container, pod, namespace) max(kube_pod_container_info{job=\"kube-state-metrics\"}) by(container, container_id, pod, namespace)"
          },
          {
            "record": "windows_container_network_received_bytes_total",
            "expression": "windows_container_network_receive_bytes_total{job=\"windows-exporter\"} * on(container_id) group_left(container, pod, namespace) max(kube_pod_container_info{job=\"kube-state-metrics\"}) by(container, container_id, pod, namespace)"
          },
          {
            "record": "windows_container_network_transmitted_bytes_total",
            "expression": "windows_container_network_transmit_bytes_total{job=\"windows-exporter\"} * on(container_id) group_left(container, pod, namespace) max(kube_pod_container_info{job=\"kube-state-metrics\"}) by(container, container_id, pod, namespace)"
          },
          {
            "record": "kube_pod_windows_container_resource_memory_request",
            "expression": "max by (namespace, pod, container) (kube_pod_container_resource_requests{resource=\"memory\",job=\"kube-state-metrics\"}) * on(container,pod,namespace) (windows_pod_container_available)"
          },
          {
            "record": "kube_pod_windows_container_resource_memory_limit",
            "expression": "kube_pod_container_resource_limits{resource=\"memory\",job=\"kube-state-metrics\"} * on(container,pod,namespace) (windows_pod_container_available)"
          },
          {
            "record": "kube_pod_windows_container_resource_cpu_cores_request",
            "expression": "max by (namespace, pod, container) ( kube_pod_container_resource_requests{resource=\"cpu\",job=\"kube-state-metrics\"}) * on(container,pod,namespace) (windows_pod_container_available)"
          },
          {
            "record": "kube_pod_windows_container_resource_cpu_cores_limit",
            "expression": "kube_pod_container_resource_limits{resource=\"cpu\",job=\"kube-state-metrics\"} * on(container,pod,namespace) (windows_pod_container_available)"
          },
          {
            "record": "namespace_pod_container:windows_container_cpu_usage_seconds_total:sum_rate",
            "expression": "sum by (namespace, pod, container) (rate(windows_container_total_runtime{}[5m]))"
          }
        ]
      }
  })
  schema_validation_enabled = false
  ignore_missing_property   = false
}

resource "azurerm_role_assignment" "aci_network_constributor" {
  scope                = azurerm_subnet.aci.id
  role_definition_name = "Network Contributor"
  principal_id         = azurerm_kubernetes_cluster.pc.aci_connector_linux[0].connector_identity[0].object_id
}

resource "azurerm_role_assignment" "aci_reader" {
  scope                = azurerm_subnet.aci.id
  role_definition_name = "Reader"
  principal_id         = azurerm_kubernetes_cluster.pc.aci_connector_linux[0].connector_identity[0].object_id
}
