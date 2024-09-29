from dataclasses import dataclass
from calibre.devices.interface import DevicePlugin
#from . import resync
import random
import os
import shutil

print("----------------------------------- LOAD REMARKABLE PLUGIN ------------------------")
device = None


def dummy_set_progress_reporter(*args, **kwargs):
    print("dummy_set_progress_reporter")
    return 100


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

    def startup(self):
        print("startup")
        super().startup()

    def detect_managed_devices(self, devices_on_system, force_refresh=False):
        print("detect_managed_devices")
        global device
        try:
            if device is None:
                #resync.open_connection()
                device = RemarkableDeviceDescription()
                print(f"detected new {device}")
            print(f"returning device={device}")
            return device
        except Exception as e:
            print(f"No device detected {e}")
            device = None
            return None

    def debug_managed_device_detection(self, devices_on_system, output):
        print(
            "Should write information about the devices detected on the system to output, which is a file like object."
        )
        return True

    def books(self, oncard=None, end_session=True):
        print("---------------- books")
        #return resync.get_toplevel_files()
        return [

        ]

    def upload_books(
        self, files_original, names, on_card=None, end_session=True, metadata=None
    ):
        print("pushing")
        # TODO rename in another temp folder
        files = []
        for path_old, name in zip(files_original, names):
            filename, directory = os.path.basename(path_old), os.path.dirname(path_old)
            path_new = os.path.join(directory, f"{name} - {filename}")
            shutil.copy(path_old, path_new)
            files.append(path_new)
        print(files)
        #resync.push(files) 

    def open(self, connected_device, library_uuid):
        print(f"opening {connected_device}")

    def is_usb_connected(self, devices_on_system, debug=False, only_presence=False):
        print("is_usb_connected")
        global device
        return True, device

    def eject(self):
        global device
        print("ejecting")
        #resync.close_connection()
        device = None

    def get_device_information(self, end_session=True):
        print("get_device_information")
        global device
        if device is not None:
            return (str(device), 1, 1, "application/epub")

    def total_space(self, end_session=True):
        print("total_space")
        return 0

    def get_driveinfo(self):
        print("get_driveinfo")
        return super().get_driveinfo()

    def get_device_uid(self):
        print("get_device_uid")
        return device.random_id

    def get_file(self, path, outfile, end_session=True):
        print("get_file")
        return super().get_file(path, outfile, end_session)

    def get_option(self, opt_string, default=None):
        print("get_option")
        return super().get_option(opt_string, default)

    def get_user_blacklisted_devices(self):
        print("get_user_blacklisted_devices")
        return super().get_user_blacklisted_devices()

    def set_driveinfo_name(self, location_code, name):
        print("set_driveinfo_name")
        return super().set_driveinfo_name(location_code, name)

    def set_library_info(self, library_name, library_uuid, field_metadata):
        print("set_library_info")
        return super().set_library_info(library_name, library_uuid, field_metadata)

    def set_option(self, opt_string, opt_value):
        print("set_option")
        return super().set_option(opt_string, opt_value)

    def set_plugboards(self, plugboards, pb_func):
        print("set_plugboards")
        return super().set_plugboards(plugboards, pb_func)

    def set_progress_reporter(self, report_progress):
        print("set_progress_reporter")
        return dummy_set_progress_reporter

    def set_user_blacklisted_devices(self, devices):
        print("set_user_blacklisted_devices")
        return super().set_user_blacklisted_devices(devices)

    def shutdown(self):
        print("shutdown")
        return super().shutdown()

    def synchronize_with_db(self, db, book_id, book_metadata, first_call):
        print("synchronize_with_db")
        return super().synchronize_with_db(db, book_id, book_metadata, first_call)

    def free_space(self, end_session=True):
        print("free_space")
        return -1

    def temporary_file(self, suffix):
        print("temporary_file")
        return super().temporary_file(suffix)

    def test_bcd(self, bcdDevice, bcd):
        print("teszt_bcd")
        return super().test_bcd(bcdDevice, bcd)

    def specialize_global_preferences(self, device_prefs):
        print("specialize_global_preferences")
        return super().specialize_global_preferences(device_prefs)

    def start_plugin(self):
        print("start_plugin")
        return super().start_plugin()

    def stop_plugin(self):
        print("stop_plugin")
        return super().stop_plugin()

    def sync_booklists(self, booklists, end_session=True):
        print("sync_booklists")
        return super().sync_booklists(booklists, end_session)

    def prepare_addable_books(self, paths):
        print("prepare_addable_books")
        return super().prepare_addable_books(paths)

    def delete_books(self, paths, end_session=True):
        print("delete_books")
        return super().delete_books(paths, end_session)

    def do_user_config(self, parent=None):
        print("do_user_config")
        return super().do_user_config(parent)

    def can_handle(self, device_info, debug=False):
        print("can_handle")
        return super().can_handle(device_info, debug)

    def can_handle_windows(self, usbdevice, debug=False):
        print("can_handle_windows")
        return super().can_handle_windows(usbdevice, debug)

    def card_prefix(self, end_session=True):
        print("card prefix")
        return ("/prefix1", "/prefix2")

    def cli_main(self, args):
        print("cli_main")
        return super().cli_main(args)

    def customization_help(self, gui=False):
        print("customization_help")
        return super().customization_help(gui)

    def is_customizable(self):
        print("is_customizable")
        return super().is_customizable()

    def ignore_connected_device(self, uid):
        print("ignore_connected_device")
        return super().ignore_connected_device(uid)

    def post_yank_cleanup(self):
        print("post_yank_cleanup")
        return super().post_yank_cleanup()

    def is_dynamically_controllable(self):
        print("is_dynamically_controllable")
        return super().is_dynamically_controllable()

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
