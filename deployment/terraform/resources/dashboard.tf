resource "azurerm_dashboard" "pqe" {
  name                = "pqe-dashboard"
  resource_group_name = azurerm_resource_group.mqe.name
  location            = azurerm_resource_group.mqe.location
  tags = {
    source = "terraform"
  }
  dashboard_properties = <<DASH
{
  "lenses": {
    "0": {
      "order": 0,
      "parts": {
        "0": {
          "position": {
            "x": 0,
            "y": 0,
            "colSpan": 6,
            "rowSpan": 4
          },
          "metadata": {
            "inputs": [
              {
                "name": "options",
                "isOptional": true
              },
              {
                "name": "sharedTimeRange",
                "isOptional": true
              }
            ],
            "type": "Extension/HubsExtension/PartType/MonitorChartPart",
            "settings": {
              "content": {
                "options": {
                  "chart": {
                    "metrics": [
                      {
                        "resourceMetadata": {
                          "id": "${azurerm_application_insights.pqe_application_insights.id}"
                        },
                        "name": "requests/count",
                        "aggregationType": 7,
                        "namespace": "microsoft.insights/components",
                        "metricVisualization": {
                          "displayName": "Server requests",
                          "resourceDisplayName": "PQE"
                        }
                      }
                    ],
                    "title": "Requests (count)",
                    "titleKind": 1,
                    "visualization": {
                      "chartType": 2,
                      "legendVisualization": {
                        "isVisible": true,
                        "position": 2,
                        "hideSubtitle": false
                      },
                      "axisVisualization": {
                        "x": {
                          "isVisible": true,
                          "axisType": 2
                        },
                        "y": {
                          "isVisible": true,
                          "axisType": 1
                        }
                      },
                      "disablePinning": true
                    }
                  }
                }
              }
            }
          }
        },
        "1": {
          "position": {
            "x": 6,
            "y": 0,
            "colSpan": 6,
            "rowSpan": 4
          },
          "metadata": {
            "inputs": [
              {
                "name": "options",
                "isOptional": true
              },
              {
                "name": "sharedTimeRange",
                "isOptional": true
              }
            ],
            "type": "Extension/HubsExtension/PartType/MonitorChartPart",
            "settings": {
              "content": {
                "options": {
                  "chart": {
                    "metrics": [
                      {
                        "resourceMetadata": {
                          "id": "${azurerm_application_insights.pqe_application_insights.id}"
                        },
                        "name": "requests/duration",
                        "aggregationType": 4,
                        "namespace": "microsoft.insights/components",
                        "metricVisualization": {
                          "displayName": "Server response time",
                          "resourceDisplayName": "PQE"
                        }
                      }
                    ],
                    "title": "Response Time (average)",
                    "titleKind": 1,
                    "visualization": {
                      "chartType": 2,
                      "legendVisualization": {
                        "isVisible": true,
                        "position": 2,
                        "hideSubtitle": false
                      },
                      "axisVisualization": {
                        "x": {
                          "isVisible": true,
                          "axisType": 2
                        },
                        "y": {
                          "isVisible": true,
                          "axisType": 1
                        }
                      },
                      "disablePinning": true
                    }
                  }
                }
              }
            }
          }
        },
        "2": {
          "position": {
            "x": 12,
            "y": 0,
            "colSpan": 6,
            "rowSpan": 4
          },
          "metadata": {
            "inputs": [
              {
                "name": "options",
                "isOptional": true
              },
              {
                "name": "sharedTimeRange",
                "isOptional": true
              }
            ],
            "type": "Extension/HubsExtension/PartType/MonitorChartPart",
            "settings": {
              "content": {
                "options": {
                  "chart": {
                    "metrics": [
                      {
                        "resourceMetadata": {
                          "id": "${azurerm_application_insights.pqe_application_insights.id}"
                        },
                        "name": "requests/failed",
                        "aggregationType": 7,
                        "namespace": "microsoft.insights/components",
                        "metricVisualization": {
                          "displayName": "Failed requests",
                          "resourceDisplayName": "PQE"
                        }
                      }
                    ],
                    "title": "Failed Requests (count)",
                    "titleKind": 1,
                    "visualization": {
                      "chartType": 2,
                      "legendVisualization": {
                        "isVisible": true,
                        "position": 2,
                        "hideSubtitle": false
                      },
                      "axisVisualization": {
                        "x": {
                          "isVisible": true,
                          "axisType": 2
                        },
                        "y": {
                          "isVisible": true,
                          "axisType": 1
                        }
                      },
                      "disablePinning": true
                    }
                  }
                }
              }
            }
          }
        },
        "3": {
          "position": {
            "x": 0,
            "y": 4,
            "colSpan": 6,
            "rowSpan": 4
          },
          "metadata": {
            "inputs": [
              {
                "name": "options",
                "isOptional": true
              },
              {
                "name": "sharedTimeRange",
                "isOptional": true
              }
            ],
            "type": "Extension/HubsExtension/PartType/MonitorChartPart",
            "settings": {
              "content": {
                "options": {
                  "chart": {
                    "metrics": [
                      {
                        "resourceMetadata": {
                          "id": "${azurerm_application_insights.pqe_application_insights.id}"
                        },
                        "name": "requests/custom/Request Size",
                        "aggregationType": 4,
                        "namespace": "microsoft.insights/components/kusto",
                        "metricVisualization": {
                          "displayName": "Request Size"
                        }
                      }
                    ],
                    "title": "Request Size (average)",
                    "titleKind": 1,
                    "visualization": {
                      "chartType": 2,
                      "legendVisualization": {
                        "isVisible": true,
                        "position": 2,
                        "hideSubtitle": false
                      },
                      "axisVisualization": {
                        "x": {
                          "isVisible": true,
                          "axisType": 2
                        },
                        "y": {
                          "isVisible": true,
                          "axisType": 1
                        }
                      },
                      "disablePinning": true
                    }
                  }
                }
              }
            }
          }
        },
        "4": {
          "position": {
            "x": 6,
            "y": 4,
            "colSpan": 6,
            "rowSpan": 4
          },
          "metadata": {
            "inputs": [
              {
                "name": "options",
                "isOptional": true
              },
              {
                "name": "sharedTimeRange",
                "isOptional": true
              }
            ],
            "type": "Extension/HubsExtension/PartType/MonitorChartPart",
            "settings": {
              "content": {
                "options": {
                  "chart": {
                    "metrics": [
                      {
                        "resourceMetadata": {
                          "id": "${azurerm_application_insights.pqe_application_insights.id}"
                        },
                        "name": "requests/custom/Response Size",
                        "aggregationType": 4,
                        "namespace": "microsoft.insights/components/kusto",
                        "metricVisualization": {
                          "displayName": "Response Size"
                        }
                      }
                    ],
                    "title": "Response Size (average)",
                    "titleKind": 1,
                    "visualization": {
                      "chartType": 2,
                      "legendVisualization": {
                        "isVisible": true,
                        "position": 2,
                        "hideSubtitle": false
                      },
                      "axisVisualization": {
                        "x": {
                          "isVisible": true,
                          "axisType": 2
                        },
                        "y": {
                          "isVisible": true,
                          "axisType": 1
                        }
                      },
                      "disablePinning": true
                    }
                  }
                }
              }
            }
          }
        },
        "5": {
          "position": {
            "x": 0,
            "y": 8,
            "colSpan": 6,
            "rowSpan": 4
          },
          "metadata": {
            "inputs": [
              {
                "name": "resourceTypeMode",
                "isOptional": true
              },
              {
                "name": "ComponentId",
                "isOptional": true
              },
              {
                "name": "Scope",
                "value": {
                  "resourceIds": [
                    "${azurerm_application_insights.pqe_application_insights.id}"
                  ]
                },
                "isOptional": true
              },
              {
                "name": "PartId",
                "value": "15b2426a-10c7-4acf-a231-14a920f934df",
                "isOptional": true
              },
              {
                "name": "Version",
                "value": "2.0",
                "isOptional": true
              },
              {
                "name": "TimeRange",
                "value": "P7D",
                "isOptional": true
              },
              {
                "name": "DashboardId",
                "isOptional": true
              },
              {
                "name": "DraftRequestParameters",
                "isOptional": true
              },
              {
                "name": "Query",
                "value": "requests\n| summarize ['requests/count_sum'] = count() by bin(timestamp, 15m)\n",
                "isOptional": true
              },
              {
                "name": "ControlType",
                "value": "AnalyticsGrid",
                "isOptional": true
              },
              {
                "name": "SpecificChart",
                "isOptional": true
              },
              {
                "name": "PartTitle",
                "value": "Analytics",
                "isOptional": true
              },
              {
                "name": "PartSubTitle",
                "value": "PQE",
                "isOptional": true
              },
              {
                "name": "Dimensions",
                "isOptional": true
              },
              {
                "name": "LegendOptions",
                "isOptional": true
              },
              {
                "name": "IsQueryContainTimeRange",
                "value": false,
                "isOptional": true
              }
            ],
            "type": "Extension/Microsoft_OperationsManagementSuite_Workspace/PartType/LogsDashboardPart",
            "settings": {
              "content": {
                "Query": "requests\n| summarize ['requests/count_sum'] = count() by client_CountryOrRegion\n\n",
                "PartTitle": "Requests by country or region",
                "PartSubTitle": "PQE"
              }
            },
            "savedContainerState": {
              "partTitle": "Requests by country or region",
              "assetName": "PQE"
            }
          }
        },
        "6": {
          "position": {
            "x": 6,
            "y": 8,
            "colSpan": 6,
            "rowSpan": 4
          },
          "metadata": {
            "inputs": [
              {
                "name": "resourceTypeMode",
                "isOptional": true
              },
              {
                "name": "ComponentId",
                "isOptional": true
              },
              {
                "name": "Scope",
                "value": {
                  "resourceIds": [
                    "${azurerm_application_insights.pqe_application_insights.id}"
                  ]
                },
                "isOptional": true
              },
              {
                "name": "PartId",
                "value": "1335eeba-2b6f-4ef8-9a15-fda68df1b104",
                "isOptional": true
              },
              {
                "name": "Version",
                "value": "2.0",
                "isOptional": true
              },
              {
                "name": "TimeRange",
                "value": "P7D",
                "isOptional": true
              },
              {
                "name": "DashboardId",
                "isOptional": true
              },
              {
                "name": "DraftRequestParameters",
                "isOptional": true
              },
              {
                "name": "Query",
                "value": "requests\n| summarize['API Operation'] = count() by operation_Name\n",
                "isOptional": true
              },
              {
                "name": "ControlType",
                "value": "AnalyticsGrid",
                "isOptional": true
              },
              {
                "name": "SpecificChart",
                "isOptional": true
              },
              {
                "name": "PartTitle",
                "value": "Analytics",
                "isOptional": true
              },
              {
                "name": "PartSubTitle",
                "value": "PQE",
                "isOptional": true
              },
              {
                "name": "Dimensions",
                "isOptional": true
              },
              {
                "name": "LegendOptions",
                "isOptional": true
              },
              {
                "name": "IsQueryContainTimeRange",
                "value": false,
                "isOptional": true
              }
            ],
            "type": "Extension/Microsoft_OperationsManagementSuite_Workspace/PartType/LogsDashboardPart",
            "settings": {
              "content": {
                "PartTitle": "Requests by API operation",
                "PartSubTitle": "PQE"
              }
            },
            "savedContainerState": {
              "partTitle": "Requests by API operation",
              "assetName": "PQE"
            }
          }
        }
      }
    }
  },
  "metadata": {
    "model": {
      "timeRange": {
        "value": {
          "relative": {
            "duration": 24,
            "timeUnit": 1
          }
        },
        "type": "MsPortalFx.Composition.Configuration.ValueTypes.TimeRange"
      },
      "filterLocale": {
        "value": "en-us"
      },
      "filters": {
        "value": {
          "MsPortalFx_TimeRange": {
            "model": {
              "format": "utc",
              "granularity": "auto",
              "relative": "7d"
            },
            "displayCache": {
              "name": "UTC Time",
              "value": "Past 7 days"
            },
            "filteredPartIds": [
              "StartboardPart-MonitorChartPart-a2e1d111-1c44-408c-9379-b9b1cebdba42",
              "StartboardPart-MonitorChartPart-a2e1d111-1c44-408c-9379-b9b1cebdba66",
              "StartboardPart-MonitorChartPart-a2e1d111-1c44-408c-9379-b9b1cebdba4e",
              "StartboardPart-MonitorChartPart-a2e1d111-1c44-408c-9379-b9b1cebdba33",
              "StartboardPart-MonitorChartPart-a2e1d111-1c44-408c-9379-b9b1cebdba5a",
              "StartboardPart-LogsDashboardPart-b75e70ed-e9d8-430b-8070-c151135270ae",
              "StartboardPart-LogsDashboardPart-7e6c9c6d-03a2-46f5-ab27-1c7377081189"
            ]
          }
        }
      }
    }
  }
}
DASH
}

