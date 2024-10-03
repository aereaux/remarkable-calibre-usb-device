#!/usr/bin/env python3

import argparse
import os
import shutil
import subprocess
import sys
import tempfile

from resync.lib import get_toplevel_files, pull_from_remarkable, push_to_remarkable, ssh_connection, upload_directly

default_prepdir = tempfile.mkdtemp(prefix="resync-")

ssh_socketfile = "/tmp/remarkable-push.socket"
ssh_options = "-o BatchMode=yes"

parser = argparse.ArgumentParser(description="Push and pull files to and from your reMarkable")

parser.add_argument(
    "--dry-run",
    dest="dryrun",
    action="store_true",
    default=False,
    help="Don't actually copy files, just show what would be copied",
)
parser.add_argument(
    "-o",
    "--output",
    action="store",
    default=None,
    dest="output_destination",
    metavar="<folder>",
    help="Destination for copied files, either on or off device",
)
parser.add_argument("-v", dest="verbosity", action="count", default=0, help="verbosity level")

parser.add_argument(
    "--if-exists",
    dest="conflict_behavior",
    choices=["skip", "new", "replace", "replace-pdf-only"],
    default="skip",
    help=(
        "if the destination file already exists: *skip* pushing document (default); create a separate *new* separate document under the same name; *replace* document; *replace-pdf-only*: replace underlying pdf only on reMarkable, keep notes etc."
    ),
)

parser.add_argument(
    "-e",
    "--exclude",
    dest="exclude_patterns",
    action="append",
    type=str,
    help="exclude a pattern from transfer (must be Python-regex)",
)

parser.add_argument(
    "-r",
    "--remote-address",
    action="store",
    default="10.11.99.1",
    dest="ssh_destination",
    metavar="<IP or hostname>",
    help="remote address of the reMarkable",
)
parser.add_argument(
    "--transfer-dir",
    metavar="<directory name>",
    dest="prepdir",
    type=str,
    default=default_prepdir,
    help="custom directory to render files to-be-upload",
)
parser.add_argument(
    "--debug", dest="debug", action="store_true", default=False, help="Render documents, but don't copy to remarkable."
)

parser.add_argument("mode", metavar="mode", type=str, help="push/+, pull/- or backup")
parser.add_argument(
    "documents", metavar="documents", type=str, nargs="*", help="Documents and folders to be pushed to the reMarkable"
)

args = parser.parse_args()

if args.exclude_patterns is None:
    args.exclude_patterns = []

if args.mode == "+":
    args.mode = "push"
elif args.mode == "-":
    args.mode = "pull"


ssh_connection = None
try:
    ssh_connection = subprocess.Popen(f"ssh -o ConnectTimeout=1 -M -N -q root@{args.ssh_destination}", shell=True)

    # quickly check if we actually have a functional ssh connection (might not be the case right after an update)
    p = subprocess.Popen(
        f'ssh {ssh_options} root@{args.ssh_destination} "/bin/true"',
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    p.wait()
    if p.returncode != 0:
        stdout, stderr = p.communicate()
        print(
            "ssh connection does not work, verify that you can manually ssh into your reMarkable. ssh itself commented the situation with:"
        )
        print(stdout.decode("utf-8"), stderr.decode("utf-8"))
        ssh_connection.terminate()
        sys.exit(255)

    if args.mode == "push":
        if args.output_destination is None and args.conflict_behavior not in ["replace", "replace-pdf-only"]:
            failed_uploads = upload_directly(args.documents)
            if failed_uploads:
                push_to_remarkable(failed_uploads, destination=args.output_destination)
        else:
            push_to_remarkable(args.documents, destination=args.output_destination)
    elif args.mode == "pull":
        pull_from_remarkable(args.documents, destination=args.output_destination)
    elif args.mode == "backup":
        pull_from_remarkable(get_toplevel_files(), destination=args.output_destination)
    else:
        print("Unknown mode, doing nothing.")
        print("Available modes are")
        print("    push:   push documents from this machine to the reMarkable")
        print("    pull:   pull documents from the reMarkable to this machine")
        print("    backup: pull all files from the remarkable to this machine (excludes still apply)")

finally:
    if ssh_connection is not None:
        ssh_connection.terminate()
        # os.remove(ssh_socketfile)
    if os.path.exists(default_prepdir):  # we created this
        shutil.rmtree(args.prepdir)
