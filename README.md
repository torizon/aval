# AVAL
Aval is a remote command executor targeting systems that can be provisioned on Torizon Cloud.

More specifically, Aval is used to initialize remote testing frameworks such as bats-core inside a given target and receive back one or more `report.xml` junit files, aka test results.

Aval is meant to be used either locally or from a CI pipeline.

## Usage

Copied straight from `python3 main.py --help`.

```
usage: main.py [-h] [--copy-artifact remote-path [local-output ...]] [--before BEFORE] [--delegation-config DELEGATION_CONFIG] [--device-config DEVICE_CONFIG] [--run-before-on-host RUN_BEFORE_ON_HOST]
               [command]

Run commands on remote devices provisioned on Torizon Cloud.

positional arguments:
  command               Command to run on target device.

options:
  -h, --help            show this help message and exit
  --copy-artifact remote-path [local-output ...]
                        Copies multiple files over Remote Access from the target device to local-output. Specify pairs of remote-path and local-output.
  --before BEFORE       Command to run before the main command on target device.
  --delegation-config DELEGATION_CONFIG
                        Path of config which tells Aval how to parse the target delegation.
  --device-config DEVICE_CONFIG
                        Path of config which tells Aval which device to match.
  --run-before-on-host RUN_BEFORE_ON_HOST
                        Path of a file to be executed on the host system running Aval before running the main command in the DUT
```

## Network Information

Network information is always written to a file on the local folder called `device_information.json`. When used in combination with `--run-before-on-host`, this provides an alternative way to connect to the device from a script on the host computer using the data from the json network information file.

This allows integration with tests being run outside of the scope of Aval, such as integration tests between a host computer and the board. Note that you'll need to handle the SSH session on your own on this case.

This option mainly exists to use Aval for the TCB/IDE tests.

## Example

An example can be found in the `meta-e2e-tests` folder.

We have our test paylod (a container built from `meta-e2e-tests/Dockerfile`) that includes the bats-core framework. Test suites can be included in `example/suites` and for now we provide `example/suites/meta`, which contains two tests - one passing and one failing.

`meta-e2e-tests/run-tests.sh` is a bash script that invokes the suite and returns a `report.xml` in the `/home/torizon` folder inside the container, which will be a shared volume with the hosts (that's how Aval gets the junit xml back).

One interesting aspect is that Aval uses `fabric`, which echoes back the test runs, so one has real-time information about the test run.

For more information check the `main.py` file and `.gitlab-ci.yml`.

## Developing 

First, fill in the information from the provided `.env.template` into a new `.env` file.

The easiest way to develop is setting up a mountpoint inside the Python container like so

```
$ docker run -it -v $(pwd):/aval --workdir=/aval python:latest bash
# make install
# make test
# make format
```

To run a test (echo Hello) on a provisioned Apalis iMX8 QuadMax
```
# eval $(cat .env) && SOC_UDT="apalis-imx8qm" python main.py --delegation-config delegation_config.toml "echo Hello"`
```

## Aval's Database

Aval uses Postgres as a locking mechanism. In the future we may also opt to use it to gather testing statistics.

The idea behind it is exploiting transaction atomicity for database operations, abusing it as a lock.

## Using it in CI

We have end-to-end tests that mimic exactly how you should run this in CI. Please take a look at the `.gitlab-ci.yml` and `.e2e-tests.yml` files.

Note: if you're using RAC for remote access (`USE_RAC=true`), you must have the IP of the CI runner whitelisted on Torizon Cloud, under Remote Access settings, otherwise the IP will be soft-banned and automatically return a 400 error when opening a new session.

## Property-based Filtering

Aval can filter by SoC properties such as if it has a VPU, NPU or any other peripheral. The basic idea is we describe the features we want when issuing a test
through a toml file (see [the a description of Verdin iMX8 with NPU](./verdin-imx8mpq-npu.toml)) and Aval holds a source-of-truth based on the PID4 (Product ID)
for a every possible board (see the [pid_mal.yaml file](./pid_map.yaml)). Aval will then automatically match properties and match against a provisioned
device with those properties by its PID4 stored in the `notes` field of Torizon Cloud.

For an example, check the [e2e-tests](./e2e-tests.yml) file. Currently supported properties can be examined in the [pid_mal.yaml file](./pid_map.yaml).

## Architecture-based Filtering

If you don't care for a particular device, invoking Aval with just a `SOC_ARCHITECTURE=<arm|arm64|...>` will simply lock
the first device of that architecture.

## Device Information

For each locked device, Aval will output a `device_information.json` file to the current directory. The workflow here
is that one can use this information together with `--run-before-on-host` to execute scripts that already manage an
SSH connection and "bypass" Aval, utilizing it solely as a board manager. An example of such script can be found in
the [host_command.sh file](./host_command.sh) and the flag usage can be observed in the [e2e-tests](.e2e-tests.yml) file. 

## Contributing

`TODO`s and `FIXME`s are probably scattered around the code, please grep for that.

## Credits

The core classes of Aval are based off Eduardo's A/B to Torizon OS migration script, albeit with significant changes.

The hardware setup that Aval is developed upon and used to run hundreds of tests each day was created by Lucas Bernardes, with 3D models available for download [here](https://github.com/torizon/modular-rack-toradex).
