from copy import deepcopy
from dataclasses import dataclass
import json
import logging
from appium.webdriver.appium_service import AppiumService
import __main__
from datetime import datetime
import os
import re
import subprocess
from enum import Enum
from time import time
from typing import AnyStr, Dict, List, Tuple, Union
import cv2
import numpy as np


class _CONFIG:
    login_facebook =  False
    multi_split_packages = False
    debug_print = False


CONFIG = _CONFIG()
BASE_PORT = 4723

weights = 'notebooks/yolov5/runs/train/exp007/weights/best_309.pt'
weights = 'notebooks/yolov5/runs/train/exp4/weights/best.pt'  # Lastest RoboFlow Model V1
weights = 'notebooks/yolov5/runs/train/exp6/weights/best.pt'  # Lastest RoboFlow Model V2
weights = 'notebooks/yolov5/runs/train/exp7/weights/best.pt'  # Lastest RoboFlow Model V3
WEIGHTS = 'notebooks/yolov5/runs/train/exp8/weights/best.pt'  # Lastest RoboFlow Model V4

# Ip Address of machien Running Appium Server
EXECUTOR = 'http://192.168.0.175:4723/wd/hub'
PLAYSTORE_PACKAGE_NAME = "com.android.vending"
PLAYSTORE_MAIN_ACT = "com.google.android.finsky.activities.MainActivity"
FACEBOOK_PACKAGE_NAME = "com.facebook.katana"
FACEBOOK_APP_NAME = "Facebook"

# Labels for YOLOv5
LOGIN = 'loginfield'
PASSWORD = 'passwordfield'
CONTINUE = 'Continue'
GOOGLE_AUTH = 'GoogleAuth'
FB_ATUH = 'Facebook Auth'
SIGN_IN = 'Sign In'

IMAGE_LABELS = [
    LOGIN,
    PASSWORD,
    CONTINUE,
    GOOGLE_AUTH,
    FB_ATUH,
    SIGN_IN
]

ACCOUNTS = None
with open(f"{os.path.expanduser( '~' )}/accounts.json", 'r') as f:
    ACCOUNTS = json.load(f)
print(f"{ACCOUNTS=}")
class ArcVersions(Enum):
    '''
        Enumeration for each Android Version we intend to support.
    '''
    UNKNOWN = -1
    ARC_P = 9
    ARC_R = 11

class BuildChannels(Enum):
    '''
        Enumeration for each build channel on for ChromeOS.
    '''
    STABLE = 'stable'
    BETA = 'beta'
    DEV = 'dev'
    CANARY = 'canary'
    NOT_CHROMEOS = 'Android device is not running on ChromeOS'

    @staticmethod
    def get_channel(channel: str) -> 'BuildChannels':
        if channel == BuildChannels.STABLE.value:
            return BuildChannels.STABLE
        elif channel == BuildChannels.BETA.value:
            return BuildChannels.BETA
        elif channel == BuildChannels.DEV.value:
            return BuildChannels.DEV
        elif channel == BuildChannels.CANARY.value:
            return BuildChannels.CANARY
        else:
            return BuildChannels.NOT_CHROMEOS

class CrashTypes(Enum):
    '''
        Enumeration for the result when checking if a program crashed.
    '''
    SUCCESS = "Success"
    WIN_DEATH = "Win Death"
    FORCE_RM_ACT_RECORD = "Force removed ActivityRecord"
    ANR = "App not responding"
    FDEBUG_CRASH = "F DEBUG crash"

class DEVICES(Enum):
    '''
        Enumeration for device_names as reported via ADB getprop device name.
    '''
    KEVIN = "kevin"
    COACHZ = "coachz"
    EVE = "eve"
    HELIOS = "helios"
    TAIMEN = "taimen"
    CAROLINE = "caroline"
    KOHAKU = "kohaku"
    KRANE = "krane"
    UNKNOWN = "unknown"


    @staticmethod
    def get_device(device_name: str) -> 'DEVICES':
        if device_name == DEVICES.KEVIN.value:
            return DEVICES.KEVIN
        elif device_name == DEVICES.COACHZ.value:
            return DEVICES.COACHZ
        elif device_name == DEVICES.EVE.value:
            return DEVICES.EVE
        elif device_name == DEVICES.HELIOS.value:
            return DEVICES.HELIOS
        elif device_name == DEVICES.TAIMEN.value:
            return DEVICES.TAIMEN
        elif device_name == DEVICES.CAROLINE.value:
            return DEVICES.CAROLINE
        elif device_name == DEVICES.KOHAKU.value:
            return DEVICES.KOHAKU
        elif device_name == DEVICES.KRANE.value:
            return DEVICES.KRANE
        else:
            return DEVICES.UNKNOWN



# APK & Manifest stuff
@dataclass(frozen=True)
class AppData:
    ''' Represents app information to capture. '''
    name: str
    versionCode: str
    versionName: str
    compileSdkVersion: str
    compileSdkVersionCodename: str
    is_pwa: bool
    is_game: bool

class AppInfo:
    '''
        Manages the process of pulling APK from device, extracting the
         manifest text and parsing the manifest text for the information in @
         dataclass AppData

        package: name='air.com.lunime.gachaclub' versionCode='1001001' versionName='1.1.0'

        package: name='com.plexapp.android' versionCode='855199985' versionName='9.15.0.38159' compileSdkVersion='33' compileSdkVersionCodename='13'
        package: name='com.tumblr' versionCode='1280200110' versionName='28.2.0.110' compileSdkVersion='33' compileSdkVersionCodename='13'

        .split(" ") => ['package:', "name='com.tumblr'", "versionCode='855199985'"]
        skip index=0
        split("=") => ["name", "'com.tumblr'"]
        remove quotes from index 1
        .replace("'", "")
        Then create a dict from the list of lists.
    '''
    def __init__(self, transport_id: str, package_name: str):
        self.transport_id = transport_id
        self.package_name = package_name
        self.__info = {
                'name': '',
                'versionCode': '',
                'versionName': '',
                'compileSdkVersion': '',
                'compileSdkVersionCodename': '',
                'is_pwa': False,
                'is_game': False
            }
        self.__process_app()

    def __get_aapt_version(self) -> str:
        ''' Get the latest version of aapt on host device.

            Returns:
             - path of the latest version of aapt installed on host device.
        '''
        android_home = os.environ.get("ANDROID_HOME")
        # aapt = f"{android_home}/build-tools/*/aapt"
        aapt = f"{android_home}/build-tools/"
        items = os.listdir(aapt)

        # Iterate over the items
        for item in items[::-1]:
            return  os.path.join(aapt, item, "aapt")
        return ""

    def __check_chromium_webapk(self, manifest: str) -> bool:
        ''' Checks app's manifest to detect if the app is a PWA.

            Args:
             - manifest: A str containing the entire manifest text.

            Returns:
             - True if org.chromium.webapk.shell_apk is present in the manifest text.
        '''
        pattern = r".*org\.chromium\.webapk\.shell_apk.*"
        matches = re.findall(pattern, manifest, flags=re.MULTILINE)
        print(f"{matches=}")
        return True if matches else False

    def __get_apk(self) -> bool:
        ''' Grabs the APK from device.

            adb shell pm path package_name

            package:/data/app/~~-TjCwRkZEFass6mjqTzMtg==/com.netflix.mediaclient-mPHhWQM2xwIJco8coL6OYg==/base.apk
            # package:/data/app/~~-TjCwRkZEFass6mjqTzMtg==/com.netflix.mediaclient-mPHhWQM2xwIJco8coL6OYg==/split_config.en.apk
            # package:/data/app/~~-TjCwRkZEFass6mjqTzMtg==/com.netflix.mediaclient-mPHhWQM2xwIJco8coL6OYg==/split_config.mdpi.apk
            # package:/data/app/~~-TjCwRkZEFass6mjqTzMtg==/com.netflix.mediaclient-mPHhWQM2xwIJco8coL6OYg==/split_config.x86_64.apk

            JUST NEED BASE APK FOR MAIN INFO

            Grabs APK via ADB PULL /path/to/apk
            and stores it in /apks/<package_name>

            Returns:
             - True when APK is in required location. False otherwise.
        '''
        print("Gettign APK ", self.package_name)

        if not is_package_installed(self.transport_id, self.package_name):
            return False

        root_path = get_root_path()
        dl_dir = f"{root_path}/apks/{self.package_name}"
        create_dir_if_not_exists(dl_dir)

        does_exist = file_exists(f"{root_path}/apks/{self.package_name}/base.apk")
        if does_exist:
            return True

        cmd = ('adb', '-t', self.transport_id, 'shell', 'pm', 'path', self.package_name )
        print("File exists ", does_exist)
        outstr = subprocess.run(cmd, check=True, encoding='utf-8',
                                    capture_output=True).stdout.strip()
        apk_path = None
        for line in outstr.split("\n"):
            if 'base.apk' in line and not "asset" in line:
                apk_path = line[len("package:"):]

        print(f"Found apk path: {apk_path}")



        print("Pulling APK: ", self.package_name, dl_dir)

        cmd = ('adb', '-t', self.transport_id, 'pull', apk_path, dl_dir )
        outstr = subprocess.run(cmd, check=True, encoding='utf-8',
                                    capture_output=True).stdout.strip()

        return True

    def __download_manifest(self) -> str:
        ''' Grabs Manifest from the APK using aapt dump bading.

            Returns:
                - the manifest text.
        '''
        # /Android/Sdk/tools/bin/apkanalyzer manifest print /path/to/app.apk
        #     N: android=http://schemas.android.com/apk/res/android
        #   E: manifest (line=0)
        #     A: android:versionCode(0x0101021b)=(type 0x10)0xc49f
        #     A: android:versionName(0x0101021c)="8.52.2 build 14 50335" (Raw: "8.52.2 build 14 50335")
        # Need to download APK tho....
        # aapt dump badging my.apk | sed -n "s/.*versionName='\([^']*\).*/\1/p"
        # ./aapt2 dump xmltree --file AndroidManifest.xml /home/killuh/Downloads/com.netflix.mediaclient_8.52.2\ build\ 14\ 50335.apk
        # ./aapt dump xmltree /home/killuh/Downloads/com.netflix.mediaclient_8.52.2\ build\ 14\ 50335.apk AndroidManifest.xml
        # ./aapt dump xmltree app.apk AndroidManifest.xml


        aapt = self.__get_aapt_version()
        root_path = get_root_path()
        manifest_path = f"{root_path}/apks/{self.package_name}/manifest.txt"
        apk_path = f"{root_path}/apks/{self.package_name}/base.apk"

        if file_exists(manifest_path):
            with open(manifest_path, 'r', encoding='utf-8') as f:
                return f.read()
        manifest = ""
        try:
            cmd = (aapt, "dump", "badging", apk_path)
            manifest = subprocess.run(cmd, check=False, encoding='utf-8',
                                    capture_output=True).stdout.strip()
        except Exception as error:
            print("Error getting manifest: ", error)
            return manifest

        with open(manifest_path, 'w', encoding='utf-8') as f:
            f.write(manifest)

        return manifest

    def __populate_app_info(self, manifest_text: str)  -> dict:
        ''' Populates the App information from manifest text.

            Args:
             - manifest_text: Text from the apps manifest file in the APK.
        '''
        if not manifest_text:
            return Dict()
        info_line = manifest_text.split("\n")[0]

        try:
            parts = info_line.split(" ")[1: ]
            for part in parts:
                pieces = part.split("=")
                pieces[1].replace("'", "")
                self.__info[pieces[0]] = pieces[1]
        except Exception as error:
            print("Error w/ __get_app_info: ", error)

        self.__info['is_pwa'] = self.__check_chromium_webapk(manifest_text)


    def __has_surface_name(self) -> bool:
        ''' Checks SurfaceFlinger for a surface matching the package name.

            Returns:
                - True if there is a matching surface name.
        '''
        pattern_with_surface = rf"""^SurfaceView\s*-\s*(?P<package>{self.package_name})/[\w.#]*$"""                    # Surface window
        re_surface = re.compile(pattern_with_surface, re.MULTILINE | re.IGNORECASE | re.VERBOSE)
        cmd = ('adb', '-t', self.transport_id, 'shell', 'dumpsys', 'SurfaceFlinger', '--list')
        surfaces_list = subprocess.run(cmd, check=True, encoding='utf-8', capture_output=True).stdout.strip()
        last = None
        for match in re_surface.finditer(surfaces_list):
            print(f"Found match: ", match)
            last = match
        if last:
            if self.package_name != last.group('package'):
                return False
            # UE4 games have at least two SurfaceView surfaces. The one
            # that seems to in the foreground is the last one.
            # return last.group()
            return True

        # Some apps will report a surface in use but will not have a SurfaceView.
        # E.g. Facebook messenger has surfaces views present while the user is on the login screen but it does not report a 'SurfaceView'

        # pattern_without_surface = rf"""^(?P<package>{package_name})/[\w.#]*$"""
        # re_without_surface = re.compile(pattern_without_surface, re.MULTILINE | re.IGNORECASE | re.VERBOSE)
        # # Fallback: SurfaceView was not found.
        # matches_without_surface = re_without_surface.search(surfaces_list)
        # if matches_without_surface:
        #     if package_name != matches_without_surface.group('package'):
        #         return False
        #         # return (f'Surface not found for package {package_name}. '
        #         #                 'Please ensure the app is running.')
        #     # return matches_without_surface.group()
        #     return True
        return False

    def __process_app(self) -> Union[AppData, None]:
        ''' Downloads APK & manifest from App and extracts information from Manifest.

            Returns:
                - A dict containing the app's information.
        '''
        if self.__get_apk():
            manifest = self.__download_manifest()
            if not manifest:
                p_alert("No manifest found.")
                return None
            self.__info = self.__populate_app_info(manifest)
            self.__info['is_game'] = self.__has_surface_name()

    def info(self):
        return AppData(**self.__info)

