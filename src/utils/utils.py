from appium.webdriver.appium_service import AppiumService
import __main__
from datetime import datetime
import os
import re
import subprocess
from enum import Enum
from time import time
from typing import AnyStr, Dict, List
import cv2


class ArcVersions(Enum):
    '''
        Enumeration for each Android Version we intend to support.
    '''
    ARC_P = 1
    ARC_R = 2

class CrashType(Enum):
    '''
        Enumeration for the result when checking if a program crashed.
    '''
    SUCCESS = "Success"
    WIN_DEATH = "Win Death"
    FORCE_RM_ACT_RECORD = "Force removed ActivityRecord"

def get_cur_activty(transport_id: str, ArcVersion: ArcVersions = ArcVersions.ARC_R) -> List[str]:
    '''
        Gets the current activity running in the foreground.

        Params:
            transport_id: The transport id of the connected android device.
            ArcVersion: ArcVersion Enum for the device.

        Returns:
            A List of strings: [package_name, activity_name]
    '''
    MAX_WAIT_FOR_OPEN_APP = 420  # 7 mins
    t = time()
    while int(time() - t) < MAX_WAIT_FOR_OPEN_APP:
        try:
            '''

                ARC-P
                mResumedActivity: ActivityRecord{9588d06 u0 com.netflix.mediaclient/o.cwK t127}
                ARC-R
                mFocusedWindow=Window{b3ef1fc u0 NotificationShade} ## Sleep
                mFocusedWindow=Window{3f50b2f u0 com.netflix.mediaclient/com.netflix.mediaclient.acquisition.screens.signupContainer.SignupNativeActivity}
            '''
            keyword = ""
            if ArcVersion == ArcVersions.ARC_P:
                keyword = "mResumedActivity"
            if ArcVersion == ArcVersions.ARC_R:
                keyword = "mFocusedWindow"
            print("Key word ", ArcVersions.ARC_R, ArcVersion,  keyword)
            cmd = ('adb', '-t', transport_id, 'shell', 'dumpsys', 'activity',
                    '|', 'grep', keyword)
            text = subprocess.run(cmd, check=False, encoding='utf-8',
                capture_output=True).stdout.strip()
            print("res text: ", text)

            query = r".*{.*\s.*\s(?P<package_name>.*)/(?P<act_name>[\S\.]*)\s*.*}"
            result = re.search(query, text)

            if result is None:
                print("Cant find current activity.")
                return "",""

            print(result.group("package_name"), result.group("act_name"))
            return result.group("package_name"), result.group("act_name")
        except Exception as err:
            print("Err get_cur_activty ", err)
    return "",""

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
        while cur_package != package_name and int(time() - t) < MAX_WAIT_FOR_OPEN_APP:
            try:
                cur_package, act_name = get_cur_activty(transport_id, ArcVersion)
            except Exception as err:
                print("Err getting cur act", err)
        print(outstr)


    except Exception as err:
        print("Error opening app with monkey", err)
        return False
    return True

def close_app(package_name: str, transport_id: int):
    '''
        Opens an app using ADB monkey.

        Params:
            package_name: The name of the package to check crash logs for.
            transport_id: The transport id of the connected android device.
    '''
    try:
        cmd = ('adb', '-t', transport_id, 'shell', 'am', 'force-stop', package_name)
        outstr = subprocess.run(cmd, check=True, encoding='utf-8',
                                capture_output=True).stdout.strip()
        print(f"Closed {package_name}...")
        print(outstr)
    except Exception as err:
        print("Error closing app with monkey", err)
        return False
    return True

def adb_connect(ip: str):
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
        print(outstr)
    except Exception as err:
        print("Error connecting to ADB", err)
        return False
    return True

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
        "appium:uiautomator2ServerInstallTimeout": 60000
    }

def find_transport_id(ip_address)-> str:
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

def is_emulator(transport_id: str):
    ''' Checks if device is an emulator.

        Params:
            transport_id: The transport id of the connected android device.

        Returns:
            A boolean representing if it's an emulator or not.
    '''

    cmd = ('adb','-t', transport_id, 'shell', 'getprop', "ro.build.characteristics")
    try:
        res = subprocess.run(cmd, check=False, encoding='utf-8', capture_output=True).stdout.strip()
        print("Res: ", res)
        return res == "emulator"
    except Exception as err:
        print("Failed to check for emualtor", err)
    return False

