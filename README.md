# Microsoft Planetary Computer APIs

__Note__: This repository serves as a reference implementation for deploying APIs on Azure. This code supports the production deployment of the Planetary Computer APIs. This repository is not meant to be reusable in other situations without significant modification, and the repository maintainers will not provide any support for non-development deployments of this code.

That said, feel free to crib any code that is useful!

## STAC API + Tiler

This repository contains two components of the Planetary Computer APIs: the STAC API and the Tiler. These are implementations of the open source [stac-fastapi](https://github.com/stac-utils/stac-fastapi) and [titiler](https://github.com/developmentseed/titiler) projects. It uses [titiler-pgstac](https://github.com/stac-utils/titiler-pgstac) to connect the tiler and database.

The `pcstac` project provides a STAC API which indexes Microsoft's publicly available [geospatial data](https://planetarycomputer.microsoft.com/catalog) and an API for searching through this large collection.
The `pctiler` provides visualization and data access capabilities for the data in the Planetary Computer.

## Azure Functions (a.k.a. Funcs)

This repository also contains Azure Functions that provide additional endpoints for working with Planetary Computer data and metadata. This includes Function endpoints for generating images and animations based on STAC searches, using the tiler to render mosaiced data from Collections.

## Collection configuration

See [collection config](./docs/collection-config.md) for more on developing collection configurations.

## Deployment

This repository hosts the code that is deployed in the Planetary Computer. It contains deployment code for hosting these services in Azure through running the published docker images and Helm charts in [Azure Kubernetes Service (AKS)](https://azure.microsoft.com/en-us/services/kubernetes-service/), which we used to stand up a development version of the services. The production deployment code is not contained in this repository.

For documentation of how you can deploy your own test version of these services, refer to [docs/01-deployment.md](./docs/01-deployment.md).

## Development URLs

After building the project locally using the instructions below, you can access the development version of the services by pointing your browser to the following URLs:

|                      |                                        |
|----------------------|----------------------------------------|
| STAC API (via nginx) | <http://localhost:8080/stac>           |
| Tiler (via nginx)    | <http://localhost:8080/data>           |
| Funcs (vai nginx)    | <http://localhost:8080/f/image>, etc.. |
| STAC API (direct)    | <http://localhost:8081>                |
| Tiler (direct)       | <http://localhost:8082>                |
| Funcs (direct)       | <http://localhost:8083>                |

To see the HTTP endpoints available for FastAPI servers, visit the OpenAPI documentation for each service:

|           |                                   |
|-----------|-----------------------------------|
| STAC API  | <http://localhost:8080/stac/docs> |
| Tiler API | <http://localhost:8080/data/docs> |

The development data only includes a single collection `naip`, with a few items in it. You can verify the data is loaded correctly by visiting the following URL:

<http://localhost:8080/stac/collections/naip>

## Building and Testing Locally

### Requirements

The development environment is run almost entirely through docker containers. Developing locally requires docker-compose v1.27+.

### Running the Planetary Computer API services in a local development environment

This project uses a variation on [scripts to rule them all](https://github.com/github/scripts-to-rule-them-all).

#### Environment setup and building images

Before setting up the local environment, you must set the AZURITE_ACCOUNT_KEY environment variable to the Azurite default
account key, a string that can be [found here](https://github.com/Azure/Azurite?tab=readme-ov-file#usage-with-azure-storage-sdks-or-tools).

For example, you can set the environment variable in your terminal with:

```console
export AZURITE_ACCOUNT_KEY=$(curl -s https://learn.microsoft.com/en-us/azure/storage/common/storage-use-azurite | grep "Account key:" | cut -b 24-111)
```

To set up a local environment, use:

```console
./scripts/setup
```

This will build containers, apply database migrations, and load the development data.

After migrations and development database loading are in place, you can rebuild the docker images with:

```console
./scripts/update
```

`pip` dependencies in `setup.py` are collected and installed through requirements files.
If you modify dependencies, run `./scripts/generate-requirements` to regenerate
`requirements-*.txt` used by Dockerfiles otherwise your dependency change will not
be realized.

#### Running the services

There is a local proxy service that facilitates a local "managed identity" functionality, run as your local identity. Make sure to run

```console
az login
```

To run the servers, use

```console
./scripts/server
```

This will bring up the development database, STAC API, Tiler, Azure Functions, and other services.  If at this point something errors out (e.g. nginx complaining about a config file), try deleting the containers/images and rerunning `./scripts/setup`.

The STAC API can be found at <http://localhost:8080/stac/> (goes through nginx) or <http://localhost:8081> directly.

To hit the tiler, try going to <http://localhost:8080/data/mosaic/info?collection=naip>, although it will fail due to lack of an authorization header.

#### Testing and and formatting

To run tests, use one of the following (note, you don't need `./scripts/server` running).  If you get an immediate error related to library stubs, just run it again.  The tiler tests may fail locally, TBD why.

```console
./scripts/test
./scripts/test --stac
./scripts/test --tiler
./scripts/test --common
```

To format code, use

```console
./scripts/format
```

## Changing environments

By default, the `stac`, `tiler`, `funcs`, and supporting services will run against the development containers brought up by `scripts/server`.
It can sometimes be convenient to test against other services, e.g. a test database deployed on Azure.
To do that, you can create a new environment file for the services based on `./pc-stac.dev.env`, `./pc-tiler.dev.env`, and/or `./pc-funcs.dev.env`.
Any environment file named similarly will be .gitignore'd, so you can leave them in your local clone and avoid
committing (e.g. `./pc-stac.testing.env`). You then need to set the `PC_STAC_ENV_FILE`, `PC_TILER_ENV_FILE`, and `PC_FUNCS_ENV_FILE` to the
environment files you want to use before running `scripts/server`. __Note__: Be careful not to run migrations
with a non-dev database set - avoid `scripts/setup`, or ensure the migration connection is still using the local
dev database even if using a remote test db.

## Published images, charts, and functions

This project publishes images and helm charts, which are used in the deployment of the Planetary Computer.

### Images

The following images are hosted in the [Microsoft Container Registry](https://github.com/microsoft/ContainerRegistry):

- `mcr.microsoft.com/planetary-computer-apis/stac`
- `mcr.microsoft.com/planetary-computer-apis/tiler`

Only tagged builds will be published to MCR, untagged builds will only be published to the internal ACR `pcccr`.

### Charts

See the [Helm chart repository](https://microsoft.github.io/planetary-computer-apis) published to GitHub pages for the published charts.

### Functions

See the [Function package repository](https://microsoft.github.io/planetary-computer-apis) published to GitHub pages for the published Azure Functions.