@dataclass(frozen=True)
class DeviceData:
    ip: str
    transport_id: str
    is_emu: bool
    arc_version: str
    device_name: str
    channel: str
    wxh: str
    arc_build: str
    product_name: str

class Device:
    def __init__(self, ip: str):
        self.__is_connected = self.__adb_connect(ip)
        self.__transport_id = self.__find_transport_id(ip)
        self.__device_info = {
            'ip': ip,
            'transport_id': self.__transport_id,
            'is_emu': self.__is_emulator(),
            'arc_version': self.__get_arc_version(),
            'device_name': self.__get_device_name(),
            'channel': self.__get_device_build_channel(),
            'wxh': self.__get_display_size(),
            'arc_build': self.__get_arc_build(),
            'product_name': self.__get_product_name(),
        }

    def __str__(self):
        return f"{self.__device_info['device_name']}({self.__device_info['arc_version']}): {self.__device_info['channel']} - {self.__device_info['arc_build']} - {self.__device_info['product_name']}"

    def is_connected(self):
        return self.__is_connected

    def __adb_connect(self, ip: str):
        '''
            Connects device via ADB

            Params:
                ip: ip_address on local network of device to connect to.

            Returns:
                A boolean representing if the connection was successful.
        '''
        try:
            cmd = ('adb', 'connect', ip)
            outstr = subprocess.run(cmd, check=True, encoding='utf-8',
                                    capture_output=True).stdout.strip()
            if outstr.startswith("failed to connect to"):
                raise Exception(outstr)
            print(outstr)
        except Exception as err:
            print("Error connecting to ADB", err)
            return False
        return True

    def __find_transport_id(self, ip_address)-> str:
        ''' Gets the transport_id from ADB devices command.

            ['192.168.1.113:5555', 'device', 'product:strongbad', 'model:strongbad',
                'device:strongbad_cheets', 'transport_id:1']

            Params:
                ip_address: A string representing the name of the device
                    according to ADB devices, typically the ip address.

            Returns:
                A string representing the transport id for the device matching the
                    @ip_adress

        '''
        cmd = ('adb', 'devices', '-l')
        outstr = subprocess.run(cmd, check=True, encoding='utf-8', capture_output=True).stdout.strip()
        # Split the output into a list of lines
        lines = outstr.split("\n")
        for line in lines:
            # Split the line into words
            words = line.split()
            if ip_address in words:
                # The transport ID is the last word in the line
                return words[-1].split(":")[-1]
        # If the IP address was not found, return None
        return '-1'

    def __is_emulator(self):
        ''' Checks if device is an emulator.

            Params:
                transport_id: The transport id of the connected android device.

            Returns:
                A boolean representing if it's an emulator or not.
        '''

        cmd = ('adb','-t', self.__transport_id, 'shell', 'getprop', "ro.build.characteristics")
        try:
            res = subprocess.run(cmd, check=False, encoding='utf-8', capture_output=True).stdout.strip()
            return res == "emulator"
        except Exception as err:
            print("Failed to check for emualtor", err)
        return False

    def __get_arc_version(self):
        ''' Gets Android OS version on connected device.

            Params:
                self.transport_id: The transport id of the connected android device.

            Returns:
                An ENUM representing the Android Version [P, R] else None if
                    release if not found from ADB getprop.


        '''
        cmd = ('adb','-t', self.__transport_id, 'shell', 'getprop', "ro.build.version.release")
        try:
            res = subprocess.run(cmd, check=False, encoding='utf-8', capture_output=True).stdout.strip()
            # print("Arc version: ", res)
            if res == "9":
                return ArcVersions.ARC_P
            elif res == "11":
                return ArcVersions.ARC_R
            else:
                return ArcVersions.UNKNOWN
        except Exception as err:
            print("Cannot find Android Version", err)
        return None

    def __get_device_name(self):
        ''' Gets name of connected device.

            Returns:
                An ENUM representing the Android Version [P, R] else None if
                    release if not found from ADB getprop.


        '''
        cmd = ('adb','-t', self.__transport_id, 'shell', 'getprop', "ro.product.board")
        try:
            res = subprocess.run(cmd, check=False, encoding='utf-8', capture_output=True).stdout.strip()
            return res
        except Exception as err:
            print("Cannot find device name", err)
        return None

    def __get_device_build_channel(self):
        ''' Gets build channel of connected device.

            Returns:
                An ENUM representing the Build Channel.


        '''
        cmd = ('adb','-t', self.__transport_id, 'shell', 'getprop', "ro.boot.chromeos_channel")
        try:
            res = subprocess.run(cmd, check=False, encoding='utf-8', capture_output=True).stdout.strip()
            return BuildChannels.get_channel(res)
        except Exception as err:
            print("Cannot find device name", err)
        return None

    def __get_display_size(self):
        ''' Determines the devices current display size.
                adb shell wm size
        '''
        cmd = ('adb','-t', self.__transport_id, 'shell', 'wm', "size")
        try:
            res = subprocess.run(cmd, check=False, encoding='utf-8', capture_output=True).stdout.strip()
            size_str = res.split(": ")[1]  # Extract the string after the colon
            width, height = map(int, size_str.split("x"))  # Split the string into width and height, and convert them to integers
            return width, height
        except Exception as err:
            print("Cannot find display size", err)
        return None

    def __get_arc_build(self):
        cmd = ('adb','-t', self.__transport_id, 'shell', 'getprop', "ro.build.display.id")
        try:
            res = subprocess.run(cmd, check=False, encoding='utf-8', capture_output=True).stdout.strip()
            return res
        except Exception as err:
            print("Cannot find display size", err)
        return None

    def __get_product_name(self):
        '''ro.product.name'''
        cmd = ('adb','-t', self.__transport_id, 'shell', 'getprop', "ro.product.name")
        try:
            res = subprocess.run(cmd, check=False, encoding='utf-8', capture_output=True).stdout.strip()
            return res
        except Exception as err:
            print("Cannot find display size", err)
        return None


    def info(self) -> DeviceData:
        return DeviceData(**self.__device_info)

