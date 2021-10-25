# Deployment

- [Deployment](#deployment)
  - [Configure Azure resources](#configure-azure-resources)
  - [Build and publish containers](#build-and-publish-containers)
  - [Create Helm apps](#create-helm-apps)

The publicy available Planetary Query Engine is a collection of related services
that run as containers in Azure Kubernetes Service (AKS). Getting those
containers deployed requires a few steps, that we'll go into more below:

* Configure Azure resources
* Build and publish containers
* Create Helm apps consuming those containers

There are many other resources deployed in the public Planetary Query Engine,
but we'll focus here just on the "run containers in the cloud" piece of the
deployment.

## Configure Azure resources

The key resources required for deploying containers into AKS are a cluster and a
container registry. If you're not familiar with Kubernetes, the cluster is an
abstraction representing a connection between a _scheduler_ and a _node pool_.
This is a gross oversimplification, but it's sufficient for describing the
Planetary Query Engine's Kubernetes deployment. The node pool is responsible for
providing undifferentiated compute capacity. The scheduler is responsible for
keeping track of what tasks need to run and assigning them to the node pool.

We provision this cluster using terraform, and you can find the cluster
configuration in [aks.tf](../deployment/terraform/resources/aks.tf).

## Build and publish containers

Building containers happens in the [`update` script](../scripts/update). You can
see there that there are a few `build` commands starting with `docker-compose`.
Those commands build the containers necessary for running the services, running
migrations, and more.

After those containers are built, they need to be pushed to a _container
registry_. That happens in the [`cipublish`](../scripts/cipublish) script. For
each of the metadata query engine, data query engine, and SAS services, that
script ships the containers to the configured container registry. You'll need to
ensure that the relevant variables referred to in that file are set in your
environment, that the Azure Container Registry referred to exists, and that
you've logged in to Azure and that container registry with `az login` and `az
acr login`, but having completed those steps, you can ship the built containers.

## Create Helm apps

To run the published containers in the cluster, we create _Helm charts_. Helm
charts are a templating system for deploying services to Kubernetes clusters.

If you're unfamiliar with Helm and need to debug deployment-related issues, you
can check out the [Helm's topics](https://helm.sh/docs/topics/). However, in
short, you'll need to be able to provide variables to fill in [the deploy values
template](../deployment/helm/deploy-values.template.yaml). Most of them are
availabale from Terraform output, if you completed the Terrraform step; however
some also depend on environment variables that you also already needed. You can
find the latter category of values prefixed with `env.` in the template.