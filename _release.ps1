mkdir release -Force
rm .\release\* -Recurse -Force
cp * release -Exclude img,release,.* -Force -Recurse
cd release

Compress-Archive * -CompressionLevel Fastest -DestinationPath remarkable-calibre-usb-device.zip
rm * -Force -Recurse -Exclude remarkable-calibre-usb-device.zip
