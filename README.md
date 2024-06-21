# AVAL
Aval is a remote command executor targeting systems that can be provisioned on Torizon Cloud.

More specifically, Aval is used to initialize remote testing frameworks such as bats-core inside a given target and receive back one or more `report.xml` junit files, aka test results.

Aval is meant to be used either locally or from a CI pipeline.

## Usage

Copied straight from `python3 main.py --help`.

```
usage: main.py [-h] [--report remote-path local-output] command

Run commands on remote devices provisioned on Torizon Cloud.

positional arguments:
  command               Command to run on target device.

options:
  -h, --help            show this help message and exit
  --report remote-path local-output
                        Copies a file over Remote Access from remote-path from the target device to local-output.
```

## Example

An example can be found in the `meta-e2e-tests` folder.

We have our test paylod (a container built from `meta-e2e-tests/Dockerfile`) that includes the bats-core framework. Test suites can be included in `example/suites` and for now we provide `example/suites/meta`, which contains two tests - one passing and one failing.

`meta-e2e-tests/run-tests.sh` is a bash script that invokes the suite and returns a `report.xml` in the `/home/torizon` folder inside the container, which will be a shared volume with the hosts (that's how Aval gets the junit xml back).

One interesting aspect is that Aval uses `fabric`, which echoes back the test runs, so one has real-time information about the test run.

For more information check the `main.py` file and `.gitlab-ci.yml`.

## Running it locally

The easiest way to try it is using the provided `docker-compose.yml`.
You'll need a `.env` file as well, which can be created from the `.env.template` file.

An explanation of each variable follows:

- `POSTGRES_DB` is the name of the database. Defaults to `aval`.
- `POSTGRES_HOST` is the IP of where the Postgres service is running. Defaults to `aval_postgres`, the same name of the service in `docker-compose.yml`.
- `POSTGRES_PORT` is the database server port. Defaults to `5432`
- `POSTGRES_USER` is the user used to login/authenticate into Postgres.
- `POSTGRES_PASSWORD` is the password for `POSTGRES_USER`.
- `PGADMIN_DEFAULT_EMAIL` is the default login e-mail for pgadmin (frontend for Postgres).
- `PGADMIN_DEFAULT_PASSWORD` is the default password for pgadmin.
- `TORIZON_API_CLIENT_ID` and `TORIZON_API_SECRET_ID` can be obtained using the Torizon Cloud UI.
- `PUBLIC_KEY`, `PRIVATE_KEY` are the ones registered in the Torizon Cloud.
- `DEVICE_PASSWORD` is the actual device password for the devices. We do not support having different password for each of the devices.
- `SOC_UDT` (System-on-Chip Under Test) is a variable to match against the `Device ID` field under the Device Information tab under the Hardware section. As an example, a provisioned device with `Device ID: apalis-imx8-14724532-f2b9cb` will match against `SOC_UDT=imx8`.

Then just `docker-compose up --build`.

## Developing 

To run the unit tests, you can do it locally or also use the container using `coverage`, overriding the entrypoint:

```
docker run --entrypoint coverage aval run -m unittest discover -v -s . -p 'test_*.py'
```

Possibly useful commands to run it locally:

```
# exports variables from `.env` and runs the aval, assuming that the database is up
env $(cat .env | xargs) python3 main.py ...
```

## Aval's Database

Aval uses Postgres as a locking mechanism. In the future we may also opt to use it to gather testing statistics.

The idea behind it is exploiting transaction atomicity for database operations, abusing it as a lock.

## Using it in CI

Note: you must have the IP of the CI runner whitelisted on Torizon Cloud, under Remote Access settings, otherwise the IP will be soft-banned and automatically return a 400 error when opening a new session.

## Missing features
 - Merge multiple junit files into one `report.xml`
 - Missing documentation about how to use it in CI
 - Missing documentation about how to use mountpoints with the source code to make development easier
 - Source and test code is not split at all at this moment, would be a very nice to have

Other `TODO`s and `FIXME`s are probably in the code as well, so if you wanna fix something outright, just grep for that.

## Credits

The core classes of Aval are based off Eduardo's A/B to Torizon OS migration script, albeit with significant changes.