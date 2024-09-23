# How to store the device's PID on Torizon Cloud

We need to store the device's PID on Torizon Cloud so we can use it later. The
main idea is to be able to set a filter to select a specific set of Devices
Under Test (DUT) to run the test suite.

## Getting the PID od a device

Using the device, the easiest way is:

```bash
cat /proc/device-tree/toradex,product-id
```

Another one is to [query Toradex's
website](https://www.toradex.com/pt-br/util/invent-serial-box) (login required)
with the device's serial number.

## Storing the PID on Torizon Cloud

Currently, Torizon Cloud has no other way to store this info than use the notes
field. There are a few ways to get the information in there.

The easiest from the user's perspective is to open [Torizon Cloud's management
interface](app.torizon.io/), go to a device and change its `Description` field.

Another way is to use Torizon Cloud's APIv2. For that, you can follow the
[developer's website
turorial](https://developer.toradex.com/torizon/torizon-platform/torizon-api)
to get a token and then:

- Create an APIv2 token on the management interface;
- Get a Bearer token via the API:
```bash
curl -X POST \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "grant_type=client_credentials&client_id=<yourClientId>&client_secret=<yourClientSecret>" \
     https://kc.torizon.io/auth/realms/ota-users/protocol/openid-connect/token
```
- Use the API to PUT the PID in the `notes` field:
```bash
curl -X 'PUT' \
  'https://app.torizon.io/api/v2beta/devices/notes/<device-uuid>' \
  -H 'accept: */*' \
  -H 'Authorization: Bearer <bearer-token>' \
  -H 'Content-Type: application/json' \
  -d '"<device-pid>"'
```

## Using our forked version of provision-device.sh

We do have a forked version of Torizon Cloud's `provision-device.sh` script and
it can be used to provision the device storing the PID in the `notes` field
automatically. It also allows one to set a custom PID via the `-i <PID>` option.

To use it, use the provided command line from Torizon Cloud, but change the URL
of the `curl` command to a link to our forked script.
