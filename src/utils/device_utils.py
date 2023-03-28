from dataclasses import dataclass
from enum import Enum
import subprocess

class ArcVersions(Enum):
    '''
        Enumeration for each Android Version we intend to support.
    '''
    UNKNOWN = -1
    ARC_P = 9
    ARC_R = 11

class BuildChannels(Enum):
    '''
        Enumeration for each build channel for ChromeOS.
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


@dataclass(frozen=True)
class DeviceData:
    ''' Holds device information. '''
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
    ''' Simple class to connect and query a device for its information. '''
    def __init__(self, ip: str):
        self.__is_connected = self.__adb_connect(ip)
        self.__transport_id = self.__find_transport_id(ip)
        self.__device_info = DeviceData(**{
            'ip': ip,
            'transport_id': self.__transport_id,
            'is_emu': self.__is_emulator(),
            'arc_version': self.__get_arc_version(),
            'device_name': self.__get_device_name(),
            'channel': self.__get_device_build_channel(),
            'wxh': self.__get_display_size(),
            'arc_build': self.__get_arc_build(),
            'product_name': self.__get_product_name(),
        })

    def __str__(self):
        return f"{self.__device_info.device_name}({self.__device_info.arc_version}): {self.__device_info.channel} - {self.__device_info.arc_build} - {self.__device_info.product_name}"

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
        width, height = 0, 0
        try:
            res = subprocess.run(cmd, check=False, encoding='utf-8', capture_output=True).stdout.strip()
            print(f"Dispaly size: {res=}")
            size_str = res.split(": ")[1]  # Extract the string after the colon
            width, height = map(int, size_str.split("x"))  # Split the string into width and height, and convert them to integers
        except Exception as err:
            print("Cannot find __get_display_size", err)
        return width, height

    def __get_arc_build(self):
        cmd = ('adb','-t', self.__transport_id, 'shell', 'getprop', "ro.build.display.id")
        try:
            res = subprocess.run(cmd, check=False, encoding='utf-8', capture_output=True).stdout.strip()
            return res
        except Exception as err:
            print("Cannot find __get_arc_build", err)
        return None

    def __get_product_name(self):
        '''ro.product.name'''
        cmd = ('adb','-t', self.__transport_id, 'shell', 'getprop', "ro.product.name")
        try:
            res = subprocess.run(cmd, check=False, encoding='utf-8', capture_output=True).stdout.strip()
            return res
        except Exception as err:
            print("Cannot find __get_product_name", err)
        return None

    @property
    def info(self) -> DeviceData:
        return self.__device_info