class ErrorDetector:
    ''' Detects crashes from Logcat and ANRs from Dumpsys activity.
    '''
    def __init__(self, transport_id: str, ArcVersion: ArcVersions):
        self.__transport_id = transport_id
        self.__package_name = ""
        self.__ArcVersion = ArcVersion
        self.__start_time = None  # Logcat logs starting at
        self.reset_start_time()

    def get_package_name(self):
        return self.__package_name

    def update_package_name(self, package_name: str):
        self.__package_name = package_name

    def update_transport_id(self, transport_id: str):
        self.__transport_id = transport_id

    def update_arc_version(self, ArcVersion: ArcVersions):
        self.__ArcVersion = ArcVersion

    def __get_logs(self, start_time: str):
        '''Grabs logs from ADB logcat starting at a specified time.

            Params:
                start_time: The formatted string representing the time the app was
                    launched/ started.
                transport_id: The transport id of the connected android device.

            Returns

        '''
        cmd = ('adb', '-t', self.__transport_id, 'logcat', 'time', '-t', start_time)  #
        self.__logs =  subprocess.run(cmd, check=False, encoding='utf-8',
            capture_output=True).stdout.strip()

    def __check_for_win_death(self):
        ''' Searches logs for WIN DEATH record.

            12-28 17:48:37.233   153   235 I WindowManager: WIN DEATH: Window{913e5ce u0 com.Psyonix.RL2D/com.epicgames.ue4.GameActivity}

            Returns:
                A string representing the failing activity otherwise it returns an empty string.
        '''
        # adb logcat -v time -t 10:30:00

        win_death = rf"\d+-\d+\s\d+\:\d+\:\d+\.\d+\s*\d+\s*\d+\s*I WindowManager: WIN DEATH: Window{'{'}.*\s.*\s{self.__package_name}/.*{'}'}"
        win_death_pattern = re.compile(win_death, re.MULTILINE)
        match = win_death_pattern.search(self.__logs)
        if match:
            print(f"{match.group(0)=}")
            failed_activity = match.group(0).split("/")[-1][:-1]
            # print("failed act: ", failed_activity)
            return failed_activity, match.group(0)
        return "", ""

    def __check_force_remove_record(self):
        ''' Searches logs for Force remove ActivtyRecord.

            12-28 17:48:37.254   153  4857 W ActivityManager: Force removing ActivityRecord{f024fcc u0 com.Psyonix.RL2D/com.epicgames.ue4.GameActivity t195}: app died, no saved state

            Returns:
                A string representing the failing activity otherwise it returns an empty string.
        '''

        force_removed = rf"^\d+-\d+\s\d+\:\d+\:\d+\.\d+\s*\d+\s*\d+\s*W ActivityManager: Force removing ActivityRecord{'{'}.*\s.*\s{self.__package_name}/.*\s.*{'}'}: app died, no saved state$"
        force_removed_pattern = re.compile(force_removed, re.MULTILINE)
        match = force_removed_pattern.search(self.__logs)


        if match:
            print(f"{match.group(0)=}")
            failed_activity = match.group(0).split("/")[-1][:-1].split(" ")[0]
            print("failed act: ", failed_activity)
            return failed_activity, match.group(0)
        return "", ""

    def __check_f_debug_crash(self):
        ''' Searches logs for F DEBUG crash logs.

            03-03 14:36:13.060 19417 19417 F DEBUG   : pid: 19381, tid: 19381, name: lay.KingsCastle  >>> com.PepiPlay.KingsCastle <<<
            alskdnlaksndlkasndklasnd
            03-01 15:50:25.856 22026 22026 F DEBUG   : pid: 21086, tid: 21241, name: UnityMain  >>> zombie.survival.craft.z <<<
            alskdnlaksndlkasndklasnd
            [.\s]*F DEBUG[.\s]*>>> zombie.survival.craft.z <<<
            Returns:
                A string representing the failing activity otherwise it returns an empty string.
        '''
        force_removed = rf"[a-zA-Z0-9\s\-\:.,]*F DEBUG[a-zA-Z0-9\s\-\:.,]*>>> {self.__package_name} <<<"
        force_removed_pattern = re.compile(force_removed, re.MULTILINE)
        match = force_removed_pattern.search(self.__logs)

        if match:
            return '', match.group(0)
        return "", ""

    def __check_for_ANR(self) -> bool:
        ''' Checks dumpsys for ANR.
        '''
        dumpsys_act_text = dumpysys_activity(self.__transport_id, self.__ArcVersion)
        return is_ANR(dumpsys_act_text, self.__package_name)

    def check_crash(self)-> Tuple:
        ''' Grabs logcat logs starting at a specified time and check for crash logs.

            Params:
                package_name: The name of the package to check crash logs for.
                start_time: The formatted string representing the time the app was
                    launched/ started.
                transport_id: The transport id of the connected android device.

            Return:
                A string representing the failing activity otherwise it returns an empty string.

        '''
        self.__get_logs(self.__start_time)

        failed_act, match = self.__check_for_win_death()
        if failed_act:
            return (CrashTypes.WIN_DEATH, failed_act, match)

        failed_act, match = self.__check_force_remove_record()
        if failed_act:
            return (CrashTypes.WIN_DEATH, failed_act, match)

        failed_act, match = self.__check_f_debug_crash()
        if match:
            return (CrashTypes.FDEBUG_CRASH, failed_act, match)

        if self.__check_for_ANR():
            return (CrashTypes.ANR, "unknown activity", "ANR detected.")

        return (CrashTypes.SUCCESS, "", "")

    def __get_start_time(self, ):
        '''
            Gets current time and formats it properly to match ADB -t arg.

            This is used at the beginning of a test for an app.
            It will limit the amount logs we will need to search each run.

            Returns a string in the format "MM-DD HH:MM:SS.ms"
        '''
        return datetime.fromtimestamp(time()).strftime('%m-%d %H:%M:%S.%f')[:-3]

    def reset_start_time(self):
        self.__start_time = self.__get_start_time()


class TSV:
    ''' Tranformation layer between persisted storage of list to python list.

        Creates python list from a file is users home dir named self.__filename.

        We can replace this with another class to interact with another data source.

        1. We just read from the data source, in the beginning.
        2. We valdiate apps
        3. At the end, we update the data source wit any new changes.
            So, if we wanted to use a database instead, we just write a new class with same methods:
                - get_apps() -> List
                - update_list(updated_names: Dict)
    '''

    def __init__(self):
        self.__app_list = list()
        self.__filename = "app_list.tsv" # This file should be place in the home dir on linux ~/
        self.__badfilename = "bad_app_list.tsv" # This will be created in the home dir ~/
        self.__failed_app_filename = "failed_app_list.tsv" # This will be created in the home dir ~/
        self.__all_bad_apps = dict()
        self.__home_dir = users_home_dir()
        self.__read_file()
        self.__read_bad_apps()

    def get_apps(self):
        ''' Returns 2D list of apps that will be tested. '''
        return self.__app_list

    def __read_file(self):
        with open(f"{self.__home_dir}/{self.__filename}", 'r' ) as f:
            [self.__app_list.append([w.strip() for w in line.split("\t")]) for line in f.readlines()]

    def __read_bad_apps(self):
        create_file_if_not_exists(f"{self.__home_dir}/{self.__badfilename}")
        with open(f"{self.__home_dir}/{self.__badfilename}", 'r' ) as f:
            bad_apps = {}
            for line in f.readlines():
                app_name, package_name = line.split("\t")
                bad_apps[package_name] = app_name
            self.__all_bad_apps = bad_apps

    def __write_bad_apps(self):
        with open(f"{self.__home_dir}/{self.__badfilename}", 'w') as f:
            pass  # Clear contents

        with open(f"{self.__home_dir}/{self.__badfilename}", 'w') as f:
            for package_name, app_name  in self.__all_bad_apps.items():
                f.write(f"{app_name.strip()}\t{package_name.strip()}\n")

    def export_bad_apps(self, bad_apps: Dict):
        '''
            After test run is completed, updates instance app_list by removing apps that are also in @bad_apps and then writes entire list to file.

            Args:
                - bad_apps: List of apps that are deemed invalid during test run.
        '''
        # Rm bad apps from app_list
        updated_list = [[app_name, package_name] for app_name, package_name in self.__app_list if not package_name in bad_apps]
        # Update app_list
        if not len(self.__app_list) == len(updated_list):
            self.__app_list = updated_list
            # input("Writing new app_list w/out bad apps", updated_list)
            self.__write_file()

        # Update bad list
        self.__all_bad_apps.update(bad_apps)
        self.__write_bad_apps()

    def update_list(self, updated_names: Dict):
        '''  After test run is completed, updates instance app_list with new names and then writes entire list to file.

            Args:
            - updated_names: List of apps that are had mismatched names as compared to the Playstore via web.
        '''
        i = 0
        end  = len(self.__app_list)
        num_updated = 0
        while i < end:
            _app_name, package_name = self.__app_list[i]
            # print(f"{app_name} {package_name} {len(package_name)=} {package_name in updated_names}")
            if package_name in updated_names:
                self.__app_list[i][0] = updated_names[package_name]
                num_updated += 1
            i += 1

        if num_updated:
            self.__write_file()

    def __write_file(self):
        with open(f"{self.__home_dir}/{self.__filename}", 'w' ) as f:
            pass  # Clear contents

        with open(f"{self.__home_dir}/{self.__filename}", 'w' ) as f:
            [f.write(f"{app[0]}\t{app[1]}\n") for app in self.__app_list]

    def write_failed_apps(self, failed_apps: Dict):
        '''
            Logs failed apps per run that failed on all device tested during the run. Not updated each run.

            Failed apps will inlcude apps that aren't available in the region or where the app doesn't appear as the first result or
             if the app shares similar names to other apps like: solitaire

            Args:
             - failed_apps: Apps that failed during test run but are not named wrong and available on playstore.
        '''
        if not len(failed_apps.keys()):
            return

        path = f'{self.__home_dir}/{self.__failed_app_filename}'
        create_file_if_not_exists(path)
        with open(path, 'w'):
            pass

        with open(path, 'w') as f:
            for key in failed_apps:
                f.write(f"{failed_apps[key]}\t{key}\n")


class __AppLogger:
    def __init__(self):
        filename = 'latest_report.txt'
        logger = logging.getLogger('my_logger')
        logger.setLevel(logging.DEBUG)

        # Create a file handler for the logger
        with open(filename, 'w'):
            pass

        file_handler = logging.FileHandler(filename)
        file_handler.setLevel(logging.DEBUG)

        # Create a formatter for the file handler
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)

        # Add the file handler to the logger
        logger.addHandler(file_handler)
        self.logger = logger


    def log(self, *args, **kwargs):
        message = ' '.join(map(str, args)) + kwargs['end']
        self.logger.info(message)

    def print_log(self, *args, **kwargs):
        message = ' '.join(map(str, args))
        self.logger.info(message)
        print(message)

logger = __AppLogger()
##     Colored printing     ##
Red = "\033[31m"
Black = "\033[30m"
Green = "\033[32m"
Yellow = "\033[33m"
Blue = "\033[34m"
Purple = "\033[35m"
Cyan = "\033[36m"
White = "\033[37m"
RESET = "\033[0m"


def p_red(*args, end='\n'):
    print(Red, *args, RESET, end=end)
    logger.log(*args, end=end)
def p_green(*args, end='\n'):
    print(Green, *args, RESET, end=end)
    logger.log(*args, end=end)
def p_yellow(*args, end='\n'):
    print(Yellow, *args, RESET, end=end)
    logger.log(*args, end=end)
def p_blue(*args, end='\n'):
    print(Blue, *args, RESET, end=end)
    logger.log(*args, end=end)
def p_purple(*args, end='\n'):
    print(Blue, *args, RESET, end=end)
    logger.log(*args, end=end)
def p_cyan(*args, end='\n'):
    print(Cyan, *args, RESET, end=end)
    logger.log(*args, end=end)