def get_arc_version(transport_id: str):
    ''' Gets Android OS version on connected device.

        Params:
            transport_id: The transport id of the connected android device.

        Returns:
            An ENUM representing the Android Version [P, R] else None if
                release if not found from ADB getprop.


    '''
    cmd = ('adb','-t', transport_id, 'shell', 'getprop', "ro.build.version.release")
    try:
        res = subprocess.run(cmd, check=False, encoding='utf-8', capture_output=True).stdout.strip()
        print("Res: ", res)
        if res == "9":
            return ArcVersions.ARC_P
        elif res == "11":
            return ArcVersions.ARC_R
    except Exception as err:
        print("Cannot find Android Version", err)
    return None

def get_logs(start_time: str, transport_id: str):
    '''Grabs logs from ADB logcat starting at a specified time.

        Params:
            start_time: The formatted string representing the time the app was
                launched/ started.
            transport_id: The transport id of the connected android device.

        Returns

    '''
    cmd = ('adb', '-t', transport_id, 'logcat', 'time', '-t', start_time)  #
    logs =  subprocess.run(cmd, check=False, encoding='utf-8',
         capture_output=True).stdout.strip()
    return logs

def check_for_win_death(package_name: str, logs: str):
    ''' Searches logs for WIN DEATH record.

        12-28 17:48:37.233   153   235 I WindowManager: WIN DEATH: Window{913e5ce u0 com.Psyonix.RL2D/com.epicgames.ue4.GameActivity}

        Returns:
            A string representing the failing activity otherwise it returns an empty string.
    '''
    # adb logcat -v time -t 10:30:00

    win_death = rf"\d+-\d+\s\d+\:\d+\:\d+\.\d+\s*\d+\s*\d+\s*I WindowManager: WIN DEATH: Window{'{'}.*\s.*\s{package_name}/.*{'}'}"
    win_death_pattern = re.compile(win_death, re.MULTILINE)
    match = win_death_pattern.search(logs)
    if match:
        # print("match ", match.group(0))
        failed_activity = match.group(0).split("/")[-1][:-1]
        # print("failed act: ", failed_activity)
        return failed_activity
    return ""

def check_force_remove_record(package_name: str, logs: str):
    ''' Searches logs for Force remove ActivtyRecord.

        12-28 17:48:37.254   153  4857 W ActivityManager: Force removing ActivityRecord{f024fcc u0 com.Psyonix.RL2D/com.epicgames.ue4.GameActivity t195}: app died, no saved state

        Returns:
            A string representing the failing activity otherwise it returns an empty string.
    '''

    force_removed = rf"^\d+-\d+\s\d+\:\d+\:\d+\.\d+\s*\d+\s*\d+\s*W ActivityManager: Force removing ActivityRecord{'{'}.*\s.*\s{package_name}/.*\s.*{'}'}: app died, no saved state$"
    force_removed_pattern = re.compile(force_removed, re.MULTILINE)
    match = force_removed_pattern.search(logs)


    if match:
        print("match ", match.group(0))
        failed_activity = match.group(0).split("/")[-1][:-1].split(" ")[0]
        print("failed act: ", failed_activity)
        return failed_activity
    return ""

def check_crash(package_name: str, start_time: str, transport_id: str):
    ''' Grabs logcat logs starting at a specified time and check for crash logs.

        Params:
            package_name: The name of the package to check crash logs for.
            start_time: The formatted string representing the time the app was
                launched/ started.
            transport_id: The transport id of the connected android device.

        Return:
            A string representing the failing activity otherwise it returns an empty string.

    '''
    logs = get_logs(start_time, transport_id)

    failed_act: str = check_for_win_death(package_name, logs)
    if len(failed_act) > 0:
        return (CrashType.WIN_DEATH, failed_act)

    failed_act: str = check_force_remove_record(package_name, logs)
    if len(failed_act) > 0:
        return (CrashType.WIN_DEATH, failed_act)
    return (CrashType.SUCCESS, "")

