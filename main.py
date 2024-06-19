from cloud import CloudAPI
from device import Device
from remote import Remote
import database

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

    """
    TODO: we possibly also want to grab some current information about the
    software running in the system so we can filter against a specific release
    of Torizon.
    For example, the user may want to invoke the program passing a flag such as
    SOC_UDT="imx8m" TORIZON_VERSION="6.5.0" or TORIZON_VERSION="nightly".
    """
    possible_duts = []
    for device in cloud.provisioned_devices:
        if soc_udt in device["deviceId"]:
            possible_duts.append(device)

    for device in possible_duts:
        uuid = device["deviceUuid"]
        if not database.device_exists(uuid):
            database.create_device(uuid)
            logger.info(f"Created new device entry for {uuid}")

        if database.acquire_lock(uuid):
            logger.info(f"Lock acquired for device {uuid}")
            try:
                dut = Device(cloud, device["deviceUuid"], public_key)
                remote = Remote(dut, RAC_IP, device_password)
                if remote.test_connection():
                    logger.info(f"Connection test succeeded for device {uuid}")
                    remote.connection.run(
                        "docker run --privileged --pid host -v /var/run/docker.sock:/var/run/docker.sock -v /home/torizon:/home/torizon leonardoheldattoradex/hoop-target /suites/run-tests.sh --junit"
                    )
                    logger.info(f"Docker command executed for device {uuid}")
                    remote.connection.get(
                        "/home/torizon/report.xml", "report.xml"
                    )
                    logger.info(f"Report retrieved for device {uuid}")
                else:
                    logger.error(f"Connection test failed for device {uuid}")
            except Exception as e:
                logger.error(
                    f"An error occurred while processing device {uuid}: {e}"
                )
            finally:
                database.release_lock(uuid)
                logger.info(f"Lock released for device {uuid}")
        else:
            logger.info(f"Failed to acquire lock for device {uuid}")


if __name__ == "__main__":
    main()
