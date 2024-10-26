
Sync your epub/pdf to Remarkable with Calibre
==========================================================
This Calibre plugin implements Calibre's [Device Plugin](https://manual.calibre-ebook.com/plugins.html#module-calibre.devices.interface),
making the Remarkable  Tablet a device Calibre can communicate with, similar to other supported Ebook readers.

The plugin will create the necessary folder structure (by default under `calibre/{author_sort}/{title} - {authors}`, News feeds are uploaded to a separate folder `News`)

Requirements
------------
This plugin relies on the USB web interface but optionally heavily relies on SSH for a lot of features (organizing books into folders, lookup for books on device, etc.)

If you wish to benefit of the full features, please setup SSH and ensure that you can successfully SSH to your Remarkable tablet (see [here](https://support.remarkable.com/s/article/Developer-mode) and [here](https://remarkable.guide/guide/access/ssh.html)).

Installation
------------
[Download](https://github.com/andriniaina/remarkable-calibre-usb-device/releases/latest) the zip file, and install it in Calibre via the Plugin interface (from the main screen: `Preferences-->Plugins-->Load plugin from file`).

Configuration
-------------
Go to `Preferences-->Plugins-->Show only user installed plugins`, select the plugin and then `Customize plugin`

![](img/calibre_settings.png)

SSH password can be empty if you have setup an SSH certificate.

Usage
-----
At Calibre startup, the plugin will attempt to find your Remarkable device (by default on ip address 10.11.99.1). If it succeeds you should see "Device" button at the top which shows your books on your Remarkable Tablet.

To send a book to your Remarkable Tablet, right click on the book, select "send to device" and then "send to main memory". The book will transfer and you should now see your book in the Device tab.

![](img\calibre_send_to_device.png)

If you start Calibre and you don't see the Device tab, most likely Calibre was not able to find or connect to your Remarkable tablet. Try running Calibre in debug using `calibre-debug -g` and see the messages in the console regarding trying to connect to the device.

Donate
------

[here](https://github.com/sponsors/andriniaina) or on [patreon](https://patreon.com/andriniaina)

Thanks
------

* [Calibre](https://github.com/kovidgoyal/calibre) for making a great ebook manager.
* [naclander](https://github.com/naclander/Calibre-Remarkable-Device-Driver-Plugin) for the initial plugin.

All developers in the Remarkable community.