def get_start_time():
    '''
        Gets current time and formats it properly to match ADB -t arg.

        This is used at the beginning of a test for an app.
        It will limit the amount logs we will need to search each run.

        Returns a string in the format "MM-DD HH:MM:SS.ms"
    '''
    return datetime.fromtimestamp(time()).strftime('%m-%d %H:%M:%S.%f')[:-3]


def is_package_installed(transport_id: str, package_name: str):
    ''' Checks if package is installed via ADB. '''
    # Call the adb shell pm list packages command
    result = subprocess.run(
        ['adb', '-t', transport_id, 'shell', 'pm', 'list', 'packages'],
        check=False, encoding='utf-8', capture_output=True
    ).stdout.strip()
    # Check the output for the package name
    return package_name in result

def stop_appium_server(service: AppiumService):
    ''' Stops the Appium Server running on port 4723'''
    service.stop()
    cmd = ["kill", "$(lsof -t -i :4723)"]
    res = subprocess.run(cmd, check=False, encoding='utf-8', capture_output=True).stdout.strip()


def get_root_path():
    root_path = os.path.realpath(__main__.__file__).split("/")[1:-1]
    root_path = '/'.join(root_path)
    return f"/{root_path}"

def lazy_start_appium_server():
    ''' Attempts to start Appium server. '''
    print("Starting Server")
    try:
        service = AppiumService()
        service.start(args=['--address', '0.0.0.0', '-p', str(4723), '--base-path', '/wd/hub'])
        # For some reason, interacting with service before returning has prevented random errors like:
        # Failed to establish a new connection: [Errno 111] Connection refused
        # Remote end closed
        while not service.is_listening or not service.is_running:
            print("Waiting for appium service to listen...")
        return service
    except Exception as error:
        print("Error starting appium server", str(error)[:50])
    return None

'''
Two problems


1. Getting screen shot with window titles
2. Detecting image.
3. Yolo obj detection

'''



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



# '''
# Apk Analyzer - AMAC-e
#  ActivityTaskManager: START u0 {act=android.intent.action.MAIN cat=[android.intent.category.LAUNCHER] id=window_session_id=8 flg=0x10200000 cmp=sk.styk.martin.apkanalyzer/.ui.main.MainActivity} from uid 1000



# '''
def create_dir_if_not_exists(directory):
    print("Create dir if not exist", directory)
    if not os.path.exists(directory):
        print("Creating dir: ", directory)
        os.makedirs(directory)

def file_exists(directory):
    return os.path.exists(directory)


# # Identify Android vs PWA & AMAC-e
def check_amace(driver, package_name: str) -> bool:
    # Grab screenshot of device
    # Look for AMAC-e image.
    names = ['amace_phone', 'amace_tablet', 'amace_resize']
    root_path = get_root_path()
    ss_path = f"{root_path}/apks/{package_name}/test.png"
    does_exist = file_exists(ss_path)

    print("Checking AMAC-e", ss_path[:100])
    ss = driver.get_screenshot_as_file(ss_path)
    for name in names:
        amace_icon_path = f"{get_root_path()}/images/templates/{name}.png"
        find_template(ss_path, amace_icon_path)
    return False


# '''
#     1. Pull APK from device
#     2. Store APK in /apks/package_name
#     3. Run aapt commands
#         - 1. Store Manifest in memory
#         - 2. Parse for version_name
#         - 3. Save Manifest in apks/package_name


# '''



def gather_app_info(transport_id: str, package_name: str):
    '''
    Downloads APK & manifest from App and extracts information from Manifest.
    '''
    has_apk = get_apk(transport_id, package_name)
    manifest = download_manifest(package_name)
    print(manifest[:200])
    app_info = get_app_info(manifest)
    return app_info

