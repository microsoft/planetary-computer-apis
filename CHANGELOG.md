# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
### Changed
- Upgraded stac-fastapi and pgstac versions to bring support for CQL2-JSON filter support [#20](https://github.com/microsoft/planetary-computer-apis/pull/20)
- Organized and updated documentation markdown docs [#11](https://github.com/microsoft/planetary-computer-apis/pull/11)
- Allow SAS URL variable to be passed to PC SDK in tiler service [#33](https://github.com/microsoft/planetary-computer-apis/pull/33)

### Added
- Errors are logged using exceptions and including request metadata [#14](https://github.com/microsoft/planetary-computer-apis/pull/14)
### Fixed
- Updated search limit constraints to avoid 500s [#15](https://github.com/microsoft/planetary-computer-apis/pull/15)
- Fixed STAC `describedby` and `preview` links [#33](https://github.com/microsoft/planetary-computer-apis/pull/33)
