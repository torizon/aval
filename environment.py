import os
import sys
from common import get_architectures_from_pid_map
import logging_setup

logger = logging_setup.setup_logging()


def load_environment_variables(args):
    test_whole_fleet = os.getenv("TEST_WHOLE_FLEET", "False").lower() == "true"
    use_rac = os.getenv("USE_RAC", "False").lower() == "true"
    use_common_devices = (
        os.getenv("USE_COMMON_DEVICES", "False").lower() == "true"
    )

    soc_udt = os.environ.get("SOC_UDT") if not args.device_config else None

    if not args.device_config and not soc_udt:
        logger.error("Missing environment variable: SOC_UDT must be set")
        sys.exit(1)

    required_env_vars = [
        "TORIZON_API_CLIENT_ID",
        "TORIZON_API_SECRET_ID",
        "PUBLIC_KEY",
        "DEVICE_PASSWORD",
        "TARGET_BUILD_TYPE",
    ]
    env_vars = {}

    for var in required_env_vars:
        try:
            env_vars[var] = os.environ[var]
        except KeyError as e:
            logger.error(f"Missing environment variable: {e}")
            sys.exit(1)

    architectures = get_architectures_from_pid_map(args.pid_map)

    if (
        soc_udt is not None
        and soc_udt not in architectures
        and use_common_devices
    ):
        logger.error(
            "You cannot use target a specific device with USE_COMMON_DEVICES set to true."
        )
        sys.exit(1)

    env_vars["TEST_WHOLE_FLEET"] = test_whole_fleet
    env_vars["USE_RAC"] = use_rac
    env_vars["USE_COMMON_DEVICES"] = use_common_devices

    if soc_udt is not None:
        env_vars["SOC_UDT"] = soc_udt

    return env_vars
