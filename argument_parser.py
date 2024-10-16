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
    parser.add_argument(
        "--device-config",
        type=str,
        help="Path of config which tells Aval which device to match.",
    )
    args = parser.parse_args()
    return args