def get_apk(transport_id: str, package_name: str) -> bool:
    ''' Grabs the APK from device.

        adb shell pm path package_name

        package:/data/app/~~-TjCwRkZEFass6mjqTzMtg==/com.netflix.mediaclient-mPHhWQM2xwIJco8coL6OYg==/base.apk
        # package:/data/app/~~-TjCwRkZEFass6mjqTzMtg==/com.netflix.mediaclient-mPHhWQM2xwIJco8coL6OYg==/split_config.en.apk
        # package:/data/app/~~-TjCwRkZEFass6mjqTzMtg==/com.netflix.mediaclient-mPHhWQM2xwIJco8coL6OYg==/split_config.mdpi.apk
        # package:/data/app/~~-TjCwRkZEFass6mjqTzMtg==/com.netflix.mediaclient-mPHhWQM2xwIJco8coL6OYg==/split_config.x86_64.apk

        JUST NEED BASE APK FOR MAIN INFO

        Grabs APK via ADB PULL /path/to/apk
        and stores it in /apks/<package_name>

        Returns True when APK is in required location. False otherwise.
    '''
    print("Gettign APK ", package_name)

    if not is_package_installed(transport_id, package_name):
        return False

    root_path = get_root_path()
    dl_dir = f"{root_path}/apks/{package_name}"
    create_dir_if_not_exists(dl_dir)

    does_exist = file_exists(f"{root_path}/apks/{package_name}/base.apk")
    if does_exist:
        return True

    cmd = ('adb', '-t', transport_id, 'shell', 'pm', 'path', package_name )
    print("File exists ", does_exist)
    outstr = subprocess.run(cmd, check=True, encoding='utf-8',
                                capture_output=True).stdout.strip()
    apk_path = None
    for line in outstr.split("\n"):
        if 'base.apk' in line:
            apk_path = line[len("package:"):]

    print(f"Found apk path: {apk_path}")



    print("Pulling APK: ", package_name)

    cmd = ('adb', '-t', transport_id, 'pull', apk_path, dl_dir )
    outstr = subprocess.run(cmd, check=True, encoding='utf-8',
                                capture_output=True).stdout.strip()

    return True


def get_aapt_version():
    '''
        Returns path of the latest version of aapt installed on host device.
    '''
    android_home = os.environ.get("ANDROID_HOME")
    # aapt = f"{android_home}/build-tools/*/aapt"
    aapt = f"{android_home}/build-tools/"
    items = os.listdir(aapt)

    # Iterate over the items
    for item in items[::-1]:
        return  os.path.join(aapt, item, "aapt")
    return ""

# App version
def get_app_info(manifest_text: str)  -> dict:
    ''' Grabs the App version from ...
    '''

    info_line = manifest_text.split("\n")[0]
    # Define the regular expression pattern
    pattern = r"name='(?P<name>.*?)' versionCode='(?P<versionCode>.*?)' versionName='(?P<versionName>.*?)' compileSdkVersion='(?P<compileSdkVersion>.*?)' compileSdkVersionCodename='(?P<compileSdkVersionCodename>.*?)'"

    # Search for the pattern in the string
    match = re.search(pattern, info_line)

    # Extract the groups
    if match:
        info = {
            'name': match.group("name"),
            'versionCode': match.group("versionCode"),
            'versionName': match.group("versionName"),
            'compileSdkVersion': match.group("compileSdkVersion"),
            'compileSdkVersionCodename': match.group("compileSdkVersionCodename")
        }

        # print(f'Match found!  {info}')
        return info
    else:
        print("No match found.")




    return dict()

# Manifest DL
def download_manifest(package_name: str):
    ''' Grabs the APK Manifest from ...  '''
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


    aapt = get_aapt_version()
    root_path = get_root_path()
    manifest_path = f"{root_path}/apks/{package_name}/manifest.txt"
    apk_path = f"{root_path}/apks/{package_name}/base.apk"

    if file_exists(manifest_path):
        with open(manifest_path, 'r', encoding='utf-8') as f:
            return f.read()

    cmd = (aapt, "dump", "badging", apk_path)
    manifest = subprocess.run(cmd, check=True, encoding='utf-8',
                                capture_output=True).stdout.strip()

    with open(manifest_path, 'w', encoding='utf-8') as f:
        f.write(manifest)

    return manifest


