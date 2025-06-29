# Geese

Because we are migrating goats.
This module allows interaction between Cribl environments.
The main commands are: `export`, `import`, `simulate`, `migrate`, `validate`, and `commit`.

## Status

### Releases

![snyk](https://github.com/aplura/cribl_geese/actions/workflows/snyk-scanning.yml/badge.svg?branch=main)
![testing](https://github.com/aplura/cribl_geese/actions/workflows/python-package.yml/badge.svg?branch=main)
![release](https://github.com/aplura/cribl_geese/actions/workflows/create-release.yml/badge.svg?branch=main)

### Next

![snyk](https://github.com/aplura/cribl_geese/actions/workflows/snyk-scanning.yml/badge.svg?branch=next)
![testing](https://github.com/aplura/cribl_geese/actions/workflows/python-package.yml/badge.svg?branch=next)

## TAKE THIS DOWN

> ℹ️ **_NOTE:_** There is *NO* `copy` feature.
> Configs will need exported, reviewed, and imported.
> This prevents "shot-gunning" bad, not needed, or incorrect configs between environments.
> Since this module is expected to be used "at scale", it will take some time and is not an "instant transfer".
> But it's much faster than clicking through the GUI multiple times to make the same config.

Expected order of operations:

1. Export the configs required
2. Review the configs to make sure they are accurate, and rename as needed.
    1. Update any that require secrets or other non-exportable configs.
3. Simulate the configs to check for and resolve conflicts.
4. Import the configs required.
5. Commit and deploy the groups required.
6. Migrate the workers <- `WORK IN PROGRESS` AND `EXPERIMENTAL`

## Known Issues

Please see: https://github.com/aplura/cribl_geese/issues for open issues.

## Release Notes

### v1.1.5

* API Spec Updates
    * Added `4.10.1` API Specification
    * Added `4.11.0`, `4.11.1` API Specification
    * Added `4.12.0`, `4.12.2` API Specification
    * Fixed bad Regex in API Specification to perform input validation.
        * See README.md in `geese/constants/api_specs`
* New Features
  * **Environment Variables in Config**
    * In `config.yaml`, or a user defined configuration file, each root level item (`username`, `password`, etc) can now include an environment variable.
    * The key is variable as the environment requires.
    * The variable must have a double `$$`
    * Example is below, where the key will be replaced according to the regex `$$\S+`.
    ```yaml
    destination:
      username: $CRIBL_LEADER_USERNAME
      password: $CRIBL_LEADER_PASSWORD
    ```
* Improvements
  * Export `ALL`
    * When working with geese, if a config source does not have the `worker_groups` configuration item, Cribl will be queried to determine available groups, and the entire set will be utilized for exporting.
    * Destinations without a `worker_groups` configuration item will default to the single group `default`. 

### v1.1.4

* Security Updates
    * Updated `urllib3` to v2.2.2 to address [CVE-2024-37891](https://www.cve.org/CVERecord?id=CVE-2024-37891)
    * Updated `setuptools` to `>=70.0.0`
* Bugs
    * Fixed `packs` export, configuration of the pack is now exported into the export config file.
    * Fixed group targeting in source and destination.
* Improvements
    * Across the board, reworked internal command switches to be more consistent.
* New Feature
    * When uploading packs, the option to include a custom "pack" called a "ruck" is available.
        * "kits" allow a more-comprehensive approach to packs, as they can include `collectors`, `inputs`, `secrets` and
          a default route that funnels matching data to the pack.
        * The pack itself will still only contain pack routes, pipelines, and other knowledge settings, but other
          objects will be created if defined.
    * Added configuration option `is_free` for standalone or not Enterprise editions of Cribl.
    * Added `create` command for future use.
    * Restrict to specific sources/destinations using `namespaces`.
* Export
    * Ability to export a lookup file (CSV) of Cribl Ids and Display names for further enrichments.
    * Added ability to "split" configs into their knowledge objects with group and namespace information.
* Validate
    * Added multiple API Specs
    * Still not working as intended due to malformed OpenAPI spec parsing.
* Knowledge Objects
    * `routes`
        * Fixed the update call to "substitute and replace" only configured routes. Will not overwrite entire route
          list.

### v1.1.3

* Improvements
    * Updated README for links to releases.
    * Included Snyk Scanning
    * Now supports Environment variables for authentication
* New Knowledge Objects
    * Supports CriblSearch knowledge objects

### v1.1.2

* Initial Release

## LICENSE

The MIT License (MIT)

Copyright © 2024 Aplura, LLC

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
documentation files (the “Software”), to deal in the Software without restriction, including without limitation the
rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit
persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the
Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

## Download

Download the latest sdist/whl from https://github.com/aplura/cribl_geese/releases/latest .
This file will be used in the installation and upgrade sections with the pip command.

## Install

From the command line, run this, changing `pip3` if required for your environment.

    pip3 install ./geese-1.1.5.tar.gz

## Upgrade

    pip3 install --upgrade ./geese-1.1.5.tar.gz

## Usage

For all commands, the `-h` will display relevant information about the command and flags possible for configuration.

### config.yaml

For all instances of the command, there should be a `config.yaml` that has the sources and destinations.
This file can have different names, and is set using the `--config-file` flag.
The default value is `./config.yaml`.
`import`, `simulate`, and `commit` require a destination.
Only one destination is supported.
`export` requires source(s).
Multiple sources are supported.

| :memo: | The `client_id`, `client_secret`, `username`, and `password` fields support environment variables. Simply replace the value of the key in `config.yaml` with the name of the environment variable (e.g. `CRIBL_SRC_1`) and have the environment variable available. |
|--------|:--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|

```yaml
# Sources: Array of items
source:
  - is_cloud: (true|false) # Optional, default: false
    enabled: (true|false) # Optional, default: true
    verify_ssl: (true|false) # Optional, default: false
    namespace: <string> # Optional, use in conjunction with --use-namespace
    url: "https?://<your_instance>" # Required, http OR https are supported
    username: <username> # Required, if no `client_id`
    password: <password> # Required, if no `client_secret`
    client_id: <client_id> # Required, if no `username`
    client_secret: <client_secret> # Required, if no `password`
    worker_groups: # Optional.
      - default
# Destination: Single Object
destination:
  is_cloud: (true|false) # Optional, default: false
  enabled: (true|false) # Optional, default: true
  verify_ssl: (true|false) # Optional, default: false
  url: "https?://<your_instance>" # Required, http OR https are supported
  username: <username> # Required, if no `client_id`
  password: <password> # Required, if no `client_secret`
  client_id: <client_id> # Required, if no `username`
  client_secret: <client_secret> # Required, if no `password`
  worker_groups: # Optional.
    - default
```

> ℹ️ **_NOTE:_** `worker_groups` will allow the same configurations to be exported and imported to those groups.
> There are several locations within an import yaml that can determine the worker group the config is placed into.
> 1. `config.yaml`, as a child under a source or destination.
> 2. As an attribute of an object configuration
> 3. As an attribute of an attribute `conf` of an object configuration
>

### tuning.yaml

This is set using `--tune-ids`, and is a path with filename.
It is used to implicitly include, or implicitly exclude different Cribl knowledge objects, based on their Cribl ID.
`include` will override `exclude`.

| Parent Key                    | Meaning                                                                                                      |
|-------------------------------|--------------------------------------------------------------------------------------------------------------|
| `universal`                   | This applies to every item that is processed.                                                                |
| `knowledge_objects`           | This only applies at the "entire object" level. <br/>All configs under that object will be included/excluded |
| `<cribl_knowledge_object_id>` | These apply to specific knowledge objects only. Examples are: `pipelines`, `inputs`, and `packs`             |
| `<attribute>`                 | This is the json/yaml attribute of the object. An example is `id` or `lib`                                   |
| `<id>`                        | This is the value of the `<attribute>` to include/exclude                                                    |

```yaml
exclude:
  universal:
    <attribute>:
      - <id>
  knowledge_objects:
    - <cribl_knowledge_object_id>
  <cribl_knowledge_object_id>:
    <attribute>:
      - <id>
include:
# The Same Structure as "exclude".
```

Example:

```yaml
exclude:
  universal:
    lib:
      - cribl
    id:
      - default
    disabled:
      - true
  knowledge_objects:
    - auth_config
    - lookups
    - packs
  packs:
    id:
      - HelloPacks
      - Testing

```

## Export

This exports specified configs from the `source` Cribl environments.
The available options are shown using: `geese export -h`.

    geese export --all-objects

If an object does not have a recognized "id", a warning will be generated, and you can find the item in the config using
`(<worker_group>|<namespace>)-unknown_id`.

### Namespace

This allows for multiple sources with same named worker groups.
Use a namespace to differentiate the configs, otherwise they will be merged in the final export with any conflicts
renamed.

If `--use-namespace` is set, the export will have an additional level in the configs.

    ---
    <namespace>:
      <worker_group>:
         <cribl_knowledge_object_id>:
            <...configs>

Otherwise, the export structure is:

    ---
    <worker_group>:
         <cribl_knowledge_object_id>:
            <...configs>

## Import

> ℹ️ **_NOTE:_** Currently, import will only check the last high level configuration set in the export file.
> Multiple groups (at the highest level) is not supported.
> If you want to import against multiple worker groups, update the configurations to have a `worker_groups` array with the
> specified worker groups.

Here, if `--use-namespace` is set, then any conflicted items will use their 'namespaced' id, and not the Cribl
configured ID.

## Simulate

> ℹ️ **_NOTE:_**  Currently, simulate will only check the last high level configuration set in the export file.
> Multiple groups (at the highest level) is not supported.
> If you want to simulate against multiple worker groups, update the configurations to have a `worker_groups` array with
> the specified worker groups.

Here, if `--use-namespace` is set, then any conflicted items will use their 'namespaced' id, and not the Cribl
configured ID.

## Commit

geese can be used to commit and deploy groups via command line.
If `--groups` is not set, it will assume "single instance" and not distributed.

    geese commit --deploy

    or

    geese commit --deploy --groups <group1> <group2> --commit-message "I did it on the CLI"

## Validate

    geese validate --all-objects --directory <directory_of_configs> [--split] [--errors-only] [--api-version 4.11.0]

## Migrate

> ⚠️ **_IMPORTANT:_** EXPERIMENTAL AND NOT YET TESTED. EXPERIMENT ON YOUR OWN. ⚠️

This migrates workers from old leaders to new leaders.

    geese migrate --guids <list of guids> --new-group <destination_group> --auto-restart