def p_alert(msg):
    art = r"""
          _ ._  _ , _ ._
        (_ ' ( `  )_  .__)
      ( (  (    )   `)  ) _)
     (__ (_   (_ . _) _) ,__)
         `~~`\ ' . /`~~`
              ;   ;
              /   \
_____________/_ __ \_____________"""
    p_red(art)
    p_blue(msg)
    print()


##      Appium config & stuff  ##
def android_des_caps(device_name: AnyStr, app_package: AnyStr, main_activity: AnyStr) -> Dict:
    '''
        Formats the Desired Capabilities for Appium Server.
    '''
    return {
        'platformName': 'Android',
        'appium:udid': device_name,
        'appium:appPackage': app_package,
        'appium:automationName': 'UiAutomator2',
        'appium:appActivity': main_activity,
        'appium:ensureWebviewHavepages': "true",
        'appium:nativeWebScreenshot': "true",
        'appium:newCommandTimeout': 3600,
        'appium:connectHardwareKeyboard': "true",
        'appium:noReset': True,
        "appium:uiautomator2ServerInstallTimeout": 60000,
    }

def lazy_start_appium_server(port: int):
    ''' Attempts to start Appium server. '''
    try:
        service = AppiumService()
        service.start(args=['--address', '0.0.0.0', '-p', str(port), '--base-path', '/wd/hub'])
        # For some reason, interacting with service before returning has prevented random errors like:
        # Failed to establish a new connection: [Errno 111] Connection refused
        # Remote end closed
        while not service.is_listening or not service.is_running:
            print("Waiting for appium service to listen...")
        return service
    except Exception as error:
        print("Error starting appium server", str(error))
    return None


##          Filesystem stuff     ##
def get_root_path():
    ''' Returns root path /home/user/pathto/appium/src '''
    root_path = os.path.realpath(__main__.__file__).split("/")[1:-1]
    root_path = '/'.join(root_path)
    return f"/{root_path}"

def create_dir_if_not_exists(directory):
    print("Create dir if not exist", directory)
    if not os.path.exists(directory):
        print("Creating dir: ", directory)
        os.makedirs(directory)

def create_file_if_not_exists(path):
    print("Create path if not exist", path)
    if not file_exists(path):
        with open(path, 'w'):
            pass

def file_exists(directory):
    return os.path.exists(directory)

def users_home_dir():
    return os.path.expanduser( '~' )

##              App stuff           ##

def is_ANR(dumpsys_act_text: str, package_name: str) -> bool:
    # TODO confirm this works by finding an APP that throws ANR consistently. OR create an app that crashes.
    ''' Given a string, dumpsys_act_text, determine if an ANR window is present.

        ANR Text:
            mFocusedWindow=Window{afc9fce u0 Application Not Responding: com.thezeusnetwork.www}

        Params:
            dumpsys_act_text: Output from ADB dumpsys activity.
            package: The app's package name.

        Returns True if ANR text is present.
    '''
    regex = rf".*Application Not Responding: {package_name}.*"
    is_ANR_res = re.search(regex, dumpsys_act_text)
    print(f"{is_ANR_res=}")
    return not is_ANR_res is None

def dumpysys_activity(transport_id: str, ArcVersion: ArcVersions) -> str:
    try:
        keyword = ""
        if ArcVersion == ArcVersions.ARC_P:
            keyword = "mResumedActivity"
        if ArcVersion == ArcVersions.ARC_R:
            keyword = "mFocusedWindow"
        cmd = ('adb', '-t', transport_id, 'shell', 'dumpsys', 'activity',
                '|', 'grep', keyword)
        return subprocess.run(cmd, check=False, encoding='utf-8',
            capture_output=True).stdout.strip()
    except Exception as err:
            print("Err dumpysys_activity ", err)
    return ''

def get_cur_activty(transport_id: str, ArcVersion: ArcVersions, package_name: str) -> Dict:
    ''' Gets the current activity running in the foreground.

        ARC-P
            mResumedActivity: ActivityRecord{9588d06 u0 com.netflix.mediaclient/o.cwK t127}
        ARC-R
            mFocusedWindow=Window{b3ef1fc u0 NotificationShade} ## Sleep
            mFocusedWindow=Window{3f50b2f u0 com.netflix.mediaclient/com.netflix.mediaclient.acquisition.screens.signupContainer.SignupNativeActivity}


        Failing on Barnes and Noble => Has pop up asking to join wifi networks...
            text = mFocusedWindow=Window{7cc92bd u0 android}

        Params:
            transport_id: The transport id of the connected android device.
            ArcVersion: ArcVersion Enum for the device.

        Returns:
            - A Dict containing:
                package_name: current focused package.
                act_name: The current focused activity.
                is_ANR_thrown: boolean indicating if ANR window is present.
                ANR_for_package: package name found in ANR message or empty string if is_ANR_thrown is False.
    '''
    MAX_WAIT_FOR_OPEN_APP = 420  # 7 mins
    t = time()
    while int(time() - t) < MAX_WAIT_FOR_OPEN_APP:
        text = dumpysys_activity(transport_id, ArcVersion)
        query = r".*{.*\s.*\s(?P<package_name>.*)/(?P<act_name>[\S\.]*)\s*.*}"
        result = re.search(query, text)

        if result is None:
            is_ANR_thrown = is_ANR(text, package_name)
            print("Cant find current activity.", f"{is_ANR_thrown=}", text)
            return {
                "package_name": '',
                "act_name": '',
                "is_ANR_thrown": is_ANR_thrown,
                "ANR_for_package": 'packge_name here'
            }

        print(f"get_cur_activty: {result.group('package_name')=} {result.group('act_name')=}")
        return  {
            "package_name": result.group("package_name"),
            "act_name": result.group("act_name"),
            "is_ANR_thrown": False,
            "ANR_for_package": ''
        }

    return {
        "package_name": '',
        "act_name": '',
        "is_ANR_thrown": False,
        "ANR_for_package": ''
    }

def open_app(package_name: str, transport_id: int, ArcVersion: ArcVersions = ArcVersions.ARC_R):
    '''
        Opens an app using ADB monkey.

        Params:
            package_name: The name of the package to check crash logs for.
            transport_id: The transport id of the connected android device.
            ArcVersion: ArcVersion Enum for the device.
    '''
    try:
        cmd = ('adb','-t', transport_id, 'shell', 'monkey', '--pct-syskeys', '0', '-p', package_name, '-c', 'android.intent.category.LAUNCHER', '1')
        outstr = subprocess.run(cmd, check=True, encoding='utf-8',
                                capture_output=True).stdout.strip()
        print(f"Starting {package_name} w/ monkey...")

        # Call get activty and wait until the package name matches....
        cur_package = ""
        MAX_WAIT_FOR_OPEN_APP = 420  # 7 mins
        t = time()
        # org.chromium.arc.applauncher will be the package if a PWA is launched...
        while (
            cur_package != package_name and
            cur_package != "com.google.android.permissioncontroller" and
            cur_package != "org.chromium.arc.applauncher" and
            int(time() - t) < MAX_WAIT_FOR_OPEN_APP):
            try:
                res = get_cur_activty(transport_id, ArcVersion, package_name)
                cur_package = res['package_name']
            except Exception as err:
                print("Err getting cur act", err)
        print(f"open_app {outstr=}")
    except Exception as err:
        print("Error opening app with monkey", err)
        return False
    return True

def close_app(package_name: str, transport_id: int):
    '''
        Opens an app using ADB monkey.
        adb shell am broadcast -a android.intent.action.ACTION_SHUTDOWN

        Params:
            package_name: The name of the package to check crash logs for.
            transport_id: The transport id of the connected android device.
    '''
    try:
        if "badidea" == FACEBOOK_PACKAGE_NAME:
            # E Security-LocalReporter: category=InternalIntentScope, message=Access denied. com.facebook.katana cannot receive broadcasts from no_app_identity, cause=java.lang.SecurityException: Access denied. com.facebook.katana cannot receive broadcasts from no_app_identity
            cmd = ('adb', '-t', transport_id, 'shell', 'am', 'broadcast', "-a", "android.intent.action.ACTION_SHUTDOWN")  # throws erro and security exception

        cmd = ('adb', '-t', transport_id, 'shell', 'am', 'force-stop', package_name)
        outstr = subprocess.run(cmd, check=True, encoding='utf-8',
                                capture_output=True).stdout.strip()
        print(f"Closed {package_name}...")
    except Exception as err:
        print("Error closing app ", err)
        return False
    return True

def is_package_installed(transport_id: str, package_name: str):
    ''' Checks if package is installed via ADB. '''
    # Call the adb shell pm list packages command
    result = subprocess.run(
        ['adb', '-t', transport_id, 'shell', 'pm', 'list', 'packages'],
        check=False, encoding='utf-8', capture_output=True
    ).stdout.strip()
    # Check the output for the package name
    return package_name in result

def is_download_in_progress(transport_id: str, package_name: str):
    ''' Runs the command:
        adb shell dumpsys activity services | grep <package_name>
        and if anything is returned, then return True as there is a download in progress.
        Good for waiting for games to downlaod extra content.
    '''
    try:
        # command = f'adb -t {transport_id} shell dumpsys activity services | grep com.google.android.finsky.assetmoduleservice.AssetModuleService:{package_name}'
        # output = subprocess.check_output(command, shell=True).decode('utf-8')

        result = subprocess.run(
            ['adb', '-t', transport_id, 'shell', 'dumpsys', 'activity', 'services', "|", "grep", f"com.google.android.finsky.assetmoduleservice.AssetModuleService:{package_name}"],
            check=False, encoding='utf-8', capture_output=True
        ).stdout.strip()
        print(f"is_download_in_progress {result=}")
        return bool(result)
    except Exception as error:
        print("Error w/ checking download in progress")
        print(error)
    return False

def get_views(transport_id: str):
    ''' Creates an XML dump of current UI hierarchy.
    '''
    #  adb exec-out uiautomator dump /dev/tty
    result = subprocess.run(
            ['adb', '-t', transport_id, 'exec-out', 'uiautomator', 'dump', '/dev/tty'],
            check=False, encoding='utf-8', capture_output=True
        ).stdout.strip()
    print(f"Get_views {result=}")



##                  Image utils               ##

