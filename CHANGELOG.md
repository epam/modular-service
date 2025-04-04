# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [3.3.0] - 2025-03-06
- updated modular-sdk to 7.0.0
- added helm command to Makefile
- updated helm charts to use modular-sdk 7.x's envs
- removed python-dotenv
- updated requirements management to `uv`


## [3.2.0] - 2024-07-31
- added endpoint for health check
- added cli command to activate all global regions
- refactored cognito client
- added rest api endpoints to manage users
- changed logs format and configuration a bit

## [3.1.0] - 2024-05-24
- added a new endpoint to change your password

## [3.0.3] - 2024-05-09
- write logs to stderr instead of stdout
- add an ability to specify system user password for `python main.py init`

## [3.0.2] - 2024-04-02
- restrict symbols that are allowed by password generator

## [3.0.1] - 2024-03-29
- added refresh token support


## [3.0.0] - 2024-03-13
### Added
- Global validation using Pydantic v2
- Swagger for ON-prem and deployment-resources generator from inner endpoints collection. Request and response models 
  for each endpoint. Added openapi v3 spec generator
- Authentication to ON-prem
- Customer scope for users. Now there are two types of users: system user and standard user. Standard users can 
  perform actions only for their customers. System users can perform actions on behalf of other customers
- added pagination to all the endpoints that do query
- entrypoint main.py script with some useful actions
- added endpoints for creating different types of applications: AWS_ROLE, AWS_CREDENTIALS, etc
- added minimal unittests


### Changed
- moved to python3.10
- moved to latest modular-sdk (5.1.1)
- changed API responses. In case api return one object the response json looks like this: `{"data": {...}}`, i.e 
  `data` with one object instead of a list with one object
- moved all logically connected constants to enums: Permission, Endpoints, Envs.
- Added uppercase names for existing envs
- changed some endpoints (see swagger for the current list of available endpoints)


### Removed
- removed all not used code & requirements & constants
- removed `Settings` model because it was useless

## [2.1.0] - 2024-01-31
- Add `logs_expiration` attribute for `modular_api_handler` lambda in 
lambda config

## [2.0.6] - 2024-01-24
- Add application_id GSI to Parent dynamoDB table meta

## [2.0.5] - 2023-12-08
- Rename:
  - `ModularRoles` to `ModularServiceRoles`,
  - `ModularPolicies` to `ModularServicePolicies`,
  - `ModularSettings` to `ModularServiceSettings`
- Add in `deployment_resources.json`:
  - `ModularAudit`, `ModularJobs`, `ModularGroup`, `ModularUser`, `ModularPolicy` 

## [2.0.4] - 2023-11-09
- Updated the project to enable Role-Based Access Control (RBAC)

## [2.0.3] - 2023-11-02
- Update libraries:
  - `Deprecated` from 1.2.13 to 1.2.14
  - `jwcrypto` from 1.3.1 to 1.4.2

## [2.0.2] - 2023-10-26
- Fix typo in `setup.py` entry point
- Add `modular-sdk` to `setup.py`
- Fix imports
- Update library `charset-normalizer` from 3.2.0 to 3.3.1

## [2.0.1] - 2023-10-26
- Migrate to `modular_sdk` version 3.3.2
- Fix typo `from modular_sdk.modular import Modular`

## [2.0.0] - 2023-10-02
- Update libraries to support Python 3.10:
  - `bcrypt` from 4.0.0 to 4.0.1
  - `boto3` from 1.24.84 to 1.26.80
  - `botocore` from 1.27.91 to 1.29.80
  - `bottle` from 0.12.23 to 0.12.25
  - `certifi` from 2022.6.15 to 2023.7.22
  - `charset-normalizer` from 2.0.12 to 3.2.0
  - `colorama` from 0.4.1 to 0.4.5
  - `configobj` from 5.0.6 to 5.0.8
  - `cryptography` from 3.4.7 to 41.0.3
  - `hvac` from 0.11.2 to 1.2.1
  - `idna` from 3.3 to 3.4
  - `pymongo` from 3.12.0 to 4.5.0
  - `pynamodb` from 5.2.1 to 5.3.2
  - `PyYAML` from 5.4 to 6.0.1
  - `requests` from 2.27.1 to 2.31.0
  - `s3transfer` from 0.6.0 to 0.6.2
  - `simplejson` from 3.17.6 to 3.19.1
  - `tabulate` from 0.8.9 to 0.9.0
  - `tqdm` from 4.19.5 to 4.65.2
  - `urllib3` from 1.26.12 to 1.26.16
  - `wrapt` from 1.14.1 to 1.15.0
  - `typing_extensions` from 4.3.0 to 4.7.1
  - `modular-sdk` from 2.1.4 to 3.x.x

## [1.2.0] - 2023-05-09
- defined extended versions of modular services

## [1.1.0] - 2023-03-05
- refactored all the code, removed excessive code
- added on-prem
- fixes some bugs
- moved to lambda-proxy-integration

## [1.0.0] - 2022-09-14
### Added
    -  Initial version of the service.

