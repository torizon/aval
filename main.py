from cloud import CloudAPI
from device import Device
from remote import Remote

import logging
import os

RAC_IP = "ras.torizon.io"


def main():

    logger = logging.getLogger(__name__)

    try:
        api_client = os.environ["TORIZON_API_CLIENT_ID"]
        api_secret = os.environ["TORIZON_API_SECRET_ID"]
        public_key = os.environ["PUBLIC_KEY"]
        device_password = os.environ["DEVICE_PASSWORD"]
        soc_udt = os.environ["SOC_UDT"]
    except KeyError as e:
        raise KeyError(f"Missing environment variable: {e}")

    cloud = CloudAPI(api_client=api_client, api_secret=api_secret)

    for device in cloud.provisioned_devices:
        if soc_udt in device["deviceId"]:
            dut = Device(cloud, device["deviceUuid"], public_key)
        else:
            logger.error("No available device on the fleet to send tests to")

    remote = Remote(dut, RAC_IP, device_password)
    if remote.test_connection():
        remote.connection.run(
            "docker run --privileged --pid host -v /var/run/docker.sock:/var/run/docker.sock -v /home/torizon:/home/torizon leonardoheldattoradex/hoop-target /suites/run-tests.sh --junit"
        )
        remote.connection.get("/home/torizon/report.xml", "report.xml")
    else:
        # TODO: checking if the device is online is a better solution
        logger.error("Connection test failed")


if __name__ == "__main__":
    main()
