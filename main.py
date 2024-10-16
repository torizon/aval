from cloud import CloudAPI
import logging
import sys

import logging_setup
import argument_parser
import environment
import device_matcher
import device_handler


def main():
    logger = logging_setup.setup_logging()

    args = argument_parser.parse_arguments()

    env_vars = environment.load_environment_variables(args)

    if args.delegation_config:
        cloud = CloudAPI(
            api_client=env_vars["TORIZON_API_CLIENT_ID"],
            api_secret=env_vars["TORIZON_API_SECRET_ID"],
            delegation_config_path=args.delegation_config,
        )
    else:
        logger.error("Missing delegation config file")
        sys.exit(1)

    possible_duts = device_matcher.find_possible_devices(cloud, args, env_vars)

    for device in possible_duts:
        success = device_handler.process_device(device, cloud, env_vars, args)
        if success and not env_vars["TEST_WHOLE_FLEET"]:
            sys.exit(0)

    if not env_vars["TEST_WHOLE_FLEET"]:
        # EX_UNAVAILABLE 69	/* service unavailable */ sysexits.h
        sys.exit(69)


if __name__ == "__main__":
    main()
