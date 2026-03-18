import atexit
import logging
import os
import shutil
import subprocess
import threading
from pathlib import Path

logger = logging.getLogger(__name__)

_SCRIPT_DIR = Path(__file__).resolve().parent
_tunnel_lock = threading.Lock()
_tunnel_started = False
_cleanup_registered = False


def use_aws_rds():
    return bool(os.environ.get("AWS_RDS_HOST"))


def ensure_ssm_tunnel():
    global _tunnel_started, _cleanup_registered

    if not use_aws_rds():
        logger.debug("AWS RDS not configured, skipping SSM tunnel startup")
        return

    with _tunnel_lock:
        if _tunnel_started:
            logger.debug("SSM tunnel already started, skipping startup")
            return

        logger.info("AWS_RDS_HOST detected -> starting SSM tunnel")
        _run_script("rds-ssm-tunnel.sh", "rds-ssm-tunnel.ps1")
        _tunnel_started = True

        if not _cleanup_registered:
            atexit.register(close_ssm_tunnel)
            _cleanup_registered = True


def close_ssm_tunnel():
    global _tunnel_started

    if not use_aws_rds():
        logger.debug("AWS RDS not configured, skipping SSM tunnel shutdown")
        return

    with _tunnel_lock:
        if not _tunnel_started:
            logger.debug("SSM tunnel not started, nothing to close")
            return

        try:
            logger.info("Stopping AWS SSM tunnel")
            _run_script("kill-ssm-tunnels.sh", "kill-ssm-tunnels.ps1")
        finally:
            _tunnel_started = False


def _run_script(posix_script_name, windows_script_name):
    command = _build_script_command(posix_script_name, windows_script_name)

    try:
        subprocess.run(command, check=True)
    except FileNotFoundError as exc:
        raise RuntimeError(
            "Unable to execute the AWS SSM helper script. "
            "Please make sure the required shell is installed."
        ) from exc


def _build_script_command(posix_script_name, windows_script_name):
    if os.name == "posix":
        return ["sh", str(_SCRIPT_DIR / posix_script_name)]

    if os.name == "nt":
        return [
            _find_powershell(),
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(_SCRIPT_DIR / windows_script_name),
        ]

    raise RuntimeError(f"Unsupported operating system: {os.name}")


def _find_powershell():
    for candidate in ("powershell", "pwsh", "powershell.exe", "pwsh.exe"):
        powershell = shutil.which(candidate)
        if powershell:
            return powershell

    raise RuntimeError(
        "PowerShell is required to manage the AWS SSM tunnel on Windows."
    )
