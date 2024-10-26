from __future__ import annotations

import json
import logging
import posixpath
import random
import tempfile
import time
from dataclasses import asdict, dataclass, field
from typing import IO, TYPE_CHECKING, List

from calibre.devices.interface import DevicePlugin  # type: ignore
from calibre.devices.interface import BookList
from calibre.devices.usbms.deviceconfig import DeviceConfig  # type: ignore

from . import rm_ssh
from . import rm_web_interface as rm_web_interface
from .log_helper import log_args_kwargs
from .rm_settings import RemarkableSettings

if TYPE_CHECKING:
    from calibre.devices.usbms.device import USBDevice  # type: ignore
    from calibre.ebooks.metadata.book.base import Metadata  # type: ignore

PLUGIN_NAME = "remarkable-calibre-usb-device"
print("----------------------------------- REMARKABLE PLUGIN web interface ------------------------")
device = None
logging.basicConfig(level=logging.DEBUG)
LOGGER = logging.getLogger()


@dataclass
class RemarkableDeviceDescription:
    def __init__(self, ip):
        self.ip = ip
        self.random_id = random.randint(0, 9999999999999)

    def __str__(self) -> str:
        return f"Remarkable on http://{self.ip}, rid={self.random_id}"


class RemarkableBookList(BookList):
    def __init__(self, oncard="", prefix="", settings=""):
        super().__init__(oncard, prefix, settings)

    def supports_collections(self):
        return False

    def add_book(self, book, replace_metadata=None):
        self.append(book)

    def remove_book(self, book):
        self.remove(book)

    def get_collections(self, collection_attributes):
        return self

    def json_dumps(self):
        return json.dumps([asdict(x) for x in self])

    @staticmethod
    def json_loads(json_data):
        books = json.loads(json_data)
        rbl = RemarkableBookList()
        for book in books:
            rbl.add_book(RemarkableBook(**book), None)
        return rbl


@dataclass()
class RemarkableBook:
    title: str
    uuid: str
    authors: list[str] = field(default_factory=list)
    size = 0
    datetime = time.localtime()
    thumbnail = None
    tags: list[str] = field(default_factory=list)
    path: str = "/"

    device_collections: List = field(default_factory=list)

    def __eq__(self, other):
        return self.uuid == other.uuid


