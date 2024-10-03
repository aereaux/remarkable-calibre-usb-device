from __future__ import annotations

import os
import pathlib
import tempfile

import random
import shutil
from dataclasses import dataclass
from typing import TYPE_CHECKING, List, Optional


# from . import rm_web_interface
from .helpers import log_args_kwargs
from . import rm_web_interface as rm_web_interface
from . import rm_ssh

if TYPE_CHECKING:
    from calibre.ebooks.metadata.book.base import Metadata

device = None
BASE_REMOTE_FOLDER = "calibre"
IP = "10.11.99.1"




def upload_books(
    self, files_original, names, on_card=None, end_session=True, metadata: Optional[list[Metadata]] = None
):
    needs_reboot = False
    has_ssh = rm_ssh.test_connection(IP)
    existing_folders = rm_web_interface.query_tree(IP, "").ls_dir_recursive_dict()
    print(f"existing_folders={existing_folders}")
    if not metadata:
        metadata = [None] * len(files_original)
    for path, visible_name, m in zip(files_original, names, metadata):
        author = m.author_sort or m.author or ""

        folder_id = ""
        if has_ssh:
            if BASE_REMOTE_FOLDER:
                folder_id = existing_folders.get(BASE_REMOTE_FOLDER)
                print(f"folder_id={folder_id}")
                if not folder_id:
                    folder_id = rm_ssh.mkdir(IP, BASE_REMOTE_FOLDER, "")
                    existing_folders[BASE_REMOTE_FOLDER] = folder_id
                    needs_reboot=True
                    print(f"after mkdir folder_id={folder_id}")

            if author:
                remote_folder = pathlib.Path(BASE_REMOTE_FOLDER, author).as_posix()
                folder_id = existing_folders.get(remote_folder)
                print(f"author folder_id={folder_id}, author={author}")
                if not folder_id:
                    folder_id = rm_ssh.mkdir(IP, author, existing_folders[BASE_REMOTE_FOLDER])
                    existing_folders[remote_folder] = folder_id
                    needs_reboot=True
                    print(f"after author mkdir folder_id={folder_id}")

        if needs_reboot:
            rm_ssh.xochitl_restart(IP)
        rm_web_interface.upload_file(IP, path, folder_id, visible_name)
