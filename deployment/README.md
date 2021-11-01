# Deployment

This folder contains the code to run a deployment of the Planetary Computer APIs in Azure. It includes a few steps that use Terraform and Helm.

## Deploy script

The logic for the deployment workflow is encapsulated in the [bin/deploy](bin/deploy) script. You can run from the top level of the repository via `scripts/cideploy` by CI. You can also drop into a console to manually run steps for a dev deployment via

```
scripts/console --deploy
```

## Manual resources

### Deployment secrets Key Vault

Deployment requires access to a Key Vault with some deployment secrets. If you are making you own stack, you'll need to create your own key vault and set the appropriate variable in the terraform. See the `keyvault.tf` resource for the list of secrets required, and to make sure these docs
are not out of date.

The service principle here needs to have the Storage Account Data Contributor role assigned for each container made available through the sas-token and sign endpoints.

## Dev deployment

To deploy your own stack, terraform will run in
the `deployment/terraform/dev` stack. Run `scripts/deploy --dev` to do this. You'll need the following
environment variables set according with the credential
information for a service principal that has permissions
to deploy to your subscription:

- `subscriptionId`
- `tenantId`
- `servicePrincipalId`
- `servicePrincipalKey`


__Note:__ Remember to bring down your resources after testing with `terraform destroy`!