class RemarkableUsbDevice(DeviceConfig, DevicePlugin):
    VENDOR_ID = 0x04B3
    PRODUCT_ID = 0x4010

    progress = 0.0
    name = PLUGIN_NAME
    description = "Send epub and pdf files to Remarkable"
    author = "Andri Rakotomalala"
    supported_platforms = ["linux", "windows", "osx"]
    version = (0, 1, 2)  # The version number of this plugin
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
                LOGGER.info(f"detected new {device=}")
            LOGGER.info(f"returning {device=}")
            return device
        except Exception as e:
            LOGGER.warning(f"No device detected {e=}", exc_info=True)
            device = None
            return None

    @log_args_kwargs
    def debug_managed_device_detection(self, devices_on_system, output: IO):
        LOGGER.warning(
            "----- TODO: Should write information about the devices detected on the system to output, which is a file like object."
        )
        return self.detect_managed_devices(devices_on_system, False)

    @log_args_kwargs
    def books(self, oncard=None, end_session=True):
        # settings = self.settings_obj()
        # return rm_web_interface.query_tree(settings.IP, "").ls_recursive()
        booklists = (RemarkableBookList(), None, None)
        booklist0, _, _ = self.sync_booklists(booklists)
        return booklist0

    def _create_upload_path(self, mdata, fname):
        from calibre.devices.utils import create_upload_path  # type: ignore
        from calibre.utils.filenames import ascii_filename as sanitize  # type: ignore

        return create_upload_path(
            mdata,
            fname,
            self.save_template(),
            sanitize,
            prefix_path="",
            path_type=posixpath,
            maxlen=250,
            use_subdirs="/" in self.save_template(),
            news_in_folder=self.NEWS_IN_FOLDER,
        )

    @log_args_kwargs
    def upload_books(self, files_original, names, on_card=None, end_session=True, metadata: list[Metadata] = None):
        locations = []
        self.progress = 0.0
        settings = self.settings_obj()

        if not metadata:
            metadata = [None] * len(files_original)
        step = 100 / len(files_original)
        has_ssh = rm_ssh.test_connection(settings)
        existing_folders = rm_web_interface.query_tree(settings.IP, "").ls_dir_recursive_dict() if has_ssh else {}
        needs_reboot = False
        for local_path, visible_name, m in zip(files_original, names, metadata):
            folder_id = ""
            folder_id_final = ""
            is_new_folder = False
            title = m.get("title") or "UNKNOWN"
            upload_path = title
            if has_ssh:
                upload_path = self._create_upload_path(m, title)
                upload_path = "/".join(upload_path.split("/")[:-1]) + "/" + title
                if upload_path:
                    parts = upload_path.split("/")
                    parts = parts[:-1]
                    parent_folder_id = ""
                    for i in range(len(parts)):
                        part_full = "/".join(parts[: i + 1])
                        LOGGER.debug(
                            f"Looking if {part_full=} already exists on remarkable",
                        )
                        folder_id_final = existing_folders.get(part_full)
                        LOGGER.debug(f"{folder_id_final=}")
                        if not folder_id_final:
                            part_name = parts[i]
                            folder_id_final = rm_ssh.mkdir(settings, part_name, parent_folder_id)
                            existing_folders[part_full] = folder_id_final
                            needs_reboot = True
                            LOGGER.debug(f"after mkdir {folder_id_final=}")
                            is_new_folder = True
                        parent_folder_id = folder_id_final
            locations.append(upload_path)

            if is_new_folder:
                rm_web_interface.upload_file(settings.IP, local_path, "", title)
                LOGGER.debug(f"{folder_id=} != {folder_id_final=}")
                if has_ssh:
                    file_id = rm_ssh.get_latest_upload_id(settings)
                    rm_ssh.sed(settings, f"{file_id}.metadata", '"parent": ""', f'"parent": "{folder_id_final}"')
                    needs_reboot = True
            else:
                rm_web_interface.upload_file(settings.IP, local_path, folder_id_final, visible_name)

            self.progress += step

        if needs_reboot and has_ssh:
            rm_ssh.xochitl_restart(settings)
        self.progress = 100.0

        return (locations, metadata, None)

    @log_args_kwargs
    def open(self, connected_device, library_uuid):
        pass

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
        return 999999999, -1, -1

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
        return 999999999, -1, -1

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
    def sync_booklists(self, booklists: tuple[RemarkableBookList, list, list], end_session=True):
        settings = self.settings_obj()
        if not rm_ssh.test_connection(settings) or booklists is None:
            return RemarkableBookList(), None, None

        booklist0, _, _ = booklists
        try:
            existing_docs = rm_web_interface.query_tree(settings.IP, "").ls_recursive()
            LOGGER.info("Attempting to open existing calibre file on device")
            json_on_device = json.loads(rm_ssh.cat(settings, settings.CALIBRE_METADATA_PATH)) or []
            booklist_on_device = [
                b for b in map(lambda x: RemarkableBook(**x), json_on_device) if b.path in existing_docs
            ]
            LOGGER.info("got booklist_on_device=%s", booklist_on_device)
        except:
            LOGGER.warning("Unable to get metadata", exc_info=True)
            rm_ssh.init_metadata(settings)
            booklist_on_device = []

        # TOOD optimize this, maybe somehow hash RemarkableBookList
        for book in booklist0:
            if book not in booklist_on_device:
                booklist_on_device.append(book)

        with tempfile.NamedTemporaryFile("w+t", delete=False) as fp:
            content = json.dumps([asdict(x) for x in booklist_on_device], indent=1)
            fp.write(content)
            fp.flush()
            rm_ssh.scp(settings, fp.name, settings.CALIBRE_METADATA_PATH)

        LOGGER.info("booklist_on_device=%s", booklist_on_device)
        LOGGER.info("booklist0=%s", booklist0)
        # Make sure our local booklist matches what's on the device too
        for book in booklist_on_device:
            if book not in booklist0:
                LOGGER.info("Adding book %s", book)
                booklist0.add_book(book)

        return booklist0, None, None

    @log_args_kwargs
    def prepare_addable_books(self, paths):
        return super().prepare_addable_books(paths)

    @log_args_kwargs
    def delete_books(self, paths, end_session=True):
        """
        Delete books at paths on device.
        """
        raise NotImplementedError()

    @classmethod
    def remove_books_from_metadata(cls, paths, booklists):
        booklist0: RemarkableBookList = booklists[0]
        to_remove = []
        for book in booklist0:
            if book.path in paths:
                to_remove.append(book)

        for book in to_remove:
            booklist0.remove_book(book)

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
        return None, None

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
        pass

    @log_args_kwargs
    def post_yank_cleanup(self):
        return super().post_yank_cleanup()

    @log_args_kwargs
    def is_dynamically_controllable(self):
        return super().is_dynamically_controllable()

    @classmethod
    @log_args_kwargs
    def add_books_to_metadata(
        cls,
        locations: tuple[list[str], list, list],
        metadata: List[dict],
        booklists: tuple[RemarkableBookList, RemarkableBookList, RemarkableBookList],
    ):
        settings = cls.settings_obj()
        if not rm_ssh.test_connection(settings):
            return

        booklist0, _, _ = booklists
        LOGGER.info(f"Adding books to metadata, locations: {locations}, metadata: {metadata}, booklists: {booklists}")
        for i, m in enumerate(metadata):
            title: str = m.get("title")  # type: ignore
            authors: list[str] = m.get("authors")  # type: ignore
            tags: list[str] = m.get("tags")  # type: ignore
            pubdate = m.get("pubdate")
            size = m.get("size")
            uuid: str = m.get("uuid")  # type: ignore
            path = locations[0][i]
            b = RemarkableBook(
                title=title,
                path=path,
                uuid=uuid,
            )
            if b not in booklist0:
                booklist0.add_book(b, None)