def transform_coord_from_resized(original_size: Tuple, resized_to: Tuple, resized_coords: Tuple) -> Tuple[int]:
    ''' Given original img size, resized image size and resized coords, this will calculate the original coords.

        Args:
            original_size: A tuple defining the size of the original image representing the screen coords.
            resized_to: A tuple defining the size of the resized image.
            resized_coords: A tuple representing the x,y coords reported from detection on the resized image.

            The image is resized from its current size to 1200x800.
            So the bound box is now referencing the resized image.

            For ex, Helios @ 100% = 1536 x 864 => actual point to click = (0.4167, 0.5) x (1536, 864) = (640, 432)
                                  = 1200 x 800 => returns x,y to click @ (500, 400) => % => ([500/1200], [400/800]) = (0.4167, 0.5)

            So, when we resize and new image reports (500, 400) we need to actually click (640, 432)

            Returns:
            A tuple representing the coordinates on the original image.
    '''
    x_coord_factor = resized_coords[0] / resized_to[0]
    y_coord_factor = resized_coords[1] / resized_to[1]
    return (original_size[0]* x_coord_factor, original_size[1] * y_coord_factor)

def save_resized_image(image_bytes: bytes, new_size: Tuple, output_path: str):
    """
    Resize the input PNG image bytes to the given size using OpenCV2 and save it as a PNG file.

    TODO() Need to transform coordinates now....


    Args:
        image_bytes: The input PNG image as bytes.
        new_size: A tuple (width, height) of the desired new image size.
        output_path: The path to save the resized image file.

    Returns:
        None.
    """
    # Read the image from bytes using OpenCV2
    image_array = np.frombuffer(image_bytes, dtype=np.uint8)
    image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

    # Get the original image size
    original_size = image.shape[:2][::-1]

    # Resize the image using OpenCV2
    resized_image = cv2.resize(image, new_size, interpolation=cv2.INTER_LINEAR)

    # Save the resized image as a PNG file
    cv2.imwrite(output_path, resized_image)

# Not used, need to get SS of ChromeOS first....
def find_template(large_img, small_img, method=cv2.TM_CCOEFF_NORMED):
    method = cv2.TM_SQDIFF_NORMED
    # Read the images
    large_img = cv2.imread(large_img)
    small_img = cv2.imread(small_img)

    # Convert images to grayscale
    gray_large_img = cv2.cvtColor(large_img, cv2.COLOR_BGR2GRAY)
    gray_small_img = cv2.cvtColor(small_img, cv2.COLOR_BGR2GRAY)

    # Apply template matching
    result = cv2.matchTemplate(gray_large_img, gray_small_img, method)

    # Use the cv2.minMaxLoc() function to find the coordinates of the best match
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
    print("Min/ max", min_val, max_val)
    # If the method is TM_SQDIFF or TM_SQDIFF_NORMED, take minimum
    if method in [cv2.TM_SQDIFF, cv2.TM_SQDIFF_NORMED]:
        top_left = min_loc
    else:
        top_left = max_loc

    # Draw a rectangle around the matched region
    bottom_right = (top_left[0] + small_img.shape[1], top_left[1] + small_img.shape[0])
    cv2.rectangle(large_img, top_left, bottom_right, (0, 0, 255), 2)

    # Show the final image
    cv2.imshow('Matched Image', large_img)
    # cv2.imshow('Matched Image', gray_large_img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

def check_amace(driver, package_name: str) -> bool:
    # '''
    # Apk Analyzer - AMAC-e
    #  ActivityTaskManager: START u0 {act=android.intent.action.MAIN cat=[android.intent.category.LAUNCHER] id=window_session_id=8 flg=0x10200000 cmp=sk.styk.martin.apkanalyzer/.ui.main.MainActivity} from uid 1000
    # '''
    # Grab screenshot of device
    # Look for AMAC-e image.
    names = ['amace_phone', 'amace_tablet', 'amace_resize'] # names of .pngs for template matching.
    root_path = get_root_path()
    ss_path = f"{root_path}/apks/{package_name}/test.png"
    does_exist = file_exists(ss_path)

    print("Checking AMAC-e", ss_path[:100])
    ss = driver.get_screenshot_as_file(ss_path)
    for name in names:
        amace_icon_path = f"{get_root_path()}/images/templates/{name}.png"
        find_template(ss_path, amace_icon_path)
    return False

def dev_scrape_start_at_app(start_package_name: str, app_list: List[List[str]]) -> int:
    ''' Given package name, returns index in the list.'''
    for i, app in enumerate(app_list):
        app_name, package_name = app
        if start_package_name == package_name:
            return i
    raise Exception(f"{start_package_name} not in the list.")

