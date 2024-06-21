from cloud import CloudAPI
from device import Device
from remote import Remote

import database
import common

import logging
import os
import sys
import argparse

RAC_IP = "ras.torizon.io"


def main():

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    parser = argparse.ArgumentParser(
        description="Run commands on remote devices provisioned on Torizon Cloud."
    )
    parser.add_argument(
        "--report",
        nargs=2,
        metavar=("remote-path", "local-output"),
        help="Copies a file over Remote Access from remote-path from the target device to local-output.",
    )
    parser.add_argument(
        "command", type=str, help="Command to run on target device."
    )

    args = parser.parse_args()

    test_whole_fleet = os.getenv("TEST_WHOLE_FLEET", "False")
    test_whole_fleet = test_whole_fleet.lower() in ["true"]

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
    logger.info(f"Finding possible devices to send tests to...")
    logger.info(f"Matching configuration: SOC {soc_udt}")
    possible_duts = []
    if test_whole_fleet:
        possible_duts = cloud.provisioned_devices
    else:
        for device in cloud.provisioned_devices:
            if soc_udt == common.parse_device_id(device["deviceId"]):
                possible_duts.append(device)

    if not possible_duts:
        logger.error("Couldn't find any possible devices to send tests to")
        sys.exit(1)
    else:
        logger.info("Found these devices to send tests to:")
        logger.info(possible_duts)

    logger.info("Attempting to lock a device")
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
                    remote.connection.run(args.command)
                    logger.info(f"Docker command executed for device {uuid}")
                    if args.report:
                        remote_path = args.report[0]
                        local_output = args.report[1]
                        logger.info(
                            f"Copying report file from {remote_path} to {local_output}"
                        )
                        remote.connection.get(remote_path, local_output)
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
            # found a matching device, locked it, tested, unlocked it...
            if not test_whole_fleet:
                sys.exit(0)
        else:
            logger.info(f"Failed to acquire lock for device {uuid}")

    if not test_whole_fleet:
        # EX_UNAVAILABLE 69	/* service unavailable */ sysexits.h
        sys.exit(69)


if __name__ == "__main__":
    main()
