provider "azurerm" {
  features {}
  use_oidc = true

  # This could be used instead of temporarily enabling shared key access once
  # this issue is resolved.
  # https://github.com/hashicorp/terraform-provider-azurerm/issues/23142
  # storage_use_azuread = true
}

provider "azurerm" {
  alias           = "planetary_computer_subscription"
  subscription_id = "9da7523a-cb61-4c3e-b1d4-afa5fc6d2da9"
  features {}
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
