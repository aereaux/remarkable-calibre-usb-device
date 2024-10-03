#!/usr/bin/env python3

import sys
import uuid
import os
import time
import json
import shutil
import argparse
import uuid
import subprocess
import tempfile
import pathlib
import urllib.request
import re

XOCHITL_BASE_FOLDER = ".local/share/remarkable/xochitl"
default_prepdir = tempfile.mkdtemp(prefix="resync-")

ssh_socketfile = '/tmp/remarkable-push.socket'
ssh_options="-o BatchMode=yes"
ssh_socket_options = f" -S {ssh_socketfile}" if os.name != 'nt' else ""

def xochitl_restart(ip):
	cmd = f'ssh {ssh_options} {ssh_socket_options} root@{ip} "systemctl restart xochitl"'
	subprocess.getoutput(cmd)
	
def mkdir(ip, parent_id):
	metadata_json = '{"createdTime": "1727938633680",    "lastModified": "1727938633678",    "parent": "'+parent_id+'",    "pinned": false,    "type": "CollectionType",    "visibleName": "L2"}'
	content_json = """{"tags": [    ]}"""
	file_id = str(uuid.uuid4())
	cmd = f'ssh {ssh_options} {ssh_socket_options} root@{ip} \'echo {metadata_json} > {XOCHITL_BASE_FOLDER}/{file_id}.metadata; echo {content_json} > {XOCHITL_BASE_FOLDER}/{file_id}.content\''
	subprocess.getoutput(cmd)
