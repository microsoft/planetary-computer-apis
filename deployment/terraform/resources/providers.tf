provider azurerm {
  features {}
}

provider "azapi" {
  default_location = "West Europe"
  default_tags = {
    team = "PC Deployments"
  }
}

terraform {
  required_version = ">= 0.13"

  required_providers {
    azapi = {
      source  = "azure/azapi"
      version = "=0.1.0"
    }
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~>3.0"
    }
  }
}