PACKAGE_NAMES = [
    # [ "Twitter", "com.twitter.android"],
    # [ "Rocket League Sideswipe", "com.Psyonix.RL2D"],
    # ['Apk Analyzer', 'sk.styk.martin.apkanalyzer'],
    [FACEBOOK_APP_NAME, FACEBOOK_PACKAGE_NAME],
    ['Roblox', 'com.roblox.client'],
    # ['Showmax', 'com.showmax.app'],  # NA in region
    # ['Epic Seven', 'com.stove.epic7.google'], #  Failed send keys
    # ['Legión Anime Tema Oscuro', 'aplicaciones.paleta.alterlegionanime'],  # Failed to send keys
    # ['Garena Free Fire', 'com.dts.freefireth'],
    # ['My Boy! - GBA Emulator', 'com.fastemulator.gba'],  # Purchase required, unable to install...
    ['Messenger', 'com.facebook.orca'],
    ['Messenger Kids', 'com.facebook.talk'],
    ['Among Us!', 'com.innersloth.spacemafia'],
    ['Tubi TV', 'com.tubitv'],
    ['Netflix', 'com.netflix.mediaclient'],  # Unable to take SS of app due to protections.
    ['YouTube Kids', 'com.google.android.apps.youtube.kids'],
    ['Gacha Club', 'air.com.lunime.gachaclub'],
    ['Gacha Life', 'air.com.lunime.gachalife'],
    ['Google Classroom', 'com.google.android.apps.classroom'],
    ['Candy Crush Soda Saga', 'com.king.candycrushsodasaga'],
    ['Google Photos', 'com.google.android.apps.photos'],
    ['Homescapes', 'com.playrix.homescapes'],
    ["June's Journey", 'net.wooga.junes_journey_hidden_object_mystery_game'],
    ['Gmail', 'com.google.android.gm'],
    ['YouTube Music', 'com.google.android.apps.youtube.music'],
    ['Viki', 'com.viki.android'],
    ['TikTok', 'com.ss.android.ugc.trill'], # Error opening with monkey com.zhiliaoapp.musically
    ['Microsoft Office Mobile', 'com.microsoft.office.officehubrow'],
    ['Spectrum TV', 'com.TWCableTV'],
    ['RAID: Shadow Legends', 'com.plarium.raidlegends'],
    ['Libby, by OverDrive Labs', 'com.overdrive.mobile.android.libby'],
    ['Google Docs', 'com.google.android.apps.docs.editors.docs'],
    ['Pluto tv', 'tv.pluto.android'],
    ['Animal Jam', 'com.WildWorks.AnimalJamPlayWild'],
    ['Webtoon', 'com.naver.linewebtoon'],
    ['PK XD', 'com.movile.playkids.pkxd'],
    ['Funimation', 'com.Funimation.FunimationNow'],
    ['myCANAL', 'com.canal.android.canal'],
    ['Picsart Ai Photo Editor', 'com.picsart.studio'],
    ['WhatsApp Business', 'com.whatsapp.w4b'],
    # ['BBC iPlayer', 'bbc.iplayer.android'],  # Not available in Region
    # ['Videoland', 'nl.rtl.videoland'], # DNExist
    ['Videoland v2', 'nl.rtl.videoland.v2'],
    # ['Ziggo GO', 'com.lgi.ziggotv'], # Not available in Region
    ['Duolingo: Learn Languages', 'com.duolingo'],
    ['Farm Heroes Saga', 'com.king.farmheroessaga'],
    ['Minecraft - Pocket Edition', 'com.mojang.minecraftpe'],
    # ['Локикрафт', 'com.ua.building.Lokicraft'], # Failed send keys
    ['Toon Blast', 'net.peakgames.toonblast'],
    ['Pokemon TCG Online', 'com.pokemon.pokemontcg'],
    ['Asphalt 8: Airborne', 'com.gameloft.android.ANMP.GloftA8HM'],
    ['8 Ball Pool', 'com.miniclip.eightballpool'],
    ['Magic Jigsaw Puzzles', 'com.bandagames.mpuzzle.gp'],
    ['Solar Smash', 'com.paradyme.solarsmash'],
    ['Jackpot Party Casino', 'com.williamsinteractive.jackpotparty'],
    ['Subway Surfers', 'com.kiloo.subwaysurf'], ## NOt found on Helios
    ['Episode', 'com.episodeinteractive.android.catalog'],
    ['Block Craft 3D', 'com.fungames.blockcraft'],
    ['Solitaire - Classic Card Games', 'com.mobilityware.solitaire'],
    ['The Sims FreePlay', 'com.ea.games.simsfreeplay_na'],
    ['ITV Player', 'air.ITVMobilePlayer'],
    ['Family Farm Adventure', 'com.farmadventure.global'], # Failed on first open.... not sure why.
    ['Finding Home', 'dk.tactile.mansionstory'],
    ['Sling Television', 'com.sling'],
    ['Asphalt 9: Legends', 'com.gameloft.android.ANMP.GloftA9HM'],
    ['Acellus', 'com.acellus.acellus'],
    ['Pokémon Quest', 'jp.pokemon.pokemonquest'],
    ['Guns of Glory', 'com.diandian.gog'],
    ['Bowmasters', 'com.miniclip.bowmasters'],
    ['CW Network', 'com.cw.fullepisodes.android'],
    ['Zooba', 'com.wildlife.games.battle.royale.free.zooba'],
    ['Amino: Communities and Chats', 'com.narvii.amino.master'],
    ['Solitaire Classic', 'com.freegame.solitaire.basic2'], # Fails to find correct app in search
    ['Summoners War', 'com.com2us.smon.normal.freefull.google.kr.android.common'], # Faisl to download extra data but doesnt crash app
    ['Plants vs. Zombies', 'com.ea.game.pvzfree_row'],
    ['Yu-Gi-Oh! Duel Links', 'jp.konami.duellinks'],
    ['Manor Matters', 'com.playrix.manormatters'],
    ['Adorable Home', 'com.hyperbeard.adorablehome'],
    ['Spider Solitaire', 'com.spacegame.solitaire.spider'],
    ['Clip Studio Paint', 'jp.co.celsys.clipstudiopaint.googleplay'],
    ['6play', 'fr.m6.m6replay'],
    ['Rokie - Roku Remote', 'com.kraftwerk9.rokie'],
    ['Bubble Witch 3 Saga', 'com.king.bubblewitch3'],
    ['Colorscapes', 'com.artlife.coloringbook'],
    ['Spider Solitaire', 'at.ner.SolitaireSpider'], ## App was not installed, TODO look into this
    ['Last Day on Earth: Survival', 'zombie.survival.craft.z'],
    ['My Talking Tom Friends', 'com.outfit7.mytalkingtomfriends'],
    ['War Robots', 'com.pixonic.wwr'],
    ['Cashman Casino', 'com.productmadness.cashmancasino'],
    ['HP All in One Printer Remote', 'com.hp.printercontrol'],
    ['TeamViewer for Remote Control', 'com.teamviewer.teamviewer.market.mobile'],
    ['Best Fiends', 'com.Seriously.BestFiends'],
    ['Xodo PDF Reader & Editor', 'com.xodo.pdf.reader'],
    ['Shadow Fight 3', 'com.nekki.shadowfight3'],
    ['Chrome Browser', 'com.chrome.beta'],
    ['Audible', 'com.audible.application'], # Protected sign in 'secure' flag set, cant take ScreenShot
    ['PowerDirector', 'com.cyberlink.powerdirector.DRA140225_01'],
    ['Deezer', 'deezer.android.app'],
    ['Magic Tiles 3', 'com.youmusic.magictiles'],
    ['Solitaire', 'com.brainium.solitairefree'],
    ['Classic Words', 'com.lulo.scrabble.classicwords'],
    ['Soul Knight', 'com.ChillyRoom.DungeonShooter'],
    ['Plex', 'com.plexapp.android'],
    ['Jigsaw Puzzles Epic', 'com.kristanix.android.jigsawpuzzleepic'],
    ['Extreme Car Driving Simulator', 'com.aim.racing'],
    ['Honkai Impact 3', 'com.miHoYo.bh3global'],
    ['Audiomack', 'com.audiomack'],
    ['Crossy Road', 'com.yodo1.crossyroad'],
    ['com.vanced.android.youtube', 'com.vanced.android.youtube'],
    ['TradingView', 'com.tradingview.tradingviewapp'],
    ['Slots - House of Fun', 'com.pacificinteractive.HouseOfFun'],
    ['RISK: Global Domination', 'com.hasbro.riskbigscreen'],
    ['My Boy! Free - GBA Emulator', 'com.fastemulator.gbafree'],
    ['MARVEL Strike Force', 'com.foxnextgames.m3'],
    ['com.yoku.marumovie', 'com.yoku.marumovie'],
    ['Family Farm Seaside', 'com.funplus.familyfarm'],
    ['World of Tanks Blitz', 'net.wargaming.wot.blitz'],
    ['eBay', 'com.ebay.mobile'],
    ['Count Masters - Stickman Clash', 'freeplay.crowdrun.com'],
    ['Gallery: Coloring Book', 'com.beresnevgames.gallerycoloringbook'],
    ['Krita', 'org.krita'],
    ['Lightroomq', 'com.adobe.lrmobile'],
    ['com.madfut.madfut21', 'com.madfut.madfut21'],
    ['Rummikub', 'com.rummikubfree'],
    ['Chat Master!', 'com.RBSSOFT.HyperMobile'],
    # ['에픽세븐', 'com.stove.epic7.google'], Failed send keys
    ['Snake.io by Amelos Interactive', 'com.amelosinteractive.snake'],
    ['Rave', 'com.wemesh.android'],
    ['Phone Case DIY', 'com.newnormalgames.phonecasediy'],
    ['My Talking Tom 2', 'com.outfit7.mytalkingtom2'],
    ['Tag with Ryan', 'com.WildWorks.RyansTag'],
    ['Dragons: Rise of Berk', 'com.ludia.dragons'],
    ['FIFA Soccer', 'com.ea.gp.fifamobile'],
    ['Anime Center', 'pro.anioload.animecenter'],
    ['VRV', 'com.ellation.vrv'],
    ['Toca Kitchen 2', 'com.tocaboca.tocakitchen2'],
    ['Love Nikki-Dress UP Queen', 'com.elex.nikkigp'],
    # ['CrossOver on Chrome OS Beta', 'com.codeweavers.cxoffice'], # Package not available.
    ['Pocket Mortys', 'com.turner.pocketmorties'],
    ['Wish - Shopping Made Fun', 'com.contextlogic.wish'],
    ['Scary Teacher 3D', 'com.zakg.scaryteacher.hellgame'],
    ['FreeCell Solitaire', 'at.ner.SolitaireFreeCell'],  # Doest find correct package
    ['Solitaire Card Games Free', 'com.Nightingale.Solitaire.Card.Games.Free'], # Doest find correct package
    ['250+ Solitaire Collection', 'com.anoshenko.android.solitaires'],
    ['NOOK', 'bn.ereader'],
    ['Evony', 'com.topgamesinc.evony'],
    ['Wonder Merge - Magic Merging and Collecting Games', 'com.cookapps.wonder.merge.dragon.magic.evolution.merging.wondermerge'],
    ['Wood Block Puzzle - Free Classic Block Puzzle Game', 'puzzle.blockpuzzle.cube.relax'],
    ['Hungry Shark Evolution', 'com.fgol.HungrySharkEvolution'],
    ['Mergical', 'com.fotoable.mergetown'],   # Package not found
    ["Diggy's Adventure", 'air.com.pixelfederation.diggy'],
    ['My Talking Angela', 'com.outfit7.mytalkingangelafree'],
    ['The Tribez', 'com.gameinsight.tribez'],
    ['Job Search', 'com.indeed.android.jobsearch'],
    ['GyaO', 'jp.co.yahoo.gyao.android.app'],
    ['Evernote', 'com.evernote'],
    ['Earn Cash & Money Rewards - CURRENT Music Screen', 'us.current.android'],
    ['Talking Tom Gold Run', 'com.outfit7.talkingtomgoldrun'],
    ['Hollywood Story', 'org.nanobit.hollywood'],
    ['hayu', 'com.upst.hayu'], # Failed click app icon
    ['NPO', 'nl.uitzendinggemist'],
    ['V - Real-time celeb broadcasting app', 'com.naver.vapp'], # Failed click app icon
    ['Cash Frenzy', 'slots.pcg.casino.games.free.android'],
    ['Crayola Scribble Scrubbie Pets', 'com.crayolallc.crayola_scribble_scrubbie_pets'],
    ['SALTO, TV & streaming illimités dans une seule app', 'fr.salto.app'],
    ['Catwalk Beauty', 'com.catwalk.fashion.star'],
    ['Mahjong Solitaire', 'com.mobilityware.MahjongSolitaire'],
    ['Pepi Wonder World: Magic Isle!', 'com.PepiPlay.KingsCastle'],
    ['Spider Solitaire', 'com.cardgame.spider.fishdom'],
    ['Relax Jigsaw Puzzles', 'com.openmygame.games.android.jigsawpuzzle'],
    ['L.O.L. Surprise! Disco House', 'com.tutotoons.app.lolsurprisediscohouse'],
    ['100 Years - Life Simulator', 'com.lawson.life'],
    ['Mobile Legends: Adventure', 'com.moonton.mobilehero'],
    ['John GBA Lite - GBA emulator', 'com.johnemulators.johngbalite'],
    ['Egg, Inc.', 'com.auxbrain.egginc'],
    ['Heart of Vegas', 'com.productmadness.hovmobile'],
    ['Google Slides', 'com.google.android.apps.docs.editors.slides'],
    ['Jewels of Rome', 'com.g5e.romepg.android'],
    ['Cooking Diary: Tasty Hills', 'com.mytona.cookingdiary.android'],
    ['House Designer : Fix & Flip', 'com.kgs.housedesigner'],
    ['TuneIn Radio', 'tunein.player'],
    ['Video Downloader', 'video.downloader.videodownloader'],
    ['Pyramid', 'com.mobilityware.PyramidFree'],
    ['Tie Dye', 'com.crazylabs.tie.dye.art'],
    ['eFootball PES 2020', 'jp.konami.pesam'],
    ['Veezie.st - Enjoy your videos, easily.', 'st.veezie'],
    ["TV d'Orange film, streaming", 'com.orange.owtv'],
    ['Prodigy Math Game', 'com.prodigygame.prodigy'],
    ['Head Ball 2', 'com.masomo.headball2'],
    ['Drive Ahead', 'com.dodreams.driveahead'],
    ['Paper Fold', 'com.game.foldpuzzle'],
    ['MetaTrader 4', 'net.metaquotes.metatrader4'],
    ['StarMaker Karaoke', 'com.starmakerinteractive.starmaker'],
    ['Cookie Jam', 'air.com.sgn.cookiejam.gp'],
    ['Nonograms Katana', 'com.ucdevs.jcross'],
    ['Kick the Buddy', 'com.playgendary.kickthebuddy'],
    ['The Simpsons™: Tapped Out', 'com.ea.game.simpsons4_na'],
    ['Tuscany Villa', 'com.generagames.toscana.hotel'],
    ['Hotel Hideaway', 'com.piispanen.hotelhideaway'],
    ['U-NEXT', 'jp.unext.mediaplayer'],
    ['DraStic DS Emulator', 'com.dsemu.drastic'],
    ['1v1.LOL', 'lol.onevone'], # Age verification
    ['Sketch - Draw & Paint', 'com.sonymobile.sketch'],
    ['Merge Elves', 'com.merge.elves'],
    ['Teamfight Tactics', 'com.riotgames.league.teamfighttactics'],
    ['GlobalProtect', 'com.paloaltonetworks.globalprotect'],
    ['News Break', 'com.particlenews.newsbreak'],
    ['Shazam', 'com.shazam.android'],
    ['Bingo Frenzy! Bingo Cooking Free Live BINGO Games', 'com.cooking.bingo.ldkwh'],
    ['Kitchen Frenzy - Chef Master', 'com.biglime.cookingmadness'],
    ['Queen Bee!', 'com.MoodGames.QueenBee'],
    ['Tumblr', 'com.tumblr'],
    ['Bus Simulator : Ultimate', 'com.zuuks.bus.simulator.ultimate'],
    ['My Boy! - GBA Emulator', 'com.fastemulator.gba'],  # Purchase required, unable to install...
    ['Zeus', 'com.thezeusnetwork.www'],
    ['CATS: Crash Arena Turbo Stars', 'com.zeptolab.cats.google'],
    ['Work Chat', 'com.facebook.workchat'],
    ['Plague Inc', 'com.miniclip.plagueinc'],
    ['Sniper 3D Assassin', 'com.fungames.sniper3d'],
    ['VPN by NordVPN', 'com.nordvpn.android'],
    ['Garena Free Fire MAX', 'com.dts.freefiremax'],
    ['DAZN', 'com.dazn'],
    ['Hempire - Weed Growing Game', 'ca.lbcstudios.hempire'],
    ['Find the Difference 1000+', 'com.gamma.find.diff'],
    ['Loyverse POS - Point of Sale & Stock Control', 'com.loyverse.sale'],
    ['Daily Themed Crossword Puzzle', 'in.crossy.daily_crossword'],
    ['Age of Civilizations II', 'age.of.civilizations2.jakowski.lukasz'],
    ['globo.tv', 'com.globo.globotv'],
    ['Color by Number Coloring Games', 'com.artlife.color.number.coloring.games'],
    ['TRANSFORMERS: Earth Wars', 'com.backflipstudios.transformersearthwars'],
    ['Web Video Cast | Browser to TV/Chromecast/Roku/+', 'com.instantbits.cast.webvideo'],
    ['Plurall', 'com.kongros.plurall'],
    ['Spades Royale', 'com.bbumgames.spadesroyale'],
    ['TextingStory', 'com.textingstory.textingstory'],
    ['My PlayHome Plus', 'com.playhome.plus'],
    ['Flipboard', 'flipboard.app'],
    ['Cross Stitch', 'com.inapp.cross.stitch'], # Not found
    ['Who is? Brain Teaser & Riddles', 'com.unicostudio.whois'],
    ['thinkorswim', 'com.devexperts.tdmobile.platform.android.thinkorswim'],
    ['Huuuge Casino Slots Vegas 777', 'com.huuuge.casino.slots'],
    ['Mahjong', 'com.fenghenda.mahjong'],
    ['Galaxy Attack: Alien Shooting', 'com.alien.shooter.galaxy.attack'],  # App not available on Helios -> doesnt show in results but when clicking on link, it shows 'Your device isn't compatible with this version.'
    ['Madden NFL 21 Mobile Football', 'com.ea.gp.maddennfl21mobile'],
    ['Bubble Shooter Rainbow - Shoot & Pop Puzzle', 'com.blackout.bubble'],
    ['VIDEOMEDIASET', 'it.fabbricadigitale.android.videomediaset'],
    ['Google Earth', 'com.google.earth'],
    ['Viaplay', 'com.viaplay.android'],
    ['Lifetime', 'com.aetn.lifetime.watch'],
    ['Coloring Book - Color by Number & Paint by Number', 'com.iceors.colorbook.release'],
    ['Tongits Go', 'com.tongitsgo.play'],
    ['Gospel Library', 'org.lds.ldssa'],
    ['Brain Test 2: Tricky Stories', 'com.unicostudio.braintest2new'],
    ['Kingdom Rush', 'com.ironhidegames.android.kingdomrush'],
    ['Grand Theft Auto: San Andreas', 'com.rockstargames.gtasa'],
    ['Vegas Live Slots', 'com.purplekiwii.vegaslive'],
    ['MLB Perfect Inning Live', 'com.gamevilusa.mlbpilive.android.google.global.normal'],
    ['OfficeSuite 7', 'com.mobisystems.office'],
    ['Cookie Run: Kingdom - Kingdom Builder & Battle RPG', 'com.devsisters.ck'],
    ['School Girls Simulator', 'com.Meromsoft.SchoolGirlsSimulator'],
    ['SiriusXM', 'com.sirius'],
    ['Castle Solitaire: Card Game', 'com.mobilityware.CastleSolitaire'],
    ['Word Stacks', 'com.peoplefun.wordstacks'],
    # ['com.roku.trc', 'com.roku.trc'],  #  Invalid package name
    ['Albion Online', 'com.albiononline'],
    ['Time Princess: Story Traveler', 'com.igg.android.dressuptimeprincess'],
    ['Mahjong Solitaire Epic', 'com.kristanix.android.mahjongsolitaireepic'],
    ['Farm Land: Farming Life Game', 'com.loltap.farmland'],
    ['Lost Island: Blast Adventure', 'com.plarium.blast'],
    ['FNF Music Battle: Original Mod', 'com.os.falcon.fnf.battle.friday.night.funkin'],
    ['Stumble Guys: Multiplayer Royale', 'com.kitkagames.fallbuddies'],
    ['discovery+', 'com.discovery.dplay'], # com.discovery.discoveryplus is the disccovery+ package name. This OG package name is NA in region
    ['Sonos', 'com.sonos.acr2'],
    ['Binge', 'au.com.streamotion.ares'],  # NA ion Pixel 2
    ['Wordfeud', 'com.hbwares.wordfeud.free'],
    ['Farming Simulator 16', 'com.giantssoftware.fs16'],
    ['Piano Kids - Music & Songs', 'com.orange.kidspiano.music.songs'],
    # ['FreeCell', 'com.hapogames.FreeCell'],  # Invalid package name
    ['Word Cookies!', 'com.bitmango.go.wordcookies'],
    ['Floor Plan Creator', 'pl.planmieszkania.android'],
    ['Legión Anime Tema Oscuro', 'aplicaciones.paleta.alterlegionanime'],
    ['Adobe Illustrator Draw', 'com.adobe.creativeapps.draw'],  # NA on Pixel 2
    ['aquapark.io', 'com.cassette.aquapark'],
    ['Bridge Race', 'com.Garawell.BridgeRace'],
    ['Jewels Magic: Mystery Match3', 'com.bitmango.go.jewelsmagicmysterymatch3'],
    ['LogMeIn Pro', 'com.logmein.ignitionpro.android'],
    ['Roku Remote: RoSpikes (WiFi&', 'roid.spikesroid.roku_tv_remote'],
    ['Battle of Warships', 'com.CubeSoftware.BattleOfWarships'],
    ['Mini Block Craft', 'mini.block.craft.free.mc'],
    ['AmongLock - Among Us Lock Screen', 'amonguslock.amonguslockscreen.amonglock'],
    ['Bloons Monkey City', 'com.ninjakiwi.monkeycity'],
    ['Match Triple 3D - Match 3D Master Puzzle', 'and.lihuhu.machingtriple'],
    # ['Showmax', 'com.showmax.app'],  # NA in region
    ['Pocket Cine Pro', 'com.flix.Pocketplus'],
    ['Guess Their Answer', 'com.qoni.guesstheiranswer'],
    ['Gold and Goblins: Idle Digging', 'com.redcell.goldandgoblins'],
    ['My Home Design - Luxury Interiors', 'com.cookapps.ff.luxuryinteriors'],
    ['Bingo Pop', 'com.uken.BingoPop'],
    ['GoToMeeting', 'com.gotomeeting'],
    ['Solitaire Collection', 'com.cardgame.collection.fishdom'],
    ['Hello Neighbor', 'com.tinybuildgames.helloneighbor'],
    ['Airport City', 'com.gameinsight.airport'],
    ['Need for Speed No Limits', 'com.ea.game.nfs14_row'],
    ['BBC Sounds', 'com.bbc.sounds'],
    ['Rummy 500', 'com.trivialtechnology.Rummy500D'],
    ['Sweet Dance', 'com.au.dance.en'],
    ['Papers Grade Please!', 'com.hyperdivestudio.papersgradeplease'],
    ['Board Kings', 'com.jellybtn.boardkings'],
    ['Dan The Man', 'com.halfbrick.dantheman'],
    ['[3D Platformer] Super Bear Adventure', 'com.Earthkwak.Platformer'],
    ['Kayo Sports', 'au.com.kayosports'],
    ['DoubleDown Casino', 'com.ddi'],
    ['Bingo Story', 'com.clipwiregames.bingostory'],
    ['Color By Number For Adults', 'com.pixign.premium.coloring.book'],
    ['Fox News', 'com.foxnews.android'],
    ['Rider', 'com.ketchapp.rider'],
    ['Kobo', 'com.kobobooks.android'],
    ['Funky Bay', 'com.belkatechnologies.fe'],
    ['WATCHED', 'com.watched.play'],
    ['Classic Solitaire', 'com.solitaire.card'],
    ['Chess Free', 'uk.co.aifactory.chessfree'],
    ['M64Plus FZ Emulator', 'org.mupen64plusae.v3.fzurita'],
    ['Bubble Shooter by Ilyon', 'bubbleshooter.orig'],
    ['Blockman Go', 'com.sandboxol.blockymods'],
    ['TLC GO', 'com.discovery.tlcgo'],
    ['DAFU Casino', 'com.grandegames.slots.dafu.casino'],
    ['Cookie Jam Blast', 'air.com.sgn.cookiejamblast.gp'],
    ['Investigation Discovery GO', 'com.discovery.idsgo'],
    # ['Contacts', 'com.google.android.contacts'], # Unable to uninstall, default app?
    ['FanFiction.Net', 'com.fictionpress.fanfiction'],
    ['Eerskraft', 'com.eers.kraft.eerskraft'],
    ['CW Seed on Fire TV', 'com.cw.seed.android'],
    ['Solitaire - Free Classic Solitaire Card Games', 'beetles.puzzle.solitaire'],
    ['combyne', 'com.combyne.app'],
    ['PlanetCraft: Block Craft Games', 'com.craftgames.plntcrft'],
    ['BanG Dream', 'com.bushiroad.en.bangdreamgbp'],
    ['Mini World Block Art', 'com.playmini.miniworld'],
    ['Omlet Arcade', 'mobisocial.arcade'],
    ['ArtFlow: Paint Draw Sketchbook', 'com.bytestorm.artflow'],
    ['World War Heroes', 'com.gamedevltd.wwh'],
    ['Horse Haven World Adventures', 'com.ubisoft.horsehaven.adventures'],
    ['Heroes Inc!', 'com.blueflamingo.herolab'],
    ['Dancing Road: Colour Ball Run', 'com.amanotes.pamadancingroad'],
    ['Groundworks G3', 'com.groundworkcompanies.g3'],
    ['Solitaire', 'solitaire.card.games.klondike.solitaire.classic.free'],
    ['AndrOpen Office', 'com.andropenoffice'],
    ['Tapastic', 'com.tapastic'],
    ['KakaoTalk', 'com.kakao.talk'],
    ['Shadow Fight 2', 'com.nekki.shadowfight'],
    ['Red Ball 4', 'com.FDGEntertainment.redball4.gp'],
    ['Polaris Office', 'com.infraware.office.link'],
    ['Granny 3', 'com.DVloper.Granny3'],
    ['Fios TV', 'com.verizon.fios.tv'],
    ['Duskwood - Crime & Investigation Detective Story', 'com.everbytestudio.interactive.text.chat.story.rpg.cyoa.duskwood'],
    ['The Battle of Polytopia', 'air.com.midjiwan.polytopia'],
    ['Moments: Choose Your Story', 'com.gg.lovestory.moments'],
    ['Acrylic Nails!', 'com.crazylabs.acrylic.nails'],
    ['Hello Kitty Nail Salon', 'com.budgestudios.HelloKittyNailSalon'],
    ['Onnect', 'com.gamebility.onet'],
    ['Whats Web', 'com.softinit.iquitos.whatsweb'],
    ['PokerStars Poker', 'com.pyrsoftware.pokerstars.net'],
    ['Telegram', 'org.thunderdog.challegram'],
    ['DOFUS Touch', 'com.ankama.dofustouch'],
    ['Steam Link', 'com.valvesoftware.steamlink'],
    ['Monster Strike', 'jp.co.mixi.monsterstrike'],
    ['House Flipper: Home Design & Simulator Games', 'com.imaginalis.HouseFlipperMobile'],
    ['Grand Hotel Mania', 'com.deuscraft.TurboTeam'],
    ['Nick Jr.', 'com.nick.android.nickjr'],
    # ['Whats Web Scan', 'com.softinit.iquitos.whatswebscan'], # NA on Playstore
    ["Hide 'N Seek!", 'com.seenax.HideAndSeek'],
    ['Ball Run 2048', 'com.kayac.ball_run'],
    ['Manor Cafe', 'com.gamegos.mobile.manorcafe'],
    ['Disney Magic Kingdoms', 'com.gameloft.android.ANMP.GloftDYHM'],
    ['Solitaire', 'com.agedstudio.card.solitaire.klondike'],
    ['WATCH ABC', 'com.disney.datg.videoplatforms.android.abc'],
    ['YouTube', 'com.google.android.youtube'],
    ['Google Drive', 'com.google.android.apps.docs'],
    ['Google Keep', 'com.google.android.keep'],
    ['Google Maps', 'com.google.android.apps.maps'],
    ['Toontastic 3D', 'com.google.toontastic'],
    ['Google Chat', 'com.google.android.apps.dynamite'],
    ['Youtube Music', 'com.google.android.apps.youtube.music.pwa'],
    ['Files by Google: Clean up space on your phone', 'com.google.android.apps.nbu.files'],
    ['YouTube Creator Studio', 'com.google.android.apps.youtube.creator'],
    ['Google Play Music', 'com.google.android.music'],
    ['Google Tasks: Any Task Any Goal. Get Things Done', 'com.google.android.apps.tasks'],
    ['Chrome Remote Desktop', 'com.google.chromeremotedesktop'],
    ['Google PDF Viewer', 'com.google.android.apps.pdfviewer'],
    ['Jamboard', 'com.google.android.apps.jam'],
    ['Google Find My Device', 'com.google.android.apps.adm'],
    ['Google Family Link for children & teens', 'com.google.android.apps.kids.familylinkhelper'],
    ['Google One', 'com.google.android.apps.subscriptions.red'],
    ['Gallery Go by Google Photos', 'com.google.android.apps.photosgo'],
    ['Google My Business', 'com.google.android.apps.vega'],
    ['Google Opinion Rewards', 'com.google.android.apps.paidtasks'],
]

