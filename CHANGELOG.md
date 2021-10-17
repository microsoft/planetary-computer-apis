# Change Log
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
### Added
- Add CHANGELOG based on [keepachangelog](https://keepachangelog.com/en/1.0.0/) format [#]()
- Add metrics dashboard for azure deployments [#364]()
- Add the ability to issue SAS tokens based on Storage Table entries [#466]()
- Add configuration to set API description [#478]()

### Changed
- Organize data endpoints under `item/` and `collection/` headings [#449]()
- Update conformance classes from 1.0.0-beta.2 to 1.0.0-beta.3 []()
- Upgrade STAC-FastApi to version 2.1.1 [#630]()

### Fixed
- Guard against low zoom levels on preview maps of deployed datasets [#450]()

## [1.1.0] - 2021-06-30
### Added
- Add ability to crop image according to POSTed polygonal boundaries [#347]()
- Add render parameters for other collections [#472]()
- Allow configuration to determine if a collection is shown and if links are injected [#472]()

### Changed
- Switch from sqlalchemy to pgstac backend [#390]()

### Fixed
- Include a workaround to stac-pydantic LandingPage error that is to be removed once 2.0.1 is released [#472]()
