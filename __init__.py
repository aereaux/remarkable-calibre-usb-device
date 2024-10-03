from __future__ import annotations

import os
import pathlib
import tempfile

import random
import shutil
from dataclasses import dataclass
from typing import TYPE_CHECKING, List, Optional

from calibre.devices.interface import DevicePlugin
from calibre.ebooks.metadata.book.base import Metadata

# from . import rm_web_interface
from .helpers import log_args_kwargs
from . import rm_web_interface as rm_web_interface
from . import rm_ssh

if TYPE_CHECKING:
    from calibre.devices.usbms.device import USBDevice

print("----------------------------------- REMARKABLE PLUGIN web interface ------------------------")
device = None
BASE_REMOTE_FOLDER = "calibre"
IP = "10.11.99.1"

def dummy_set_progress_reporter(*args, **kwargs):
    print("dummy_set_progress_reporter")
    return 100



@dataclass
class RemarkableDeviceDescription:
    def __init__(self, ip):
        self.ip = ip
        self.random_id = random.randint(0, 9999999999999)

    def __str__(self) -> str:
        return f"Remarkable on http://{self.ip}, rid={self.random_id}"


class RemarkableUsbDevice(DevicePlugin):
    name = "Remarkable Device Plugin for Calibre"
    description = "Send files to Remarkable"
    author = "Andri Rakotomalala"
    supported_platforms = ["linux", "windows", "osx"]
    version = (0, 1, 1)  # The version number of this plugin
    minimum_calibre_version = (0, 7, 53)

    FORMATS = ["epub", "pdf"]
    CAN_SET_METADATA = []
    MANAGES_DEVICE_PRESENCE = True

    @log_args_kwargs
    def startup(self):
        super().startup()

    @log_args_kwargs
    def detect_managed_devices(self, devices_on_system: List[USBDevice], force_refresh=False):
        global device
        try:
            # TODO: check for USBDevice.vendor_id
            if device is None and rm_web_interface.check_connection(IP):
                device = RemarkableDeviceDescription(IP)
                print(f"detected new {device}")
            print(f"returning device={device}")
            return device
        except Exception as e:
            print(f"No device detected {e}")
            device = None
            return None

    @log_args_kwargs
    def debug_managed_device_detection(self, devices_on_system, output):
        print(
            "Should write information about the devices detected on the system to output, which is a file like object."
        )
        return True

    @log_args_kwargs
    def books(self, oncard=None, end_session=True):
        return rm_web_interface.query_tree(IP, "").ls_recursive()

    @log_args_kwargs
    def upload_books(
        self, files_original, names, on_card=None, end_session=True, metadata: Optional[list[Metadata]] = None
    ):
        needs_reboot = False
        has_ssh = rm_ssh.test_connection(IP)
        existing_folders = rm_web_interface.query_tree(IP, "").ls_dir_recursive_dict()
        if not metadata:
            metadata = [None] * len(files_original)
        for path, visible_name, m in zip(files_original, names, metadata):
            author = m.author_sort or m.author or ""

            folder_id = ""
            if has_ssh:
                if BASE_REMOTE_FOLDER:
                    folder_id = existing_folders.get(BASE_REMOTE_FOLDER)
                    if not folder_id:
                        folder_id = rm_ssh.mkdir(IP, BASE_REMOTE_FOLDER, "")
                        needs_reboot=True

                if author:
                    remote_folder = pathlib.Path(BASE_REMOTE_FOLDER, author).as_posix()
                    folder_id = existing_folders.get(remote_folder)
                    if not folder_id:
                        folder_id = rm_ssh.mkdir(IP, author, BASE_REMOTE_FOLDER)
                        needs_reboot=True

            rm_web_interface.upload_file(IP, path, folder_id, visible_name)
        
        if needs_reboot:
            rm_ssh.xochitl_restart()

    @log_args_kwargs
    def open(self, connected_device, library_uuid):
        print(f"opening {connected_device}")

    @log_args_kwargs
    def is_usb_connected(self, devices_on_system, debug=False, only_presence=False):
        global device
        return True, device

    @log_args_kwargs
    def eject(self):
        global device
        device = None

    @log_args_kwargs
    def get_device_information(self, end_session=True):
        global device
        if device is not None:
            return (str(device), 1, 1, "application/epub")

    @log_args_kwargs
    def total_space(self, end_session=True):
        return 0

    @log_args_kwargs
    def get_driveinfo(self):
        return super().get_driveinfo()

    @log_args_kwargs
    def get_device_uid(self):
        return device.random_id

    @log_args_kwargs
    def get_file(self, path, outfile, end_session=True):
        return super().get_file(path, outfile, end_session)

    @log_args_kwargs
    def get_option(self, opt_string, default=None):
        return super().get_option(opt_string, default)

    @log_args_kwargs
    def get_user_blacklisted_devices(self):
        return super().get_user_blacklisted_devices()

    @log_args_kwargs
    def set_driveinfo_name(self, location_code, name):
        return super().set_driveinfo_name(location_code, name)

    @log_args_kwargs
    def set_library_info(self, library_name, library_uuid, field_metadata):
        return super().set_library_info(library_name, library_uuid, field_metadata)

    @log_args_kwargs
    def set_option(self, opt_string, opt_value):
        return super().set_option(opt_string, opt_value)

    @log_args_kwargs
    def set_plugboards(self, plugboards, pb_func):
        return super().set_plugboards(plugboards, pb_func)

    @log_args_kwargs
    def set_progress_reporter(self, report_progress):
        return dummy_set_progress_reporter

    @log_args_kwargs
    def set_user_blacklisted_devices(self, devices):
        return super().set_user_blacklisted_devices(devices)

    @log_args_kwargs
    def shutdown(self):
        return super().shutdown()

    @log_args_kwargs
    def synchronize_with_db(self, db, book_id, book_metadata, first_call):
        return super().synchronize_with_db(db, book_id, book_metadata, first_call)

    @log_args_kwargs
    def free_space(self, end_session=True):
        return -1

    @log_args_kwargs
    def temporary_file(self, suffix):
        return super().temporary_file(suffix)

    @log_args_kwargs
    def test_bcd(self, bcdDevice, bcd):
        return super().test_bcd(bcdDevice, bcd)

    @log_args_kwargs
    def specialize_global_preferences(self, device_prefs):
        return super().specialize_global_preferences(device_prefs)

    @log_args_kwargs
    def start_plugin(self):
        return super().start_plugin()

    @log_args_kwargs
    def stop_plugin(self):
        return super().stop_plugin()

    @log_args_kwargs
    def sync_booklists(self, booklists, end_session=True):
        pass  # on remarkable, metadata will be automatically be updated for epubs

    @log_args_kwargs
    def prepare_addable_books(self, paths):
        return super().prepare_addable_books(paths)

    @log_args_kwargs
    def delete_books(self, paths, end_session=True):
        return super().delete_books(paths, end_session)

    @log_args_kwargs
    def do_user_config(self, parent=None):
        return super().do_user_config(parent)

    @log_args_kwargs
    def can_handle(self, device_info, debug=False):
        return super().can_handle(device_info, debug)

    @log_args_kwargs
    def can_handle_windows(self, usbdevice, debug=False):
        return super().can_handle_windows(usbdevice, debug)

    @log_args_kwargs
    def card_prefix(self, end_session=True):
        return ("/prefix1", "/prefix2")

    @log_args_kwargs
    def cli_main(self, args):
        return super().cli_main(args)

    @log_args_kwargs
    def customization_help(self, gui=False):
        return super().customization_help(gui)

    @log_args_kwargs
    def is_customizable(self):
        return super().is_customizable()

    @log_args_kwargs
    def ignore_connected_device(self, uid):
        return super().ignore_connected_device(uid)

    @log_args_kwargs
    def post_yank_cleanup(self):
        return super().post_yank_cleanup()

    @log_args_kwargs
    def is_dynamically_controllable(self):
        return super().is_dynamically_controllable()

    @classmethod
    @log_args_kwargs
    def add_books_to_metadata(cls, locations, metadata, booklists):
        pass

    @classmethod
    def settings(cls):
        """
        Should return an opts object. The opts object should have at least one
        attribute `format_map` which is an ordered list of formats for the
        device.
        """
        return OptsSettings()


class OptsSettings:
    format_map = ["epub", "pdf"]
