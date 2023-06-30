# CLI for Modular Service

## Install

    pip install modularadmin

## Configure user credentials

    modularadmin configure --api_link <API_LINK>

    modularadmin login --username <username> --password <password>

## Commands

### Commands

[`login`](#login) - Authenticates user to work with modularadmin.

[`configure`](#configure) - Configures modularadmin tool to work with modularadmin.

[`cleanup`](#cleanup) - Removes all the configuration data related to the tool.

### Command groups

[`customer`](#customer) - Manages Customer Entity

[`application`](#application) - Manages Application Entity

[`parent`](#parent) - Manages Parent Entity

[`tenant`](#tenant) - Manages Tenant Entity

[`region`](#region) - Manages Region Entity

[`tenant_region`](#tenant_region) - Manages Tenant regions

[`role`](#role) - Manages Role Entity

[`policy`](#policy) - Manages Policy Entity

## Commands

### login

**Usage:**

    modularadmin login --username USERNAME --password PASSWORD

_Authenticates user to work with modularadmin. Pay attention that, the password can be
entered in an interactive mode_

`-u,--username` `TEXT` modularadmin user username. [Required]

`-p,--password` `TEXT` modularadmin user password. [Required]

### configure

**Usage:**

    modularadmin configure --api_link <modularadmin_API_LINK>

_Configures modularadmin cli tool to work Maestro Common Domain Model API._

`-api,--api_link` `TEXT` Link to the modularadmin host. [Required]

### cleanup

**Usage:**

    modularadmin cleanup

_Removes all the configuration data related to the tool._

## Command groups

----------------------------------------

### `customer`

**Usage:** `modularadmin customer  COMMAND [ARGS]...`

_Manages Customer Entity_

### Commands

[`add`](#customer-add) Creates Customer entity.

[`describe`](#customer-describe) Describes Customer entities.

[`update`](#customer-update) Updates Customer entity.

### `application`

**Usage:** `modularadmin application  COMMAND [ARGS]...`

_Manages Application Entity_

### Commands

[`add`](#application-add) Creates Application entity.

[`describe`](#application-describe) Describes Application entities.

[`deactivate`](#application-deactivate) Deactivates Application entity.

[`update`](#application-update) Updates Application entity.

### `parent`

**Usage:** `modularadmin parent  COMMAND [ARGS]...`

_Manages Parent Entity_

### Commands

[`add`](#parent-add) Creates Parent entity.

[`describe`](#parent-describe) Describes Parent entities.

[`deactivate`](#parent-deactivate) Deactivates Parent entity.

[`update`](#parent-update) Updates Parent entity.

### `tenant`

**Usage:** `modularadmin tenant  COMMAND [ARGS]...`

_Manages Tenant Entity_

### Commands

[`add`](#tenant-activate) Creates Tenant entity.

[`describe`](#tenant-describe) Describes Tenant entities.

[`deactivate`](#tenant-deactivate) Deactivates Tenant entity.

### `tenant_region`

**Usage:** `modularadmin tenant region COMMAND [ARGS]...`

_Manages Tenant Entity_

### Commands

[`activate`](#tenant-region-activate) Creates region in tenant.

[`describe`](#tenant-region-describe) Describes tenant regions.

[`deactivate`](#tenant-region-deactivate) Deactivates region in tenant.

### `policy`

**Usage:** `modularadmin policy COMMAND [ARGS]...`

_Manages modularadmin policy Entity_

### Commands

[`add`](#policy-add) Creates Policy entity.

[`delete`](#policy-delete) Deletes Policy by the provided name.

[`describe`](#policy-describe) Describes Policy entities.

[`update`](#policy-update) Updates Policy entity.

### `role`

**Usage:** `modularadmin role COMMAND [ARGS]...`

_Manages modularadmin role Entity_

### Commands

[`add`](#role-add) Creates Role entity.

[`delete`](#role-delete) Deletes Role by the provided name.

[`describe`](#role-describe) Describes Role entities.

[`update`](#role-update) Updates Role entity.


------------------------------------------------------------------------------