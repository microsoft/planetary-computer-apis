# Microsoft Planetary Computer APIs

__Note__: This repository serves as a reference implementation for deploying APIs on Azure. This code supports the production deployment of the Planetary Computer APIs. This repository is not meant to be reusable in other situations without significant modification, and the repository maintainers will not provide any support for non-development deployments of this code.

That said, feel free to crib any code that is useful!

## STAC API + Tiler

This repository contains two components of the Planetary Computer APIs: the STAC API and the Tiler. These are implementations of the open source [stac-fastapi](https://github.com/stac-utils/stac-fastapi) and [titiler](https://github.com/developmentseed/titiler) projects.

The `pcstac` project provides a STAC API which indexes Microsoft's publicly available [geospatial data](https://planetarycomputer.microsoft.com/catalog) and an API for searching through this large collection.
The `pctiler` provides visualization and data access capabilities for the data in the Planetary Computer.

## Collection configuration

See [collection config](./docs/collection-config.md) for more on developing collection configurations.

## Deployment

This repository hosts the code that is deployed in the Planetary Computer. It contains deployment code for hosting these services in Azure through running the published docker images and Helm charts in [Azure Kubernetes Service (AKS)](https://azure.microsoft.com/en-us/services/kubernetes-service/), which we used to stand up a development version of the services. The production deployment code is not contained in this repository.

For documentation of how you can deploy your own test version of these services, refer to [docs/0x-deployment.md](./docs/0x-deployment.md).

## Development URLs

|          |                              |
| -------- | ---------------------------- |
| Nginx    | <http://localhost:8080/>     |
| STAC API | <http://localhost:8081/stac> |
| Tiler    | <http://localhost:8082/data> |


## Building and Testing Locally

### Requirements

The development environment is run almost entirely through docker containers. Developing locally requires docker-compose v1.27+.

### Running the Planetary Computer API services in a local development environment

This project uses a variation on [scripts to rule them all](https://github.com/github/scripts-to-rule-them-all).

#### Environment setup and building images

To set up a local environment, use

```
> ./scripts/update
```

This will build containers, apply database migrations, and load the development data.

After migrations and development database loading are in place, you can just rebuild the docker images with

```
> ./scripts/update
```

#### Running the services

To run the servers, use

```
> ./scripts/server
```

This will bring up the development database, STAC API, and Tiler.

#### Testing and and formatting

To run tests, use

```
./scripts/test
```

To format code, use

```
./scripts/format
```

## Published images and charts

This project publishes images and helm charts, which are used in the deployment of the Planetary Computer.

### Images

Images following images are hosted in the [Microsoft Container Registry](https://github.com/microsoft/ContainerRegistry):

- `mcr.microsoft.com/planetary-computer-apis/stac`
- `mcr.microsoft.com/planetary-computer-apis/tiler`

### Charts

See the [Helm chart repository](https://microsoft.github.io/planetary-computer-apis) published to GitHub pages for the published charts.

### Building /queryable schemas

Schemas can be built/updated with

```
./scripts/build_queryables
```