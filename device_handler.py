import logging
import sys
import json
import subprocess

import database
import common
from device import Device
from remote import Remote

RAC_IP = "ras.torizon.io"


def process_device(device, cloud, env_vars, args):
    logger = logging.getLogger(__name__)

    uuid = device["deviceUuid"]
    hardware_id = common.parse_hardware_id(device["deviceId"])

    if not database.device_exists(uuid):
        database.create_device(uuid)
        logger.info(f"Created new device entry for {uuid}")

    if database.try_until_locked(uuid):
        logger.info(f"Lock acquired for device {uuid}")
        try:
            dut = Device(cloud, uuid, hardware_id, env_vars["PUBLIC_KEY"])

            if not dut.is_os_updated_to_latest(env_vars["TARGET_BUILD_TYPE"]):
                dut.update_to_latest(env_vars["TARGET_BUILD_TYPE"])
                # If this is true again, a rollback happened
                if not dut.is_os_updated_to_latest(
                    env_vars["TARGET_BUILD_TYPE"]
                ):
                    raise Exception(
                        f"The update wasn't succesfull: the device {uuid} most likely rollbacked."
                    )

            if env_vars["USE_RAC"]:
                dut.setup_rac_session(RAC_IP)
            else:
                dut.setup_usual_ssh_session()

            remote = Remote(
                dut.remote_session_ip,
                dut.remote_session_port,
                env_vars["DEVICE_PASSWORD"],
            )

            if remote.test_connection():
                logger.debug(f"Connection test succeeded for device {uuid}")

                logger.debug(dut.network_info)

                if dut.network_info:
                    with open("device_information.json", "w") as f:
                        json.dump(dut.network_info, f, ensure_ascii=False)

                if args.run_before_on_host:
                    logger.debug(f"Executing {args.run_before_on_host} on host")
                    subprocess.check_call(
                        args.run_before_on_host,
                        shell=True,
                        stdout=sys.stdout,
                        stderr=subprocess.STDOUT,
                    )

                if args.before:
                    remote.connection.run(args.before)

                if args.command:
                    remote.connection.run(args.command)
                    logger.info(
                        f"Command '{args.command}' executed for device {uuid}"
                    )

                if args.copy_artifact:
                    for i in range(0, len(args.copy_artifact), 2):
                        remote_path = args.copy_artifact[i]
                        local_output = args.copy_artifact[i + 1]
                        logger.info(
                            f"Copying artifact from {remote_path} to {local_output}"
                        )
                        remote.connection.get(remote_path, local_output)
                        logger.info(f"Artifact retrieved for device {uuid}")
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

        # Successfully processed the device
        return True
    else:
        logger.info(f"Failed to acquire lock for device {uuid}")
        return False
