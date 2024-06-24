provider "azurerm" {
  features {}
  use_oidc = true

  # This could be used instead of temporarily enabling shared key access once
  # this issue is resolved.
  # https://github.com/hashicorp/terraform-provider-azurerm/issues/23142
  # storage_use_azuread = true
}

terraform {
  required_version = ">= 0.13"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "3.108.0"
    }
  }
}

data "azurerm_client_config" "current" {}
