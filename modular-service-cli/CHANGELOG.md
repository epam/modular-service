# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [3.0.1] - 2023-04-02
- add `modular-service signup` command

## [3.0.0] - 2023-03-04
- adapt responses parser to API v3
- add commands to create different types of applications
- remove `requests`, `PyYAML` from requirements
- refactor code

## [2.0.7] - 2023-12-19
- Update `policy add` to handle policy names in lower case, same logic are in
`policy delete`.

## [2.0.6] - 2023-12-04
- Update `modular_service` for compatibility with `modular-cli`
- Update library:
  - `certifi` from 2023.7.2 to 2023.11.17
- Rename root group name and filename from `modular_service` to `modularservice`
- Rename `version.py` to `__version__.py`
- Rename CLI module name to properly work with modular-api

## [2.0.0] - 2023-10-02
- Update libraries to support Python 3.10:
  - `certifi` from 2022.6.15 to 2023.7.2
  - `charset-normalizer` from  to 3.2.0
  - `idna` from 2.7 to 3.4
  - `PyYAML` from 5.4.1 to 6.0.1
  - `requests` from 2.25.1 to 2.31.0
  - `tabulate` from 0.8.9 to 0.9.0
  - `urllib3` from 1.26.15 to 1.26.16

## [1.0.0] - 2022-09-09
### Added
    - Initial release of Maestro Common Domain Model Module.

