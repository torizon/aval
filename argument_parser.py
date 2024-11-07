import argparse


class ValidateCopyArtifact(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        if len(values) % 2 != 0:
            parser.error(
                f"argument {option_string}: You must provide pairs of remote-path and local-output."
            )
        setattr(namespace, self.dest, values)


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Run commands on remote devices provisioned on Torizon Cloud."
    )
    parser.add_argument(
        "--copy-artifact",
        nargs="+",
        metavar=("remote-path", "local-output"),
        action=ValidateCopyArtifact,
        help=(
            "Copies multiple files over Remote Access from the target device "
            "to local-output. Specify pairs of remote-path and local-output."
        ),
    )
    parser.add_argument(
        # arguments without leading `--` are assumed to be positional and not
        # optional. Use nargs='?' to force the last command to be optional.
        "command",
        type=str,
        nargs="?",
        help="Command to run on target device.",
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
    parser.add_argument(
        "--device-config",
        type=str,
        help="Path of config which tells Aval which device to match.",
    )
    parser.add_argument(
        "--run-before-on-host",
        type=str,
        help="Command to be executed on host (the machine calling aval) after locking and updating the device.",
    )
    parser.add_argument(
        "--pid-map",
        type=str,
        help="Path of a PID4 map yaml file describing devices and their properties. By default it tries to use a `pid_map.yaml` located in the directory where Aval is called from.",
    )

    args = parser.parse_args()
    return args
