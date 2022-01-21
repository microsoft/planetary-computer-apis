# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

### Added

### Fixed

## [2022.1.1]

### Fixed

- Fixed conformance classes [#39](https://github.com/microsoft/planetary-computer-apis/pull/39)
- Fixed STAC API version in API documentation [#39](https://github.com/microsoft/planetary-computer-apis/pull/39)

## [2022.1.0]

### Changed

- Upgraded stac-fastapi and pgstac versions to bring support for CQL2-JSON filter support [#20](https://github.com/microsoft/planetary-computer-apis/pull/20)
- Organized and updated documentation markdown docs [#11](https://github.com/microsoft/planetary-computer-apis/pull/11)
- Upgraded TiTiler to 0.4, includes changes to tile parameters [#22](https://github.com/microsoft/planetary-computer-apis/pull/22)
- Improved access logging [#23](https://github.com/microsoft/planetary-computer-apis/pull/23)
- Allow SAS URL variable to be passed to PC SDK in tiler service [#33](https://github.com/microsoft/planetary-computer-apis/pull/33)
- Upgrade to stac-fastapi 2.3.0 [#35](https://github.com/microsoft/planetary-computer-apis/pull/35)

### Added

- Errors are logged using exceptions and including request metadata [#14](https://github.com/microsoft/planetary-computer-apis/pull/14)
- Added endpoints to generate legends from colormap or registered classmaps [#17](https://github.com/microsoft/planetary-computer-apis/pull/17)
- Configuration for chloris-biomass, nrcan-landcover, noaa-c-cap
- Configuration for io-lulc-9-class [#34](https://github.com/microsoft/planetary-computer-apis/pull/34)
- Configuration for gnatsgo [#36](https://github.com/microsoft/planetary-computer-apis/pull/36)

### Fixed

- Updated search limit constraints to avoid 500s [#15](https://github.com/microsoft/planetary-computer-apis/pull/15)
- Fixed STAC `describedby` and `preview` links [#33](https://github.com/microsoft/planetary-computer-apis/pull/33)
- Default search limit restored to 250 [#36](https://github.com/microsoft/planetary-computer-apis/pull/36)
- Work around issue with LandPage stac_extensions [#37](https://github.com/microsoft/planetary-computer-apis/pull/37)