TOP_500_APPS = PACKAGE_NAMES[:500]

''' 100- 150 failure report
FreeCell Solitaire at.ner.SolitaireFreeCell search/install status: FAILED - [192.168.1.113:5555]
                 Failed to open because the package was not installed.

Adobe Lightroom com.adobe.lrmobile search/install status: FAILED - [192.168.1.113:5555]
                 Failed: Click app icon

CrossOver on Chrome OS Beta com.codeweavers.cxoffice search/install status: FAILED - [192.168.1.113:5555]
                 App package is invalid, update/ remove from list.

Miracle Nikki com.elex.nikkigp search/install status: FAILED - [192.168.1.113:5555]
                 Failed: Click app icon

Mergical com.fotoable.mergetown search/install status: FAILED - [192.168.1.113:5555]
                 Failed: Click app icon

com.madfut.madfut21 com.madfut.madfut21 search/install status: FAILED - [192.168.1.113:5555]
                 Failed: Click app icon

V - Real-time celeb broadcasting app com.naver.vapp search/install status: FAILED - [192.168.1.113:5555]
                 App package is invalid, update/ remove from list.

hayu com.upst.hayu search/install status: FAILED - [192.168.1.113:5555]
                 Failed: Click app icon

com.yoku.marumovie com.yoku.marumovie search/install status: FAILED - [192.168.1.113:5555]
                 Failed: Click app icon

GyaO jp.co.yahoo.gyao.android.app search/install status: FAILED - [192.168.1.113:5555]
                 Failed: Click app icon

Anime Center pro.anioload.animecenter search/install status: FAILED - [192.168.1.113:5555]
                 Failed to open because the package was not installed.





150-200

Kitchen Frenzy - Chef Master com.biglime.cookingmadness search/install status: FAILED - [192.168.1.113:5555]
                 Failed to open because the package was not installed.

Spider Solitaire com.cardgame.spider.fishdom search/install status: FAILED - [192.168.1.113:5555]
                 Failed: Click install button :: Program installed incorrect package,                    com.cardgame.spider.fishdom was not actually installed

DraStic DS Emulator com.dsemu.drastic search/install status: FAILED - [192.168.1.113:5555]
                 Failed: Click install button :: Needs purchase

My Boy! - GBA Emulator com.fastemulator.gba search/install status: FAILED - [192.168.1.113:5555]
                 Failed: Click install button :: Needs purchase

Google Slides com.google.android.apps.docs.editors.slides search/install status: FAILED - [192.168.1.113:5555]
                 Failed: Click install button :: Program installed incorrect package,                    com.google.android.apps.docs.editors.slides was not actually installed

TV d'Orange com.orange.owtv search/install status: FAILED - [192.168.1.113:5555]
                 Failed to open because the package was not installed.

Heart of Vegas com.productmadness.hovmobile search/install status: FAILED - [192.168.1.113:5555]
                 Failed: Click search icon

Sketch - Draw & Paint com.sonymobile.sketch search/install status: FAILED - [192.168.1.113:5555]
                 App package is invalid, update/ remove from list.

U-NEXT jp.unext.mediaplayer search/install status: FAILED - [192.168.1.113:5555]
                 Failed: Click app icon

Google Earth com.google.earth search/install status: FAILED - [192.168.1.113:5555]
                 Failed: Click install button :: Program installed incorrect package,                    com.google.earth was not actually installed

Kingdom Rush com.ironhidegames.android.kingdomrush search/install status: FAILED - [192.168.1.113:5555]
                 Failed: Click install button :: Needs purchase

Grand Theft Auto: San Andreas com.rockstargames.gtasa search/install status: FAILED - [192.168.1.113:5555]
                 Failed to open because the package was not installed.

Viaplay com.viaplay.android search/install status: FAILED - [192.168.1.113:5555]
                 Failed: Click app icon


'''

