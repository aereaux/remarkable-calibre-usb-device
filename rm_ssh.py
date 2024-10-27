#!/usr/bin/env python3
import logging
import os
import pathlib
import subprocess
import tempfile
import time
import uuid

from .log_helper import log_args_kwargs  # type: ignore
from .rm_data import RemarkableSettings

XOCHITL_BASE_FOLDER = "~/.local/share/remarkable/xochitl"
default_prepdir = tempfile.mkdtemp(prefix="resync-")

ssh_socketfile = "/tmp/remarkable-push.socket"
ssh_options2 = ["-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes"]
ssh_options_str = " ".join(ssh_options2)
ssh_socket_options = f" -S {ssh_socketfile}" if os.name != "nt" else ""


def ssh_address(settings: RemarkableSettings):
    return f"root:{settings.SSH_PASSWORD}@{settings.IP}" if settings.SSH_PASSWORD else f"root@{settings.IP}"


@log_args_kwargs
def xochitl_restart(settings: RemarkableSettings):
    p = subprocess.Popen(
        ["ssh", *ssh_options2, ssh_address(settings), "systemctl restart xochitl"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    p.wait()
    if p.returncode != 0:
        raise SystemError(f"{p.returncode=}, {p.stdout}")


@log_args_kwargs
def _touch_fs(settings: RemarkableSettings):
    """
    Test if ssh is working AND home is writable
    """
    p = subprocess.Popen(
        ["ssh", *ssh_options2, ssh_address(settings), "touch ~/calibre_remarkable_usb_device.touch"],
        shell=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    p.wait()
    return p.returncode == 0


@log_args_kwargs
def init_metadata(settings: RemarkableSettings):
    p = subprocess.Popen(
        ["ssh", *ssh_options2, ssh_address(settings), f"echo [] > {settings.CALIBRE_METADATA_PATH}"],
        shell=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    p.wait()
    return p.returncode == 0


@log_args_kwargs
def scp(settings: RemarkableSettings, src_file: str, dest: str):
    p = subprocess.run(
        ["scp", src_file, f"{ssh_address(settings)}:{dest}"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    if p.returncode != 0:
        raise RuntimeError(f"returncode={p.returncode}, stdout={p.stdout}")


@log_args_kwargs
def test_connection(settings: RemarkableSettings):
    """
    Test if ssh is working AND home is writable
    """
    try:
        rw_success = _touch_fs(settings)
        if not rw_success:
            p = subprocess.Popen(
                ["ssh", *ssh_options2, ssh_address(settings), "mount -o remount,rw /"],
                shell=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            p.wait()
            return p.returncode == 0
        return True
    except Exception as e:  # noqa: E722
        logging.warn("SSH connection failed", exc_info=True)
        return False


@log_args_kwargs
def sed(settings: RemarkableSettings, xochitl_filename, i: str, o: str):
    p = subprocess.Popen(
        (
            "ssh",
            "-o",
            "StrictHostKeyChecking=no",
            "-o",
            "BatchMode=yes",
            ssh_address(settings),
            f"sed -i -e 's/{i}/{o}/g' {XOCHITL_BASE_FOLDER}/{xochitl_filename}",
        ),
        shell=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    p.wait()


@log_args_kwargs
def get_latest_upload_uuid(settings: RemarkableSettings):
    p = subprocess.run(
        ["ssh", *ssh_options2, ssh_address(settings), f"cd {XOCHITL_BASE_FOLDER}; ls -Art *.metadata | tail -n 1"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    return p.stdout.strip().replace(".metadata", "")


@log_args_kwargs
def cat(settings: RemarkableSettings, file: str):
    p = subprocess.run(
        ["ssh", *ssh_options2, ssh_address(settings), f"cat {file}"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    if p.returncode != 0:
        return None

    return p.stdout.strip()


@log_args_kwargs
def mkdir(settings: RemarkableSettings, visible_name, parent_id=""):
    file_id = str(uuid.uuid4())
    with tempfile.TemporaryDirectory() as tmp_folder:
        file_metadata = f"{file_id}.metadata"
        file_content = f"{file_id}.content"
        current_timestamp_str = str(int(time.time()))
        with open(pathlib.Path(tmp_folder, file_metadata), "w+") as fp:
            metadata_json = (
                '{"createdTime": "'
                + current_timestamp_str
                + '",    "lastModified": "'
                + current_timestamp_str
                + '",    "parent": "'
                + parent_id
                + '",    "pinned": false,    "type": "CollectionType",    "visibleName": "'
                + visible_name
                + '"}'
            )
            fp.write(metadata_json)
        with open(pathlib.Path(tmp_folder, file_content), "w+") as fp:
            content_json = """{"tags": []}"""
            fp.write(content_json)

        cmd = f"scp -r {tmp_folder}/* {ssh_address(settings)}:{XOCHITL_BASE_FOLDER}"
        result = subprocess.getoutput(cmd)
        logging.getLogger().debug(result)
    return file_id
