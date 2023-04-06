#!/bin/sh
# Usage: chmod +x take_ss.sh; Connect to a single android device, transport_id not supported.
# Pulls screenshot from Android device to notebooks/yolo_images/scraped_images/

# ./take_ss.sh <filename>
# (appium) killuh@killuhwhale:~/ws_p38/appium/src$ ./take_ss.sh helios_demo
adb shell screencap -p /sdcard/screenshot.png && adb pull /sdcard/screenshot.png notebooks/yolo_images/scraped_images/$1.png