resource "azurerm_dashboard" "pqe-requests" {
  name                = "${local.pqe_stack_id}-${var.environment}-pqe-requests-dashboard"
  resource_group_name = azurerm_resource_group.mqe.name
  location            = azurerm_resource_group.mqe.location
  tags = {
    source = "terraform"
  }
  dashboard_properties = <<DASH
{
  "lenses": {
    "0": {
      "order": 0,
      "parts": {
        "0": {
          "position": {
            "x": 0,
            "y": 0,
            "colSpan": 18,
            "rowSpan": 1
          },
          "metadata": {
            "inputs": [],
            "type": "Extension/HubsExtension/PartType/MarkdownPart",
            "settings": {
              "content": {
                "settings": {
                  "content": "",
                  "title": "Request counts",
                  "subtitle": "",
                  "markdownSource": 1,
                  "markdownUri": null
                }
              }
            }
          }
        },
        "1": {
          "position": {
            "x": 0,
            "y": 1,
            "colSpan": 6,
            "rowSpan": 4
          },
          "metadata": {
            "inputs": [
              {
                "name": "resourceTypeMode",
                "isOptional": true
              },
              {
                "name": "ComponentId",
                "isOptional": true
              },
              {
                "name": "Scope",
                "value": {
                  "resourceIds": [
                    "${azurerm_application_insights.pqe_application_insights.id}"
                  ]
                },
                "isOptional": true
              },
              {
                "name": "PartId",
                "value": "0286c44d-225b-49cb-8615-77e16a283c28",
                "isOptional": true
              },
              {
                "name": "Version",
                "value": "2.0",
                "isOptional": true
              },
              {
                "name": "TimeRange",
                "value": "P1D",
                "isOptional": true
              },
              {
                "name": "DashboardId",
                "isOptional": true
              },
              {
                "name": "DraftRequestParameters",
                "isOptional": true
              },
              {
                "name": "Query",
                "value": "requests\n| extend Collection=extractjson(\"$['collection']\", tostring(customDimensions))\n| extend Service=extractjson(\"$['service']\", tostring(customDimensions))\n| filter Service == 'dqe'\n| filter string_size(Collection) > 0\n| summarize count() by bin(timestamp, 1hr), Collection\n| render timechart ",
                "isOptional": true
              },
              {
                "name": "ControlType",
                "value": "FrameControlChart",
                "isOptional": true
              },
              {
                "name": "SpecificChart",
                "value": "Line",
                "isOptional": true
              },
              {
                "name": "PartTitle",
                "value": "Analytics",
                "isOptional": true
              },
              {
                "name": "PartSubTitle",
                "value": "${azurerm_application_insights.pqe_application_insights.name}",
                "isOptional": true
              },
              {
                "name": "Dimensions",
                "value": {
                  "aggregation": "Sum",
                  "splitBy": [
                    {
                      "name": "Collection",
                      "type": "string"
                    }
                  ],
                  "xAxis": {
                    "name": "timestamp",
                    "type": "datetime"
                  },
                  "yAxis": [
                    {
                      "name": "count_",
                      "type": "long"
                    }
                  ]
                },
                "isOptional": true
              },
              {
                "name": "LegendOptions",
                "value": {
                  "isEnabled": true,
                  "position": "Bottom"
                },
                "isOptional": true
              },
              {
                "name": "IsQueryContainTimeRange",
                "value": false,
                "isOptional": true
              }
            ],
            "type": "Extension/Microsoft_OperationsManagementSuite_Workspace/PartType/LogsDashboardPart",
            "settings": {
              "content": {
                "PartTitle": "DQE Collection Requests Each Hour"
              }
            }
          }
        },
        "2": {
          "position": {
            "x": 6,
            "y": 1,
            "colSpan": 6,
            "rowSpan": 4
          },
          "metadata": {
            "inputs": [
              {
                "name": "resourceTypeMode",
                "isOptional": true
              },
              {
                "name": "ComponentId",
                "isOptional": true
              },
              {
                "name": "Scope",
                "value": {
                  "resourceIds": [
                    "${azurerm_application_insights.pqe_application_insights.id}"
                  ]
                },
                "isOptional": true
              },
              {
                "name": "PartId",
                "value": "136a2305-37a2-4ab5-ab14-50263899891b",
                "isOptional": true
              },
              {
                "name": "Version",
                "value": "2.0",
                "isOptional": true
              },
              {
                "name": "TimeRange",
                "value": "P1D",
                "isOptional": true
              },
              {
                "name": "DashboardId",
                "isOptional": true
              },
              {
                "name": "DraftRequestParameters",
                "isOptional": true
              },
              {
                "name": "Query",
                "value": "requests\n| extend Collection=extractjson(\"$['collection']\", tostring(customDimensions))\n| extend Service=extractjson(\"$['service']\", tostring(customDimensions))\n| filter Service == 'mqe'\n| filter string_size(Collection) > 0\n| summarize count() by bin(timestamp, 1hr), Collection\n| render timechart\n",
                "isOptional": true
              },
              {
                "name": "ControlType",
                "value": "FrameControlChart",
                "isOptional": true
              },
              {
                "name": "SpecificChart",
                "value": "Line",
                "isOptional": true
              },
              {
                "name": "PartTitle",
                "value": "Analytics",
                "isOptional": true
              },
              {
                "name": "PartSubTitle",
                "value": "${azurerm_application_insights.pqe_application_insights.name}",
                "isOptional": true
              },
              {
                "name": "Dimensions",
                "value": {
                  "aggregation": "Sum",
                  "splitBy": [
                    {
                      "name": "Collection",
                      "type": "string"
                    }
                  ],
                  "xAxis": {
                    "name": "timestamp",
                    "type": "datetime"
                  },
                  "yAxis": [
                    {
                      "name": "count_",
                      "type": "long"
                    }
                  ]
                },
                "isOptional": true
              },
              {
                "name": "LegendOptions",
                "value": {
                  "isEnabled": true,
                  "position": "Bottom"
                },
                "isOptional": true
              },
              {
                "name": "IsQueryContainTimeRange",
                "value": false,
                "isOptional": true
              }
            ],
            "type": "Extension/Microsoft_OperationsManagementSuite_Workspace/PartType/LogsDashboardPart",
            "settings": {
              "content": {
                "PartTitle": "MQE Collection Requests Each Hour"
              }
            }
          }
        },
        "3": {
          "position": {
            "x": 12,
            "y": 1,
            "colSpan": 6,
            "rowSpan": 4
          },
          "metadata": {
            "inputs": [
              {
                "name": "resourceTypeMode",
                "isOptional": true
              },
              {
                "name": "ComponentId",
                "isOptional": true
              },
              {
                "name": "Scope",
                "value": {
                  "resourceIds": [
                    "${azurerm_application_insights.pqe_application_insights.id}"
                  ]
                },
                "isOptional": true
              },
              {
                "name": "PartId",
                "value": "32e0a244-4d13-4b16-a15d-df7e948e434a",
                "isOptional": true
              },
              {
                "name": "Version",
                "value": "2.0",
                "isOptional": true
              },
              {
                "name": "TimeRange",
                "value": "P7D",
                "isOptional": true
              },
              {
                "name": "DashboardId",
                "isOptional": true
              },
              {
                "name": "DraftRequestParameters",
                "isOptional": true
              },
              {
                "name": "Query",
                "value": "requests\n| filter string_size(operation_Name) > 0\n| summarize['API Operation'] = count() by operation_Name\n| order by ['API Operation']\n\n",
                "isOptional": true
              },
              {
                "name": "ControlType",
                "value": "AnalyticsGrid",
                "isOptional": true
              },
              {
                "name": "SpecificChart",
                "isOptional": true
              },
              {
                "name": "PartTitle",
                "value": "Analytics",
                "isOptional": true
              },
              {
                "name": "PartSubTitle",
                "value": "PQE",
                "isOptional": true
              },
              {
                "name": "Dimensions",
                "isOptional": true
              },
              {
                "name": "LegendOptions",
                "isOptional": true
              },
              {
                "name": "IsQueryContainTimeRange",
                "value": false,
                "isOptional": true
              }
            ],
            "type": "Extension/Microsoft_OperationsManagementSuite_Workspace/PartType/LogsDashboardPart",
            "settings": {
              "content": {
                "PartTitle": "Top API Operations"
              }
            }
          }
        },
        "4": {
          "position": {
            "x": 0,
            "y": 5,
            "colSpan": 6,
            "rowSpan": 4
          },
          "metadata": {
            "inputs": [
              {
                "name": "resourceTypeMode",
                "isOptional": true
              },
              {
                "name": "ComponentId",
                "isOptional": true
              },
              {
                "name": "Scope",
                "value": {
                  "resourceIds": [
                    "${azurerm_application_insights.pqe_application_insights.id}"
                  ]
                },
                "isOptional": true
              },
              {
                "name": "PartId",
                "value": "11f57061-15d8-4f0f-97c8-de427af595d4",
                "isOptional": true
              },
              {
                "name": "Version",
                "value": "2.0",
                "isOptional": true
              },
              {
                "name": "TimeRange",
                "value": "P1D",
                "isOptional": true
              },
              {
                "name": "DashboardId",
                "isOptional": true
              },
              {
                "name": "DraftRequestParameters",
                "isOptional": true
              },
              {
                "name": "Query",
                "value": "requests\n| extend Collection=extractjson(\"$['collection']\", tostring(customDimensions))\n| extend Item=extractjson(\"$['item']\", tostring(customDimensions))\n| extend Service=extractjson(\"$['service']\", tostring(customDimensions))\n| filter Service == 'mqe'\n| filter string_size(Item) > 0\n| summarize count() by Item, Collection\n| top 10 by count_\n",
                "isOptional": true
              },
              {
                "name": "ControlType",
                "value": "AnalyticsGrid",
                "isOptional": true
              },
              {
                "name": "SpecificChart",
                "isOptional": true
              },
              {
                "name": "PartTitle",
                "value": "Analytics",
                "isOptional": true
              },
              {
                "name": "PartSubTitle",
                "value": "${azurerm_application_insights.pqe_application_insights.name}",
                "isOptional": true
              },
              {
                "name": "Dimensions",
                "isOptional": true
              },
              {
                "name": "LegendOptions",
                "isOptional": true
              },
              {
                "name": "IsQueryContainTimeRange",
                "value": false,
                "isOptional": true
              }
            ],
            "type": "Extension/Microsoft_OperationsManagementSuite_Workspace/PartType/LogsDashboardPart",
            "settings": {
              "content": {
                "PartTitle": "DQE Most Requested Items",
                "Query": "requests\n| extend Collection=extractjson(\"$['collection']\", tostring(customDimensions))\n| extend Item=extractjson(\"$['item']\", tostring(customDimensions))\n| extend Service=extractjson(\"$['service']\", tostring(customDimensions))\n| filter Service == 'dqe'\n| filter string_size(Item) > 0\n| summarize count() by Item, Collection\n| top 10 by count_\n\n"
              }
            }
          }
        },
        "5": {
          "position": {
            "x": 6,
            "y": 5,
            "colSpan": 6,
            "rowSpan": 4
          },
          "metadata": {
            "inputs": [
              {
                "name": "resourceTypeMode",
                "isOptional": true
              },
              {
                "name": "ComponentId",
                "isOptional": true
              },
              {
                "name": "Scope",
                "value": {
                  "resourceIds": [
                    "${azurerm_application_insights.pqe_application_insights.id}"
                  ]
                },
                "isOptional": true
              },
              {
                "name": "PartId",
                "value": "11f57061-15d8-4f0f-97c8-de427af595d4",
                "isOptional": true
              },
              {
                "name": "Version",
                "value": "2.0",
                "isOptional": true
              },
              {
                "name": "TimeRange",
                "value": "P1D",
                "isOptional": true
              },
              {
                "name": "DashboardId",
                "isOptional": true
              },
              {
                "name": "DraftRequestParameters",
                "isOptional": true
              },
              {
                "name": "Query",
                "value": "requests\n| extend Collection=extractjson(\"$['collection']\", tostring(customDimensions))\n| extend Item=extractjson(\"$['item']\", tostring(customDimensions))\n| extend Service=extractjson(\"$['service']\", tostring(customDimensions))\n| filter Service == 'mqe'\n| filter string_size(Item) > 0\n| summarize count() by Item, Collection\n| top 10 by count_\n",
                "isOptional": true
              },
              {
                "name": "ControlType",
                "value": "AnalyticsGrid",
                "isOptional": true
              },
              {
                "name": "SpecificChart",
                "isOptional": true
              },
              {
                "name": "PartTitle",
                "value": "Analytics",
                "isOptional": true
              },
              {
                "name": "PartSubTitle",
                "value": "${azurerm_application_insights.pqe_application_insights.name}",
                "isOptional": true
              },
              {
                "name": "Dimensions",
                "isOptional": true
              },
              {
                "name": "LegendOptions",
                "isOptional": true
              },
              {
                "name": "IsQueryContainTimeRange",
                "value": false,
                "isOptional": true
              }
            ],
            "type": "Extension/Microsoft_OperationsManagementSuite_Workspace/PartType/LogsDashboardPart",
            "settings": {
              "content": {
                "GridColumnsWidth": {
                  "Item": "259px"
                },
                "PartTitle": "MQE Most Requested Items"
              }
            }
          }
        },
        "6": {
          "position": {
            "x": 12,
            "y": 5,
            "colSpan": 6,
            "rowSpan": 4
          },
          "metadata": {
            "inputs": [
              {
                "name": "resourceTypeMode",
                "isOptional": true
              },
              {
                "name": "ComponentId",
                "isOptional": true
              },
              {
                "name": "Scope",
                "value": {
                  "resourceIds": [
                    "${azurerm_application_insights.pqe_application_insights.id}"
                  ]
                },
                "isOptional": true
              },
              {
                "name": "PartId",
                "value": "13f13412-77b9-4492-ba38-b181eb0b288a",
                "isOptional": true
              },
              {
                "name": "Version",
                "value": "2.0",
                "isOptional": true
              },
              {
                "name": "TimeRange",
                "value": "P7D",
                "isOptional": true
              },
              {
                "name": "DashboardId",
                "isOptional": true
              },
              {
                "name": "DraftRequestParameters",
                "isOptional": true
              },
              {
                "name": "Query",
                "value": "requests\n| filter string_size(operation_Name) > 0\n| filter extractjson(\"$['in-server']\", tostring(customDimensions)) != \"true\"\n| summarize ['Total Requests'] = count() by client_CountryOrRegion\n| order by ['Total Requests']\n",
                "isOptional": true
              },
              {
                "name": "ControlType",
                "value": "AnalyticsGrid",
                "isOptional": true
              },
              {
                "name": "SpecificChart",
                "isOptional": true
              },
              {
                "name": "PartTitle",
                "value": "Analytics",
                "isOptional": true
              },
              {
                "name": "PartSubTitle",
                "value": "PQE",
                "isOptional": true
              },
              {
                "name": "Dimensions",
                "isOptional": true
              },
              {
                "name": "LegendOptions",
                "isOptional": true
              },
              {
                "name": "IsQueryContainTimeRange",
                "value": false,
                "isOptional": true
              }
            ],
            "type": "Extension/Microsoft_OperationsManagementSuite_Workspace/PartType/LogsDashboardPart",
            "settings": {
              "content": {
                "PartTitle": "Request Count by Country of Origin"
              }
            }
          }
        },
        "7": {
          "position": {
            "x": 0,
            "y": 9,
            "colSpan": 18,
            "rowSpan": 1
          },
          "metadata": {
            "inputs": [],
            "type": "Extension/HubsExtension/PartType/MarkdownPart",
            "settings": {
              "content": {
                "settings": {
                  "content": "",
                  "title": "Service performance",
                  "subtitle": "",
                  "markdownSource": 1,
                  "markdownUri": null
                }
              }
            }
          }
        },
        "8": {
          "position": {
            "x": 0,
            "y": 10,
            "colSpan": 6,
            "rowSpan": 4
          },
          "metadata": {
            "inputs": [
              {
                "name": "resourceTypeMode",
                "isOptional": true
              },
              {
                "name": "ComponentId",
                "isOptional": true
              },
              {
                "name": "Scope",
                "value": {
                  "resourceIds": [
                    "${azurerm_application_insights.pqe_application_insights.id}"
                  ]
                },
                "isOptional": true
              },
              {
                "name": "PartId",
                "value": "25448fb6-424b-44fb-8047-d08b986f98d3",
                "isOptional": true
              },
              {
                "name": "Version",
                "value": "2.0",
                "isOptional": true
              },
              {
                "name": "TimeRange",
                "value": "P1D",
                "isOptional": true
              },
              {
                "name": "DashboardId",
                "isOptional": true
              },
              {
                "name": "DraftRequestParameters",
                "isOptional": true
              },
              {
                "name": "Query",
                "value": "requests\n| extend Service=extractjson(\"$['service']\", tostring(customDimensions))\n| filter Service == 'dqe'\n| summarize percentiles(duration, 50, 90, 95, 99) by bin(timestamp, 1hr)\n| render timechart\n",
                "isOptional": true
              },
              {
                "name": "ControlType",
                "value": "FrameControlChart",
                "isOptional": true
              },
              {
                "name": "SpecificChart",
                "value": "Line",
                "isOptional": true
              },
              {
                "name": "PartTitle",
                "value": "Analytics",
                "isOptional": true
              },
              {
                "name": "PartSubTitle",
                "value": "${azurerm_application_insights.pqe_application_insights.name}",
                "isOptional": true
              },
              {
                "name": "Dimensions",
                "value": {
                  "aggregation": "Sum",
                  "splitBy": [],
                  "xAxis": {
                    "name": "timestamp",
                    "type": "datetime"
                  },
                  "yAxis": [
                    {
                      "name": "percentile_duration_50",
                      "type": "real"
                    },
                    {
                      "name": "percentile_duration_90",
                      "type": "real"
                    },
                    {
                      "name": "percentile_duration_95",
                      "type": "real"
                    },
                    {
                      "name": "percentile_duration_99",
                      "type": "real"
                    }
                  ]
                },
                "isOptional": true
              },
              {
                "name": "LegendOptions",
                "value": {
                  "isEnabled": true,
                  "position": "Bottom"
                },
                "isOptional": true
              },
              {
                "name": "IsQueryContainTimeRange",
                "value": false,
                "isOptional": true
              }
            ],
            "type": "Extension/Microsoft_OperationsManagementSuite_Workspace/PartType/LogsDashboardPart",
            "settings": {
              "content": {
                "PartTitle": "DQE Response Time Percentiles",
                "Query": "requests\n| extend Service=extractjson(\"$['service']\", tostring(customDimensions))\n| filter Service == 'dqe'\n| summarize percentiles(duration, 50, 90, 95, 99) by bin(timestamp, 5min)\n| render timechart\n\n"
              }
            }
          }
        },
        "9": {
          "position": {
            "x": 6,
            "y": 10,
            "colSpan": 6,
            "rowSpan": 4
          },
          "metadata": {
            "inputs": [
              {
                "name": "resourceTypeMode",
                "isOptional": true
              },
              {
                "name": "ComponentId",
                "isOptional": true
              },
              {
                "name": "Scope",
                "value": {
                  "resourceIds": [
                    "${azurerm_application_insights.pqe_application_insights.id}"
                  ]
                },
                "isOptional": true
              },
              {
                "name": "PartId",
                "value": "64d8b471-f2d6-48c1-b305-1b16a6196e2f",
                "isOptional": true
              },
              {
                "name": "Version",
                "value": "2.0",
                "isOptional": true
              },
              {
                "name": "TimeRange",
                "value": "P1D",
                "isOptional": true
              },
              {
                "name": "DashboardId",
                "isOptional": true
              },
              {
                "name": "DraftRequestParameters",
                "isOptional": true
              },
              {
                "name": "Query",
                "value": "requests\n| extend Service=extractjson(\"$['service']\", tostring(customDimensions))\n| filter Service == 'mqe'\n| summarize percentiles(duration, 50, 90, 95, 99) by bin(timestamp, 1hr)\n| render timechart\n",
                "isOptional": true
              },
              {
                "name": "ControlType",
                "value": "FrameControlChart",
                "isOptional": true
              },
              {
                "name": "SpecificChart",
                "value": "Line",
                "isOptional": true
              },
              {
                "name": "PartTitle",
                "value": "Analytics",
                "isOptional": true
              },
              {
                "name": "PartSubTitle",
                "value": "${azurerm_application_insights.pqe_application_insights.name}",
                "isOptional": true
              },
              {
                "name": "Dimensions",
                "value": {
                  "aggregation": "Sum",
                  "splitBy": [],
                  "xAxis": {
                    "name": "timestamp",
                    "type": "datetime"
                  },
                  "yAxis": [
                    {
                      "name": "percentile_duration_50",
                      "type": "real"
                    },
                    {
                      "name": "percentile_duration_90",
                      "type": "real"
                    },
                    {
                      "name": "percentile_duration_95",
                      "type": "real"
                    },
                    {
                      "name": "percentile_duration_99",
                      "type": "real"
                    }
                  ]
                },
                "isOptional": true
              },
              {
                "name": "LegendOptions",
                "value": {
                  "isEnabled": true,
                  "position": "Bottom"
                },
                "isOptional": true
              },
              {
                "name": "IsQueryContainTimeRange",
                "value": false,
                "isOptional": true
              }
            ],
            "type": "Extension/Microsoft_OperationsManagementSuite_Workspace/PartType/LogsDashboardPart",
            "settings": {
              "content": {
                "PartTitle": "MQE Response Time Percentiles",
                "Query": "requests\n| extend Service=extractjson(\"$['service']\", tostring(customDimensions))\n| filter Service == 'mqe'\n| summarize percentiles(duration, 50, 90, 95, 99) by bin(timestamp, 5min)\n| render timechart\n\n"
              }
            }
          }
        },
        "10": {
          "position": {
            "x": 12,
            "y": 10,
            "colSpan": 6,
            "rowSpan": 4
          },
          "metadata": {
            "inputs": [
              {
                "name": "resourceTypeMode",
                "isOptional": true
              },
              {
                "name": "ComponentId",
                "isOptional": true
              },
              {
                "name": "Scope",
                "value": {
                  "resourceIds": [
                    "${azurerm_application_insights.pqe_application_insights.id}"
                  ]
                },
                "isOptional": true
              },
              {
                "name": "PartId",
                "value": "62fa4b37-b9ff-4886-b13e-d3b9f815df3b",
                "isOptional": true
              },
              {
                "name": "Version",
                "value": "2.0",
                "isOptional": true
              },
              {
                "name": "TimeRange",
                "value": "P7D",
                "isOptional": true
              },
              {
                "name": "DashboardId",
                "isOptional": true
              },
              {
                "name": "DraftRequestParameters",
                "isOptional": true
              },
              {
                "name": "Query",
                "value": "requests\n| filter success == false\n| filter extractjson(\"$['in-server']\", tostring(customDimensions)) != \"true\"\n| summarize count() by bin(timestamp, 5m)\n| render timechart\n",
                "isOptional": true
              },
              {
                "name": "ControlType",
                "value": "FrameControlChart",
                "isOptional": true
              },
              {
                "name": "SpecificChart",
                "value": "Line",
                "isOptional": true
              },
              {
                "name": "PartTitle",
                "value": "Analytics",
                "isOptional": true
              },
              {
                "name": "PartSubTitle",
                "value": "PQE",
                "isOptional": true
              },
              {
                "name": "Dimensions",
                "value": {
                  "xAxis": {
                    "name": "timestamp",
                    "type": "datetime"
                  },
                  "yAxis": [
                    {
                      "name": "count_",
                      "type": "long"
                    }
                  ],
                  "splitBy": [],
                  "aggregation": "Sum"
                },
                "isOptional": true
              },
              {
                "name": "LegendOptions",
                "value": {
                  "isEnabled": true,
                  "position": "Bottom"
                },
                "isOptional": true
              },
              {
                "name": "IsQueryContainTimeRange",
                "value": false,
                "isOptional": true
              }
            ],
            "type": "Extension/Microsoft_OperationsManagementSuite_Workspace/PartType/LogsDashboardPart",
            "settings": {},
            "partHeader": {
              "title": "Failed requests",
              "subtitle": ""
            }
          }
        },
        "11": {
          "position": {
            "x": 0,
            "y": 14,
            "colSpan": 6,
            "rowSpan": 4
          },
          "metadata": {
            "inputs": [
              {
                "name": "resourceTypeMode",
                "isOptional": true
              },
              {
                "name": "ComponentId",
                "isOptional": true
              },
              {
                "name": "Scope",
                "value": {
                  "resourceIds": [
                    "${azurerm_application_insights.pqe_application_insights.id}"
                  ]
                },
                "isOptional": true
              },
              {
                "name": "PartId",
                "value": "594d88b3-8c58-46bc-a797-220b563f806f",
                "isOptional": true
              },
              {
                "name": "Version",
                "value": "2.0",
                "isOptional": true
              },
              {
                "name": "TimeRange",
                "value": "P1D",
                "isOptional": true
              },
              {
                "name": "DashboardId",
                "isOptional": true
              },
              {
                "name": "DraftRequestParameters",
                "isOptional": true
              },
              {
                "name": "Query",
                "value": "requests\n| extend Path=extractjson(\"$['request.name']\", tostring(customDimensions))\n| extend Service=extractjson(\"$['service']\", tostring(customDimensions))\n| filter Service == 'dqe'\n| summarize percentile(duration, 95) by Path\n| top 5 by percentile_duration_95\n",
                "isOptional": true
              },
              {
                "name": "ControlType",
                "value": "AnalyticsGrid",
                "isOptional": true
              },
              {
                "name": "SpecificChart",
                "isOptional": true
              },
              {
                "name": "PartTitle",
                "value": "Analytics",
                "isOptional": true
              },
              {
                "name": "PartSubTitle",
                "value": "${azurerm_application_insights.pqe_application_insights.name}",
                "isOptional": true
              },
              {
                "name": "Dimensions",
                "isOptional": true
              },
              {
                "name": "LegendOptions",
                "isOptional": true
              },
              {
                "name": "IsQueryContainTimeRange",
                "value": false,
                "isOptional": true
              }
            ],
            "type": "Extension/Microsoft_OperationsManagementSuite_Workspace/PartType/LogsDashboardPart",
            "settings": {
              "content": {
                "GridColumnsWidth": {
                  "Path": "213px"
                },
                "PartTitle": "DQE Slow request paths"
              }
            }
          }
        },
        "12": {
          "position": {
            "x": 6,
            "y": 14,
            "colSpan": 6,
            "rowSpan": 4
          },
          "metadata": {
            "inputs": [
              {
                "name": "resourceTypeMode",
                "isOptional": true
              },
              {
                "name": "ComponentId",
                "isOptional": true
              },
              {
                "name": "Scope",
                "value": {
                  "resourceIds": [
                    "${azurerm_application_insights.pqe_application_insights.id}"
                  ]
                },
                "isOptional": true
              },
              {
                "name": "PartId",
                "value": "731aaf1c-71fe-4a32-a1da-560b013fe55f",
                "isOptional": true
              },
              {
                "name": "Version",
                "value": "2.0",
                "isOptional": true
              },
              {
                "name": "TimeRange",
                "value": "P1D",
                "isOptional": true
              },
              {
                "name": "DashboardId",
                "isOptional": true
              },
              {
                "name": "DraftRequestParameters",
                "isOptional": true
              },
              {
                "name": "Query",
                "value": "requests\n| extend Path=extractjson(\"$['request.name']\", tostring(customDimensions))\n| extend Service=extractjson(\"$['service']\", tostring(customDimensions))\n| filter Service == 'dqe'\n| summarize percentile(duration, 95) by Path\n| top 5 by percentile_duration_95\n",
                "isOptional": true
              },
              {
                "name": "ControlType",
                "value": "AnalyticsGrid",
                "isOptional": true
              },
              {
                "name": "SpecificChart",
                "isOptional": true
              },
              {
                "name": "PartTitle",
                "value": "Analytics",
                "isOptional": true
              },
              {
                "name": "PartSubTitle",
                "value": "${azurerm_application_insights.pqe_application_insights.name}",
                "isOptional": true
              },
              {
                "name": "Dimensions",
                "isOptional": true
              },
              {
                "name": "LegendOptions",
                "isOptional": true
              },
              {
                "name": "IsQueryContainTimeRange",
                "value": false,
                "isOptional": true
              }
            ],
            "type": "Extension/Microsoft_OperationsManagementSuite_Workspace/PartType/LogsDashboardPart",
            "settings": {
              "content": {
                "GridColumnsWidth": {
                  "Path": "214px"
                },
                "PartTitle": "MQE Slow request paths",
                "Query": "requests\n| extend Path=extractjson(\"$['request.name']\", tostring(customDimensions))\n| extend Service=extractjson(\"$['service']\", tostring(customDimensions))\n| filter Service == 'mqe'\n| summarize percentile(duration, 95) by Path\n| top 5 by percentile_duration_95\n\n"
              }
            }
          }
        }
      }
    }
  },
  "metadata": {
    "model": {
      "timeRange": {
        "value": {
          "relative": {
            "duration": 24,
            "timeUnit": 1
          }
        },
        "type": "MsPortalFx.Composition.Configuration.ValueTypes.TimeRange"
      },
      "filterLocale": {
        "value": "en-us"
      },
      "filters": {
        "value": {
          "MsPortalFx_TimeRange": {
            "model": {
              "format": "utc",
              "granularity": "auto",
              "relative": "3d"
            },
            "displayCache": {
              "name": "UTC Time",
              "value": "Past 3 days"
            },
            "filteredPartIds": [
              "StartboardPart-LogsDashboardPart-b0d3c74b-a345-4af9-a743-1bd2e89ed01f",
              "StartboardPart-LogsDashboardPart-b0d3c74b-a345-4af9-a743-1bd2e89ed009",
              "StartboardPart-LogsDashboardPart-b0d3c74b-a345-4af9-a743-1bd2e89ed00b",
              "StartboardPart-LogsDashboardPart-b0d3c74b-a345-4af9-a743-1bd2e89ed00d",
              "StartboardPart-LogsDashboardPart-b0d3c74b-a345-4af9-a743-1bd2e89ed00f",
              "StartboardPart-LogsDashboardPart-b0d3c74b-a345-4af9-a743-1bd2e89ed011",
              "StartboardPart-LogsDashboardPart-b0d3c74b-a345-4af9-a743-1bd2e89ed013",
              "StartboardPart-LogsDashboardPart-b0d3c74b-a345-4af9-a743-1bd2e89ed017",
              "StartboardPart-LogsDashboardPart-b0d3c74b-a345-4af9-a743-1bd2e89ed019",
              "StartboardPart-LogsDashboardPart-b0d3c74b-a345-4af9-a743-1bd2e89ed01b",
              "StartboardPart-LogsDashboardPart-b0d3c74b-a345-4af9-a743-1bd2e89ed01d"
            ]
          }
        }
      }
    }
  }
}

DASH
}