[![Build Status](https://dev.azure.com/planetary-computer/Planetary%20Computer%20Components/_apis/build/status/metadata-query-api?branchName=master)](https://dev.azure.com/planetary-computer/Planetary%20Computer%20Components/_build/latest?definitionId=5&branchName=master)
# STAC API + Data Query API

This repository contains two components of the Planetary Computer: the STAC API component, and the data query API component.

## Develop URLs

|              |                          |
|--------------|--------------------------|
| Nginx        | <http://localhost:8080/> |
| MQE (STAC)   | <http://localhost:8081/> |
| DQE          | <http://localhost:8082/> |

Nginx proxies the dqe and mqe to these URLs:

- <http://localhost:8080/stac/v1>
- <http://localhost:8080/data/v1>

Mosaic preview at http://localhost:8080/data/v1/mosaic/naip.2017/map/preview


## Build and Test

### Requirements

Most of the development environment runs through docker containers, so have the latest versions of docker and docker-compose installed. This project requires at least docker-compose v1.27+.

### Development environment setup

To setup your development environment, use

```
> scripts/setup
```

This will build the project docker images and ingest test data into the development database.

### Running build and test

To build the development containers for this project, use

```
> scripts/update
```

To run tests, use

```
> scripts/test
```

### Setting APP_ROOT_PATH

The environment variable `APP_ROOT_PATH` is used in the API services when using
behind a proxy with a stripped path prefix a la [this article](https://fastapi.tiangolo.com/advanced/behind-a-proxy/). This is set to the value the Nginx development server uses as a path prefix in the development environment, mimicing the target deployment environment.

## Notes for Open Sourcing

This section includes notes about what would have to change for the project to be open sourced. Please contribute!

- The Azure Pipelines states the subscription ID explicitly. If we are still deploying through the open source repo, and open the test deploy pipeline, we'd need to move this to a secret value.
