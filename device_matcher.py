import sys
import convolute
import common
import config_loader
import re
from common import get_architectures_from_pid_map
import logging_setup

logger = logging_setup.setup_logging()


def find_possible_devices(cloud, args, env_vars):
    test_whole_fleet = env_vars["TEST_WHOLE_FLEET"]
    target_build_type = env_vars["TARGET_BUILD_TYPE"]
    soc_udt = env_vars.get("SOC_UDT")
    use_common_devices = env_vars.get("USE_COMMON_DEVICES")

    logger.info("Finding possible devices to send tests to...")

    if not args.device_config:
        logger.info(
            f"Matching configuration: SOC_UDT {soc_udt}, BUILD TYPE {target_build_type}"
        )
    else:
        device_config = convolute.get_device_config_data(
            config_loader.load_device_config(args.device_config)
        )
        soc_udt, soc_properties = device_config
        logger.info(
            f"Matching configuration: SOC_UDT {soc_udt}, SOC_PROPERTIES {soc_properties}, BUILD TYPE {target_build_type}"
        )

    if test_whole_fleet:
        possible_duts = cloud.provisioned_devices
    else:
        pid4_map = config_loader.load_pid_map(pid_map_path=args.pid_map)
        possible_duts = []

        architectures = get_architectures_from_pid_map(args.pid_map)

        if args.device_config:
            pid4_targets = convolute.get_pid4_list_with_device_config(
                device_config, pid4_map
            )
        elif soc_udt:
            if soc_udt in architectures:
                pid4_targets = convolute.get_pid4_list_from_architecture(
                    soc_udt, pid4_map, use_common_devices
                )
            else:
                pid4_targets = convolute.get_pid4_list(soc_udt, pid4_map)

        for device in cloud.provisioned_devices:
            pid4 = device.get("notes")

            if not pid4:
                logger.error(
                    f"The following device has no PID4 set in the `notes` field: {device}"
                )
                continue

            if not re.fullmatch(r"\d{4}", pid4):
                logger.error(
                    f"The following device has an invalid PID4 '{pid4}' in the `notes` field: {device}"
                )
                continue

            # No need to reset pid4_targets inside the loop
            if pid4 in pid4_targets:
                possible_duts.append(device)

    if not possible_duts:
        logger.error("Couldn't find any possible devices to send tests to")
        sys.exit(1)
    else:
        logger.info("Found these devices to send tests to:")
        logger.debug(possible_duts)
        logger.info(common.pretty_print_devices(possible_duts))

    return possible_duts
