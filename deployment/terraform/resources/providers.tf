provider azurerm {
  features {}
  use_oidc = true
}

terraform {
  required_version = ">= 0.13"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "3.77.0"
    }
  }
}

data "azurerm_client_config" "current" {}