# Games vs App - Surface View check
def has_surface_name(transport_id: str, package_name: str) -> str:
    """
    Returns the surface name for a given package name.
    Args:
        package_name: A string representing the name of the application to
            be targeted.
    Returns:
        A string representing a surface name of the package name.
    """
    pattern_with_surface = rf"""^SurfaceView\s*-\s*
                        (?P<package>{package_name})     # Package name
                        /[\w.#]*$"""                    # Surface window

    re_surface = re.compile(pattern_with_surface, re.MULTILINE | re.IGNORECASE | re.VERBOSE)
    cmd = ('adb', '-t', transport_id, 'shell', 'dumpsys', 'SurfaceFlinger', '--list')
    surfaces_list = subprocess.run(cmd, check=True, encoding='utf-8',
                                    capture_output=True).stdout.strip()

    last = None
    for match in re_surface.finditer(surfaces_list):
        last = match
    if last:
        if package_name != last.group('package'):
            # return (f'Surface not found for package {package_name}. '
            #                 'Please ensure the app is running.')
            return False

        # UE4 games have at least two SurfaceView surfaces. The one
        # that seems to in the foreground is the last one.
        # return last.group()
        return True


    pattern_without_surface = rf"""^(?P<package>{package_name})/[\w.#]*$"""
    re_without_surface = re.compile(
        pattern_without_surface, re.MULTILINE | re.IGNORECASE | re.VERBOSE)
    # Fallback: SurfaceView was not found.
    matches_without_surface = re_without_surface.search(
        surfaces_list)
    if matches_without_surface:
        if package_name != matches_without_surface.group('package'):
            return False
            # return (f'Surface not found for package {package_name}. '
            #                 'Please ensure the app is running.')
        # return matches_without_surface.group()
        return True

# Ip Address of machien Running Appium Server
EXECUTOR = 'http://192.168.0.175:4723/wd/hub'
PLAYSTORE_PACKAGE_NAME = "com.android.vending"
PLAYSTORE_MAIN_ACT = "com.google.android.finsky.activities.MainActivity"

# Labels for YOLOv5
LOGIN = 'Login Field'
PASSWORD = 'Password Field'
CONTINUE = 'Continue'
GOOGLE_AUTH = 'Google Auth'
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