ADB_KEYCODE_UNKNOWN = "0"
ADB_KEYCODE_MENU = "1"
ADB_KEYCODE_SOFT_RIGHT = "2"
ADB_KEYCODE_HOME = "3"
ADB_KEYCODE_BACK = "4"
ADB_KEYCODE_CALL = "5"
ADB_KEYCODE_ENDCALL = "6"
ADB_KEYCODE_0 = "7"
ADB_KEYCODE_1 = "8"
ADB_KEYCODE_2 = "9"
ADB_KEYCODE_3 = "10"
ADB_KEYCODE_4 = "11"
ADB_KEYCODE_5 = "12"
ADB_KEYCODE_6 = "13"
ADB_KEYCODE_7 = "14"
ADB_KEYCODE_8 = "15"
ADB_KEYCODE_9 = "16"
ADB_KEYCODE_STAR = "17"
ADB_KEYCODE_POUND = "18"
ADB_KEYCODE_DPAD_UP = "19"
ADB_KEYCODE_DPAD_DOWN = "20"
ADB_KEYCODE_DPAD_LEFT = "21"
ADB_KEYCODE_DPAD_RIGHT = "22"
ADB_KEYCODE_DPAD_CENTER = "23"
ADB_KEYCODE_VOLUME_UP = "24"
ADB_KEYCODE_VOLUME_DOWN = "25"
ADB_KEYCODE_POWER = "26"
ADB_KEYCODE_CAMERA = "27"
ADB_KEYCODE_CLEAR = "28"
ADB_KEYCODE_A = "29"
ADB_KEYCODE_B = "30"
ADB_KEYCODE_C = "31"
ADB_KEYCODE_D = "32"
ADB_KEYCODE_E = "33"
ADB_KEYCODE_F = "34"
ADB_KEYCODE_G = "35"
ADB_KEYCODE_H = "36"
ADB_KEYCODE_I = "37"
ADB_KEYCODE_J = "38"
ADB_KEYCODE_K = "39"
ADB_KEYCODE_L = "40"
ADB_KEYCODE_M = "41"
ADB_KEYCODE_N = "42"
ADB_KEYCODE_O = "43"
ADB_KEYCODE_P = "44"
ADB_KEYCODE_Q = "45"
ADB_KEYCODE_R = "46"
ADB_KEYCODE_S = "47"
ADB_KEYCODE_T = "48"
ADB_KEYCODE_U = "49"
ADB_KEYCODE_V = "50"
ADB_KEYCODE_W = "51"
ADB_KEYCODE_X = "52"
ADB_KEYCODE_Y = "53"
ADB_KEYCODE_Z = "54"
ADB_KEYCODE_COMMA = "55"
ADB_KEYCODE_PERIOD = "56"
ADB_KEYCODE_ALT_LEFT = "57"
ADB_KEYCODE_ALT_RIGHT = "58"
ADB_KEYCODE_SHIFT_LEFT = "59"
ADB_KEYCODE_SHIFT_RIGHT = "60"
ADB_KEYCODE_TAB = "61"
ADB_KEYCODE_SPACE = "62"
ADB_KEYCODE_SYM = "63"
ADB_KEYCODE_EXPLORER = "64"
ADB_KEYCODE_ENVELOPE = "65"
ADB_KEYCODE_ENTER = "66"
ADB_KEYCODE_DEL = "67"
ADB_KEYCODE_GRAVE = "68"
ADB_KEYCODE_MINUS = "69"
ADB_KEYCODE_EQUALS = "70"
ADB_KEYCODE_LEFT_BRACKET = "71"
ADB_KEYCODE_RIGHT_BRACKET = "72"
ADB_KEYCODE_BACKSLASH = "73"
ADB_KEYCODE_SEMICOLON = "74"
ADB_KEYCODE_APOSTROPHE = "75"
ADB_KEYCODE_SLASH = "76"
ADB_KEYCODE_AT = "77"
ADB_KEYCODE_NUM = "78"
ADB_KEYCODE_HEADSETHOOK = "79"
ADB_KEYCODE_FOCUS = "80"
ADB_KEYCODE_PLUS = "81"
ADB_KEYCODE_MENU = "82"
ADB_KEYCODE_NOTIFICATION = "83"
ADB_KEYCODE_SEARCH = "84"