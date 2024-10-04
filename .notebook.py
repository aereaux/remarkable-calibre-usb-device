# https://github.com/404Wolf/remarkable-connection-utility/tree/0dc42d188af723569a07f827b43713e9c56ef6c7
# https://github.com/cherti/remarkable-cli-tooling/blob/4876f3cecbd6c2365441e24ec4d113d613159362/resync.py#L12
# https://github.com/sergei-mironov/remarkable-cli-tooling/tree/ceccaf4b2c30fcbaad0a7f3397147763c0e35f5e
# %%
from __future__ import annotations

import os
import pathlib
import tempfile

import random
import shutil
from dataclasses import dataclass
from typing import TYPE_CHECKING, List, Optional


import rm_web_interface
import rm_ssh

if TYPE_CHECKING:
    from calibre.ebooks.metadata.book.base import Metadata

device = None
BASE_REMOTE_FOLDER = "calibre_uploads"
IP = "10.11.99.1"


def upload_books(files_original, names, on_card=None, end_session=True, metadata: Optional[list[Metadata]] = None):
    upload_ids = []
    has_ssh = rm_ssh.test_connection(IP)
    existing_folders = rm_web_interface.query_tree(IP, "").ls_dir_recursive_dict() if has_ssh else {}
    print(f"existing_folders={existing_folders}")
    if not metadata:
        metadata = [None] * len(files_original)

    # upload
    for path, visible_name, m in zip(files_original, names, metadata):
        rm_web_interface.upload_file(IP, path, "", visible_name)
        upload_ids.append(rm_ssh.get_latest_upload_id(IP))

    # create folders, move files into their respective folders, reboot
    if has_ssh:
        needs_reboot = False
        for file_id, m in zip(upload_ids, metadata):
            author = m.author_sort or m.author if m else ""

            folder_id = ""
            if BASE_REMOTE_FOLDER:
                folder_id = existing_folders.get(BASE_REMOTE_FOLDER)
                print(f"folder_id={folder_id}")
                if not folder_id:
                    folder_id = rm_ssh.mkdir(IP, BASE_REMOTE_FOLDER, "")
                    existing_folders[BASE_REMOTE_FOLDER] = folder_id
                    needs_reboot = True
                    print(f"after mkdir folder_id={folder_id}")

            if author:
                remote_folder = pathlib.Path(BASE_REMOTE_FOLDER, author).as_posix()
                folder_id = existing_folders.get(remote_folder)
                print(f"author folder_id={folder_id}, author={author}")
                if not folder_id:
                    folder_id = rm_ssh.mkdir(IP, author, existing_folders[BASE_REMOTE_FOLDER])
                    existing_folders[remote_folder] = folder_id
                    needs_reboot = True
                    print(f"after author mkdir folder_id={folder_id}")

            if folder_id:
                rm_ssh.sed(IP, f"{file_id}.metadata", '"parent": ""', f'"parent": "{folder_id}"')

        if needs_reboot:
            rm_ssh.xochitl_restart(IP)


rm_ssh.sed(IP, f"fca2cac5-4da8-41b6-b3c7-48446fc63a4f.metadata", '"parent": ""', f'"parent": "f6ddcd8b-7509-4fab-853c-a43368ef0905"')
