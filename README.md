# AVAL
Aval is a remote command executor targeting systems that can be provisioned on Torizon Cloud.

More specifically, Aval is used to initialize remote testing frameworks such as bats-core inside a given target and receive back one or more `report.xml` junit files, aka test results.

Aval is meant to be used either locally or from a CI pipeline.

## Example

An example can be found in the `example` folder.

We have our test paylod (a container built from `example/Dockerfile`) that includes the bats-core framework. Test suites can be included in `example/suites` and for now we provide `example/suites/meta`, which contains two tests - one passing and one failing. 

`examples/run-tests.sh` is a bash script that invokes the suite and returns a `report.xml` in the `/home/torizon` folder inside the container, which will be a shared volume with the hosts (that's how Aval gets the junit xml back).

One interesting aspect is that Aval uses `fabric`, which echoes back the test runs, so one has real-time information about the test run.

For more information check the `main.py` file and `.gitlab-ci.yml`.

## Developing
Install dependencies with `pip install -r requirements.txt` and export the following environment variables:
```
TORIZON_API_CLIENT_ID
TORIZON_API_SECRET_ID
PUBLIC_KEY
DEVICE_PASSWORD
SOC_UDT
```

Or build and run the container with those environment variables exported

```
docker build -t aval .
docker run -it -e TORIZON_API_CLIENT_ID=<...> <...> python3 main.py
```

`SOC_UDT` (System-on-Chip Under Test) is a variable to match against the `Device ID` field under the Device Information tab under the Hardware section. 

As an example, a provisioned device with `Device ID: apalis-imx8-14724532-f2b9cb` will match against `SOC_UDT=imx8`.

`TORIZON_API_CLIENT_ID` and `TORIZON_API_SECRET_ID` can be obtained using the Torizon Cloud UI.

You'll also need to have a private key registered with your ssh-agent.

To run the unit tests, you can do it locally or also use the container using `coverage`:

```
docker run aval coverage run -m unittest discover -v -s . -p 'test_*.py'
```

## Using it in CI

You must have the IP of the CI runner whitelisted on Torizon Cloud, under Remote Access settings, otherwise the IP will be soft-banned and automatically return a 400 error when opening a new session.

## Missing features
 - merge multiple junit files into one `report.xml`
 - synchronization mechanism (ie, implementing a lock with states like `AVAILABLE`, `RUNNING`, `OFFLINE` etc.
 - supporting multiple `SOC_UDT` (if synchronization is implemented this is also solved)

## Credits

The core classes of Aval are based off Eduardo's A/B to Torizon OS migration script, albeit with significant changes.