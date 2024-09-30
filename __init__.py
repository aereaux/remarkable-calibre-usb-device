from dataclasses import dataclass
from calibre.devices.interface import DevicePlugin

# from . import resync
import random
import os
import shutil

print(
    "----------------------------------- LOAD REMARKABLE PLUGIN ------------------------"
)
device = None


def dummy_set_progress_reporter(*args, **kwargs):
    print("dummy_set_progress_reporter")
    return 100


def log_args_kwargs(func):
    def wrapper(*args, **kwargs):
        print(
            f"__ calibre-remarkable-usb-device call: {func.__name__}, Arguments: {args}, Keyword Arguments: {kwargs}"
        )
        return func(*args, **kwargs)

    return wrapper


@dataclass
class RemarkableDeviceDescription:
    IP = "http://10.11.99.1/"

    def __init__(self):
        self.random_id = random.randint(0, 9999999999999)

    def __str__(self) -> str:
        return f"Remarkable on {self.IP}, id={self.random_id}"


class RemarkableUsbDevice(DevicePlugin):
    name = "Remarkable Plugin for Calibre, Andri"
    description = "Send files to Remarkable"
    author = "Andri Rakotomalala"
    supported_platforms = ["linux", "windows", "osx"]
    version = (1, 2, 3)  # The version number of this plugin
    minimum_calibre_version = (0, 7, 53)

    FORMATS = ["epub", "pdf"]
    CAN_SET_METADATA = []
    MANAGES_DEVICE_PRESENCE = True

    @log_args_kwargs
    def startup(self):
        super().startup()

    @log_args_kwargs
    def detect_managed_devices(self, devices_on_system, force_refresh=False):
        global device
        try:
            if device is None:
                # resync.open_connection()
                device = RemarkableDeviceDescription()
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
        print("---------------- books")
        # return resync.get_toplevel_files()
        return []

    @log_args_kwargs
    def upload_books(
        self, files_original, names, on_card=None, end_session=True, metadata=None
    ):
        print(f"pushing {files_original}")
        # TODO rename in another temp folder
        files = []
        for path_old, visible_name in zip(files_original, names):
            cryptic_name, directory = (
                os.path.basename(path_old),
                os.path.dirname(path_old),
            )
            path_new = os.path.join(directory, f"{visible_name}")
            shutil.copy(path_old, path_new)
            files.append(path_new)
        print(files)
        # resync.push(files)

    @log_args_kwargs
    def open(self, connected_device, library_uuid):
        print(f"opening {connected_device}")
#        raise NotImplementedError()

    @log_args_kwargs
    def is_usb_connected(self, devices_on_system, debug=False, only_presence=False):
        global device
        return True, device

    @log_args_kwargs
    def eject(self):
        global device
        # resync.close_connection()
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
        pass # on remarkable, metadata will be automatically be updated

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
        print("add_books_to_metadata")


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
