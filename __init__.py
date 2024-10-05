from __future__ import annotations

import posixpath
import random
from dataclasses import dataclass
from typing import TYPE_CHECKING, List, Optional

from calibre.devices.interface import DevicePlugin  # type: ignore
from calibre.devices.usbms.deviceconfig import DeviceConfig  # type: ignore

from . import rm_ssh
from . import rm_web_interface as rm_web_interface
from .log_helper import log_args_kwargs

if TYPE_CHECKING:
    from calibre.devices.usbms.device import USBDevice  # type: ignore
    from calibre.ebooks.metadata.book.base import Metadata  # type: ignore

PLUGIN_NAME = "Remarkable Device Plugin for Calibre"
print("----------------------------------- REMARKABLE PLUGIN web interface ------------------------")
device = None


@dataclass
class RemarkableSettings:
    IP: str
    SSH_PASSWORD: str


@dataclass
class RemarkableDeviceDescription:
    def __init__(self, ip):
        self.ip = ip
        self.random_id = random.randint(0, 9999999999999)

    def __str__(self) -> str:
        return f"Remarkable on http://{self.ip}, rid={self.random_id}"


class RemarkableUsbDevice(DeviceConfig, DevicePlugin):
    progress = 0.0
    name = PLUGIN_NAME
    description = "Send epub and pdf files to Remarkable"
    author = "Andri Rakotomalala"
    supported_platforms = ["linux", "windows", "osx"]
    version = (0, 1, 1)  # The version number of this plugin
    minimum_calibre_version = (0, 7, 53)

    FORMATS = ["epub", "pdf"]
    CAN_SET_METADATA: list[str] = []
    MANAGES_DEVICE_PRESENCE = True
    SUPPORTS_SUB_DIRS = True
    HIDE_FORMATS_CONFIG_BOX = True
    NEWS_IN_FOLDER = True
    USER_CAN_ADD_NEW_FORMATS = False

    MUST_READ_METADATA = False
    SUPPORTS_USE_AUTHOR_SORT = False
    SAVE_TEMPLATE = "calibre/{author_sort}/{title} - {authors}"  # type: ignore

    EXTRA_CUSTOMIZATION_MESSAGE = [  # type: ignore
        # -----------
        "IP address:::"
        "<p>"
        "Use this option if you want to force the driver to listen on a "
        "particular IP address. The driver will listen only on the "
        "entered address, and this address will be the one advertised "
        "over mDNS (BonJour)."
        "</p>",
        # -----------
        "SSH password (optional):::" "<p>Required for folders support</p>",
    ]
    EXTRA_CUSTOMIZATION_DEFAULT = [  # type: ignore
        "10.11.99.1",
        "",
    ]

    def config_widget(self):
        from calibre.gui2.device_drivers.configwidget import (  # type: ignore
            ConfigWidget,
        )

        cw = ConfigWidget(
            self.settings(),
            self.FORMATS,
            self.SUPPORTS_SUB_DIRS,
            self.MUST_READ_METADATA,
            self.SUPPORTS_USE_AUTHOR_SORT,
            self.EXTRA_CUSTOMIZATION_MESSAGE,
            self,
        )
        return cw

    @classmethod
    def settings_obj(cls):
        settings = cls.settings()
        return RemarkableSettings(*settings.extra_customization)

    @log_args_kwargs
    def startup(self):
        super().startup()

    @log_args_kwargs
    def detect_managed_devices(self, devices_on_system: List[USBDevice], force_refresh=False):
        global device
        settings = self.settings_obj()

        try:
            # TODO: check for USBDevice.vendor_id
            if device is None and rm_web_interface.check_connection(settings.IP):
                device = RemarkableDeviceDescription(settings.IP)
                print(f"detected new {device=}")
            print(f"returning {device=}")
            return device
        except Exception as e:
            print(f"No device detected {e=}")
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
        settings = self.settings_obj()
        return rm_web_interface.query_tree(settings.IP, "").ls_recursive()

    def _create_upload_path(self, path, mdata, fname):
        from calibre.devices.utils import create_upload_path  # type: ignore
        from calibre.utils.filenames import ascii_filename as sanitize  # type: ignore

        return create_upload_path(
            mdata,
            fname,
            self.save_template(),
            sanitize,
            prefix_path="",
            path_type=posixpath,
            maxlen=200,
            use_subdirs="/" in self.save_template(),
            news_in_folder=self.NEWS_IN_FOLDER,
        )

    @log_args_kwargs
    def upload_books(
        self, files_original, names, on_card=None, end_session=True, metadata: Optional[list[Optional[Metadata]]] = None
    ):
        self.progress = 0.0
        settings = self.settings_obj()

        upload_ids = []
        if not metadata:
            metadata = [None] * len(files_original)
        step = 60 / len(files_original)
        for upload_path, visible_name, m in zip(files_original, names, metadata):
            rm_web_interface.upload_file(settings.IP, upload_path, "", visible_name)
            upload_ids.append(rm_ssh.get_latest_upload_id(settings.IP))
            self.progress += step
        self.progress = 60.0

        has_ssh = rm_ssh.test_connection(settings.IP)
        print(f"{has_ssh=}")
        if has_ssh:
            existing_folders = rm_web_interface.query_tree(settings.IP, "").ls_dir_recursive_dict() if has_ssh else {}
            print(f"{existing_folders=}")
            needs_reboot = False
            for file_id, fn, m in zip(upload_ids, files_original, metadata):
                upload_path = self._create_upload_path(fn, m, fn)
                if upload_path:
                    parts = upload_path.split("/")
                    parts = parts[:-1]
                    folder_id = ""
                    parent_folder_id = ""
                    for i in range(len(parts)):
                        part_full = "/".join(parts[i : i + 1])
                        folder_id = existing_folders.get(part_full)
                        print(f"{folder_id=}")
                        if not folder_id:
                            part_name = parts[i]
                            folder_id = rm_ssh.mkdir(settings.IP, part_name, parent_folder_id)
                            existing_folders[part_full] = folder_id
                            needs_reboot = True
                            print(f"after mkdir {folder_id=}")
                        parent_folder_id = folder_id

                    if folder_id:
                        rm_ssh.sed(settings.IP, f"{file_id}.metadata", '"parent": ""', f'"parent": "{folder_id}"')
                        needs_reboot = True

            self.progress = 80.0
            if needs_reboot:
                rm_ssh.xochitl_restart(settings.IP)
        self.progress = 100.0

    @log_args_kwargs
    def open(self, connected_device, library_uuid):
        print(f"opening {connected_device=}")

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
        def dummy_set_progress_reporter(*args, **kwargs):
            return int(self.progress)

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
