#!/usr/bin/env python3

import uuid
import os
import time
import uuid
import subprocess
import tempfile
import pathlib
import time
try:
    from .helpers import log_args_kwargs
except:
    from helpers import log_args_kwargs

XOCHITL_BASE_FOLDER = "~/.local/share/remarkable/xochitl"
default_prepdir = tempfile.mkdtemp(prefix="resync-")

ssh_socketfile = "/tmp/remarkable-push.socket"
ssh_options = "-o BatchMode=yes"
ssh_socket_options = f" -S {ssh_socketfile}" if os.name != "nt" else ""


@log_args_kwargs
def xochitl_restart(ip):
    cmd = f'ssh {ssh_options} {ssh_socket_options} root@{ip} "systemctl restart xochitl"'
    subprocess.getoutput(cmd)


@log_args_kwargs
def test_connection(ip):
    """
    Test if ssh is working AND home is writable
    """
    p = subprocess.Popen(
        f'ssh {ssh_options} root@{ip} "touch ~/calibre-remarkable-usb-device.touch"',
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    p.wait()
    return p.returncode == 0


@log_args_kwargs
def sed(ip, xochitl_filename, i: str, o: str):
    p = subprocess.Popen(
        (
            "ssh",
            "-o",
            "BatchMode=yes",
            f"root@{ip}",
            f"sed -i -e 's/{i}/{o}/g' {XOCHITL_BASE_FOLDER}/{xochitl_filename}",
        ),
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    p.wait()


@log_args_kwargs
def get_latest_upload_id(ip):
    p = subprocess.run(
        f'ssh {ssh_options} root@{ip} "cd {XOCHITL_BASE_FOLDER}; ls -Art *.metadata | tail -n 1',
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return p.stdout.strip().replace(".metadata", "")


@log_args_kwargs
def mkdir(ip, visible_name, parent_id=""):
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

        cmd = f"scp -r {tmp_folder}/* root@{ip}:{XOCHITL_BASE_FOLDER}"
        result = subprocess.getoutput(cmd)
        print(result)
    return file_id
