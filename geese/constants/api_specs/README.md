# Location of API Specs

https://docs.cribl.io/api/

Grab the latest yml, or select the version required, and download that

# UPDATE TO NEWLY DOWNLOADED SPECS.

There is an error in the API specs.

Search for `^[a-zA-Z0-9_-\s]+$` as a non-regex string and update it to `^[a-zA-Z0-9_\-\s]+$` to work with the OpenAPI python package.

The offender is: `components.schemas.InputWiz.properties.contentConfig.items.properties.contentType.pattern`