PACKAGE_NAMES = [
    # [ "Rocket League Sideswipe", "com.Psyonix.RL2D"],
    # ['Apk Analyzer', 'sk.styk.martin.apkanalyzer'],
    ['Roblox', 'com.roblox.client'],
    # ['Showmax', 'com.showmax.app'],  # NA in region
    # ['Epic Seven', 'com.stove.epic7.google'], #  Failed send keys
    # ['Legión Anime Tema Oscuro', 'aplicaciones.paleta.alterlegionanime'],  # Fialst o send keys
    # ['Garena Free Fire', 'com.dts.freefireth'],
    # ['My Boy! - GBA Emulator', 'com.fastemulator.gba'],  # Purchase required, unable to install...
    # ['Messenger', 'com.facebook.orca'],
    ['Netflix', 'com.netflix.mediaclient'],  # Unable to take SS of app due to protections.
    ['YouTube Kids', 'com.google.android.apps.youtube.kids'],
    ['Messenger', 'com.facebook.orca'],
    ['Gacha Club', 'air.com.lunime.gachaclub'],
    ['Messenger Kids', 'com.facebook.talk'],
    ['Among Us!', 'com.innersloth.spacemafia'],
    ['Gacha Life', 'air.com.lunime.gachalife'],
    ['Tubi TV', 'com.tubitv'],
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
    ['Subway Surfers', 'com.kiloo.subwaysurf'],
    ['Episode', 'com.episodeinteractive.android.catalog'],
    ['Block Craft 3D', 'com.fungames.blockcraft'],
    ['MobilityWare Solitaire', 'com.mobilityware.solitaire'],
    ['The Sims FreePlay', 'com.ea.games.simsfreeplay_na'],
    ['ITV Player', 'air.ITVMobilePlayer'],
    ['Family Farm Adventure', 'com.farmadventure.global'],
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
    ['Solitaire Classic', 'com.freegame.solitaire.basic2'],
    ['Summoners War', 'com.com2us.smon.normal.freefull.google.kr.android.common'],
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
    ['Spider Solitaire', 'at.ner.SolitaireSpider'],
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
    ['Audible', 'com.audible.application'],
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
    ['Adobe Lightroom', 'com.adobe.lrmobile'],
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
    ['Miracle Nikki', 'com.elex.nikkigp'],
    ['CrossOver on Chrome OS Beta', 'com.codeweavers.cxoffice'],
    ['Pocket Mortys', 'com.turner.pocketmorties'],
    ['Wish - Shopping Made Fun', 'com.contextlogic.wish'],
    ['Scary Teacher 3D', 'com.zakg.scaryteacher.hellgame'],
    ['FreeCell Solitaire', 'at.ner.SolitaireFreeCell'],
    ['Solitaire Card Games Free', 'com.Nightingale.Solitaire.Card.Games.Free'],
    ['250+ Solitaire Collection', 'com.anoshenko.android.solitaires'],
    ['NOOK', 'bn.ereader'],
    ['Evony', 'com.topgamesinc.evony'],
    ['Wonder Merge - Magic Merging and Collecting Games', 'com.cookapps.wonder.merge.dragon.magic.evolution.merging.wondermerge'],
    ['Wood Block Puzzle - Free Classic Block Puzzle Game', 'puzzle.blockpuzzle.cube.relax'],
    ['Hungry Shark Evolution', 'com.fgol.HungrySharkEvolution'],
    ['Mergical', 'com.fotoable.mergetown'],
    ["Diggy's Adventure", 'air.com.pixelfederation.diggy'],
    ['My Talking Angela', 'com.outfit7.mytalkingangelafree'],
    ['The Tribez', 'com.gameinsight.tribez'],
    ['Job Search', 'com.indeed.android.jobsearch'],
    ['GyaO', 'jp.co.yahoo.gyao.android.app'],
    ['Evernote', 'com.evernote'],
    ['Earn Cash & Money Rewards - CURRENT Music Screen', 'us.current.android'],
    ['Talking Tom Gold Run', 'com.outfit7.talkingtomgoldrun'],
    ['Hollywood Story', 'org.nanobit.hollywood'],
    ['hayu', 'com.upst.hayu'],
    ['NPO', 'nl.uitzendinggemist'],
    ['V - Real-time celeb broadcasting app', 'com.naver.vapp'],
    ['Cash Frenzy', 'slots.pcg.casino.games.free.android'],
    ['Crayola Scribble Scrubbie Pets', 'com.crayolallc.crayola_scribble_scrubbie_pets'],
    ['SALTO, TV & streaming illimités dans une seule app', 'fr.salto.app'],
    ['Catwalk Beauty', 'com.catwalk.fashion.star'],
    ['Mahjong Solitaire', 'com.mobilityware.MahjongSolitaire'],
    ['Pepi Tales: Kings Castle', 'com.PepiPlay.KingsCastle'],
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
    ["TV d'Orange", 'com.orange.owtv'],
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
    ['1v1.LOL', 'lol.onevone'],
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
    ['Colorscapes Plus - Color by Number, Coloring Games', 'com.artlife.color.number.coloring.games'],
    ['Transformers: Earth Wars', 'com.backflipstudios.transformersearthwars'],
    ['Web Video Cast | Browser to TV/Chromecast/Roku/+', 'com.instantbits.cast.webvideo'],
    ['Plurall', 'com.kongros.plurall'],
    ['Spades Royale', 'com.bbumgames.spadesroyale'],
    ['TextingStory', 'com.textingstory.textingstory'],
    ['My PlayHome Plus', 'com.playhome.plus'],
    ['Flipboard', 'flipboard.app'],
    ['Cross Stitch', 'com.inapp.cross.stitch'],
    ['Who is? Brain Teaser & Riddles', 'com.unicostudio.whois'],
    ['thinkorswim', 'com.devexperts.tdmobile.platform.android.thinkorswim'],
    ['Slots Casino Games by Huuuge', 'com.huuuge.casino.slots'],
    ['Mahjong', 'com.fenghenda.mahjong'],
    ['Galaxy Attack: Alien Shooter', 'com.alien.shooter.galaxy.attack'],
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