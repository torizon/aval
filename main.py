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
    if os.getenv("AVAL_VERBOSE"):
        logging_level = logging.DEBUG
    else:
        logging_level = logging.INFO

    logging.basicConfig(
        level=logging_level,
        format="%(levelname)s - %(asctime)s - File: %(filename)s, Line: %(lineno)d -  %(message)s",
        datefmt="%H:%M:%S",
    )

    logger = logging.getLogger(__name__)

    parser = argparse.ArgumentParser(
        description="Run commands on remote devices provisioned on Torizon Cloud."
    )
    parser.add_argument(
        "--copy-artifact",
        nargs="+",
        metavar=("remote-path", "local-output"),
        help="Copies multiple files over Remote Access from the target device to local-output. Specify pairs of remote-path and local-output.",
    )
    parser.add_argument(
        "command", type=str, help="Command to run on target device."
    )

    parser.add_argument(
        "--before",
        type=str,
        help="Command to run before the main command on target device.",
    )

    parser.add_argument(
        "--delegation-config",
        type=str,
        help="Path of config which tells Aval how to parse the target delegation.",
    )

    args = parser.parse_args()

    test_whole_fleet = os.getenv("TEST_WHOLE_FLEET", "False")
    test_whole_fleet = test_whole_fleet.lower() in ["true"]

    use_rac = os.getenv("USE_RAC", "False")
    use_rac = use_rac.lower() in ["true"]

    try:
        api_client = os.environ["TORIZON_API_CLIENT_ID"]
        api_secret = os.environ["TORIZON_API_SECRET_ID"]
        public_key = os.environ["PUBLIC_KEY"]
        device_password = os.environ["DEVICE_PASSWORD"]
        soc_udt = os.environ["SOC_UDT"]
        target_build_type = os.environ["TARGET_BUILD_TYPE"]
    except KeyError as e:
        raise KeyError(f"Missing environment variable: {e}")

    if args.delegation_config:
        cloud = CloudAPI(
            api_client=api_client,
            api_secret=api_secret,
            delegation_config_path=args.delegation_config,
        )
    else:
        logger.error("Missing delegation config file")
        sys.exit(1)

    logger.info(f"Finding possible devices to send tests to...")
    logger.info(
        f"Matching configuration: SOC {soc_udt}, BUILD TYPE {target_build_type}"
    )
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
        logger.info(common.pretty_print_devices(possible_duts))

    logger.info("Attempting to lock a device")
    for device in possible_duts:
        uuid = device["deviceUuid"]
        hardware_id = common.parse_hardware_id(device["deviceId"])
        if not database.device_exists(uuid):
            database.create_device(uuid)
            logger.info(f"Created new device entry for {uuid}")

        if database.try_until_locked(uuid):
            logger.info(f"Lock acquired for device {uuid}")
            try:
                dut = Device(cloud, uuid, hardware_id, public_key)
                if not dut.is_os_updated_to_latest(target_build_type):
                    dut.update_to_latest(target_build_type)
                if use_rac:
                    dut.setup_rac_session(RAC_IP)
                else:
                    dut.setup_usual_ssh_session()
                remote = Remote(
                    dut.remote_session_ip,
                    dut.remote_session_port,
                    device_password,
                )
                if remote.test_connection():
                    logger.info(f"Connection test succeeded for device {uuid}")
                    if args.before:
                        remote.connection.run(args.before)
                    remote.connection.run(args.command)
                    logger.info(
                        f"Command {args.command} executed for device {uuid}"
                    )
                    if args.copy_artifact:
                        if len(args.copy_artifact) % 2 != 0:
                            raise ValueError(
                                "You must provide pairs of remote-path and local-output."
                            )
                        for i in range(0, len(args.copy_artifact), 2):
                            remote_path = args.copy_artifact[i]
                            local_output = args.copy_artifact[i + 1]
                            logger.info(
                                f"Copying copy_artifact file from {remote_path} to {local_output}"
                            )
                            remote.connection.get(remote_path, local_output)
                            logger.info(f"Report retrieved for device {uuid}")
                else:
                    logger.error(f"Connection test failed for device {uuid}")
            except Exception as e:
                logger.error(
                    f"An error occurred while processing device {uuid}: {e}"
                )
                sys.exit(1)
            finally:
                database.release_lock(uuid)
                logger.info(f"Lock released for device {uuid}")
            # found a matching device, locked it, tested, unlocked it...
            if not test_whole_fleet:
                sys.exit(0)
        else:
            logger.info(f"Failed to acquire lock for device {uuid}")
            sys.exit(1)

    if not test_whole_fleet:
        # EX_UNAVAILABLE 69	/* service unavailable */ sysexits.h
        sys.exit(69)


if __name__ == "__main__":
    main()
