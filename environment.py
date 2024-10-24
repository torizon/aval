import os
import sys
import logging


def load_environment_variables(args):
    logger = logging.getLogger(__name__)

    test_whole_fleet = os.getenv("TEST_WHOLE_FLEET", "False").lower() == "true"
    use_rac = os.getenv("USE_RAC", "False").lower() == "true"

    if not args.device_config:
        soc_architecture = os.environ.get("SOC_ARCHITECTURE")
        if not soc_architecture:
            try:
                soc_udt = os.environ["SOC_UDT"]
            except KeyError as e:
                logger.error(f"Missing environment variable: {e}")
                sys.exit(1)
        else:
            soc_udt = None  # Handled by SOC_ARCHITECTURE or device config
    else:
        soc_udt = None  # Handled by device config
        soc_architecture = None

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

    env_vars["TEST_WHOLE_FLEET"] = test_whole_fleet
    env_vars["USE_RAC"] = use_rac

    if soc_udt is not None:
        env_vars["SOC_UDT"] = soc_udt
    if soc_architecture is not None:
        env_vars["SOC_ARCHITECTURE"] = soc_architecture

    return env_vars
