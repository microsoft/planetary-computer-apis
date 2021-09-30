# Microsoft Planetary Query Engine

## Metadata Query Engine + Data Query Engine

This repository contains two components of the Planetary Computer: the metadata query engine (MQE), and the data query engine (DQE).
These systems are jointly referred to as the planetary query engine (PQE) and they provide the APIs which allow users of Microsoft's Planetary Computer to access a vast collection of geospatial datasets.
The MQE provides a STAC catalog which indexes Microsoft's publicly available [geospatial data](https://planetarycomputer.microsoft.com/catalog) and an API for searching through this large collection.
The DQE, on the other hand, makes it easy to use assets indexed within the MQE.
It does this in a couple of notable ways:
First, rather than downloading these assets and using desktop analysis software to view them at different zoom levels, the DQE allows users to dynamically generate a [tiled web map](https://en.wikipedia.org/wiki/Tiled_web_map) [url template](https://en.wikipedia.org/wiki/URI_Template) which can be used to zoom and pan around the assets in geospatial context.
Second, because the geospatial assets within the MQE are often profitably used together, the DQE enables users to define mosaics of imagery which can be used for viewing as well as analysis.

This document is focused on *local* development and intended to allow new users to spin up an instance and become familiar with the PQE.
For a more involved discussion of non-local deployments, refer to [docs/0x-deployment.md](./docs/0x-deployment.md).

## Development URLs

|              |                        |
|--------------|------------------------|
| Nginx        | <http://localhost:8080/> |
| MQE          | <http://localhost:8081/stac> |
| DQE          | <http://localhost:8082/data> |


## Building and Testing Locally

### Requirements

The development environment is run almost entirely through docker containers.
You should be able to run a fully functional (if significantly smaller) instance of the PQE locally with nothing more than docker and docker-compose.
As such, it is important to have the latest versions of docker and docker-compose installed.
At a minimum, running and developing locally requires docker-compose v1.27+.
Confusing and hard to diagnose issues are to be expected if using an older version.

Actual (non-local) deployment of the project requires use of [cipublish](./scripts/cipublish), for which you'll also need the [azure command line client](https://docs.microsoft.com/en-us/cli/azure/) (installation instructions can be found [here](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli)).
Running [cipublish](./scripts/cipublish) and installing the azure command line client is *not* needed for local development.

### Running the PQE in a local development environment

This project uses a somewhat simplified variation on [scripts to rule them all](https://github.com/github/scripts-to-rule-them-all).
These are the steps necessary to get everything running locally:

#### Building and running containers (the long version)

1. To build (or rebuild) the development containers for this project, run [scripts/update](./scripts/update).
2. With built containers, should be possible to apply the database migrations which allow Postgres+PostGIS to back a STAC API: just run [scripts/migrate](./scripts/migrate).
3. Bring the containers up now that migrations are in place with [scripts/server](./scripts/server).
4. If migrations are in place, this project's example data ([NAIP imagery](https://www.fsa.usda.gov/programs-and-services/aerial-photography/imagery-programs/naip-imagery/), incidentally) can be loaded into the database. Load testing data with [loadtestdata.py](mqe/mqe/loadtestdata.py). `loadtestdata.py` must be run *from within the MQE*. This can be accomplished with the help of docker-compose:
```
docker-compose \
    -f docker-compose.yml \
    run --rm \
    mqe \
    python /opt/src/mqe/mqe/loadtestdata.p
```

#### Building and running containers (the short version)

Using `scripts/update`, `scripts/migrate`, `scripts/server`, and finally running migrations should mostly be unecessary as `scripts/setup` manages the whole process for you.
Building project docker containers from scratch requires only a call to [scripts/setup](./scripts/setup).
This will build the project docker images, carry out necessary migrations, ingest example data into the development database, and stand up the PQE containers.
The only difference worth noting is that `scripts/setup` runs the containers in [detached mode](https://docs.docker.com/engine/reference/run/#detached-vs-foreground) (output from containers will run as daemons and thus not appear in the teriminal).

To verify that the containers are now running, check the output of `docker ps`.
You should see five containers running the following images: `pqe-nginx`, `pc-sasapi`, `pc-query-dataapi`, `pc-query-stacapi`, and `pqe-stac-db`.
During development it is often useful to see errors and debugging output from these containers; in this situation daemon mode is unhelpful.
To view application output (to undaemonize these processes), run [scripts/server](./scripts/server).
Once `scripts/server` has been executed, your terminal window should attach to the running processes and output from all services defined in [docker-compose.yml](./docker-compose.yml) should display in real time.


#### Testing, and formatting

To run tests, first ensure that the docker containers are running.
Tests interact with and make requests to these containers and will fail (miserably) if they aren't up and waiting for requests.
From there, simply run [scripts/test](./scripts/test)

