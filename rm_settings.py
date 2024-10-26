from dataclasses import dataclass


@dataclass
class RemarkableSettings:
    IP: str
    SSH_PASSWORD: str

    CALIBRE_METADATA_PATH = "~/.calibre_remarkable_usb_device.metadata"
