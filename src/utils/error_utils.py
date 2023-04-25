
from datetime import datetime
from enum import Enum
import re
import subprocess
from time import time
from typing import Dict, Tuple
from utils.app_utils import dumpysys_activity, is_ANR
from utils.device_utils import ArcVersions
from utils.logging_utils import p_alert


class CrashTypes(Enum):
    '''
        Enumeration for the result when checking if a program crashed.
    '''
    SUCCESS = "Success"
    WIN_DEATH = "Win Death"
    FORCE_RM_ACT_RECORD = "Force removed ActivityRecord"
    ANR = "App not responding"
    FDEBUG_CRASH = "F DEBUG crash"
    FATAL_EXCEPTION = "Fatal Exception"

class ErrorDetector:
    ''' Detects crashes from Logcat and ANRs from Dumpsys activity.


       Finds logs from logcat starting at self.__start_time, which is when
       the program starting validating the app/ package.

        Each time we check for a crash, we grab the logs from the beginning and then check for
        a variety of crash types.
    '''
    def __init__(self, transport_id: str, ArcVersion: ArcVersions):
        self.__transport_id = transport_id
        self.__package_name = ""
        self.__ArcVersion = ArcVersion
        self.__start_time = None  # Logcat logs starting at time
        self.reset_start_time()
        self.__logs = ""  # Store logs from ADB logcat output to search through
        self.__clean_logs = []  # Collects chunks of logs surrounding the errors that are found.

    @property
    def logs(self):
        ''' Returns all logs found.'''
        return self.__escape("".join(self.__clean_logs))

    def __escape(self, logs):
        return logs.replace("\n", "\\n")

    def get_package_name(self):
        return self.__package_name

    def update_package_name(self, package_name: str):
        self.__package_name = package_name

    def update_transport_id(self, transport_id: str):
        self.__transport_id = transport_id

    def update_arc_version(self, ArcVersion: ArcVersions):
        self.__ArcVersion = ArcVersion

    def __get_logs(self):
        '''Grabs logs from ADB logcat starting at a specified time.

            Params:
                start_time: The formatted string representing the time the app was
                    launched/ started.
                transport_id: The transport id of the connected android device.

            Returns

        '''
        # Sometimes Logcat with return bytes that arent able to be encoded and throws an error
        # So we use 'getoutput' to avoid this. Also, we need to make the start time arg wrapped in string
        # So that it see it as a single argument.
        cmd = ('adb', '-t', self.__transport_id, 'logcat', 'time', '-t', f"'{self.__start_time}'")
        self.__logs =  subprocess.getoutput(" ".join(cmd))

    def __add_clean_logs(self, match: re.Match):
        ''' Given a match, store the previous/subsequent 10 lines of the match.
            The goal is to avoid storing all logs. Sometimes this would be 50,000+ chars and
            doesnt work well with Google sheets. Its also unneccessary.

            We ideally need only the 10 lines surrounding the error.
        '''
        if not type(match) is re.Match:
            return
        line_len = 160 * 10  # Chars per line * num_lines
        start = match.start() - line_len if match.start() - line_len >= 0 else match.start()
        end = match.end() + line_len if match.end() + line_len < len(self.__logs) else match.end()
        self.__clean_logs.append(self.__logs[start: end])


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
            self.__add_clean_logs(match)
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
            self.__add_clean_logs(match)
            failed_activity = match.group(0).split("/")[-1][:-1].split(" ")[0]
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
        force_removed = rf".*>>> {self.__package_name} <<<.*"
        force_removed_pattern = re.compile(force_removed, re.MULTILINE)
        match = force_removed_pattern.search(self.__logs)

        if match:
            self.__add_clean_logs(match)
            return '', match.group(0)
        return "", ""

    def __check_for_ANR(self) -> bool:
        ''' Checks dumpsys for ANR.
        '''
        dumpsys_act_text = dumpysys_activity(self.__transport_id, self.__ArcVersion)
        return is_ANR(dumpsys_act_text, self.__package_name)

    def __check_fatal_exception(self):
        ''' Searches logs for E AndroidRuntime FatalException.

            03-17 13:02:33.018 12849 12849 E AndroidRuntime: FATAL EXCEPTION: main
            03-17 13:02:33.018 12849 12849 E AndroidRuntime: Process: com.picsart.studio, PID: 12849
            03-17 13:02:33.018 12849 12849 E AndroidRuntime: java.lang.ExceptionInInitializerError


            Returns:
                A string representing the failing activity otherwise it returns an empty string.
        '''
        ts_pattern = rf"^\d+-\d+\s\d+\:\d+\:\d+\.\d+\s*\d+\s*\d+\s*"
        force_removed = rf"^\d+-\d+\s\d+\:\d+\:\d+\.\d+\s*\d+\s*\d+\s*E AndroidRuntime: FATAL EXCEPTION.*\n.*{self.__package_name}.*\n.*\n.*$"
        force_removed_pattern = re.compile(force_removed, re.MULTILINE)
        match = force_removed_pattern.search(self.__logs)

        if match:
            self.__add_clean_logs(match)
            no_timestamp_string = re.sub(ts_pattern, "", match.group(0), flags=re.MULTILINE)
            failed_activity = 'Failed to open due to crash'
            failed_msg =  ' ~ '.join(no_timestamp_string.split("E AndroidRuntime: ")).replace("\n", "").replace("\t", "").strip()
            return failed_activity, failed_msg
        return "", ""

    def check_crash(self)-> Dict[CrashTypes, Tuple[CrashTypes, str, str]]:
        ''' Grabs logcat logs starting at a specified time and check for crash logs.

            Params:
                package_name: The name of the package to check crash logs for.

                transport_id: The transport id of the connected android device.

            Return:
                A string representing the failing activity otherwise it returns an empty string.
        '''
        try:
            self.__get_logs()
            self.reset_start_time()
            '''
                Need to check ea error and not break early.
                Win death can come befre a F debug crash but we would be more interested in F debug
            '''
            errors = dict()
            failed_act, match = self.__check_fatal_exception()
            if failed_act:
                errors[CrashTypes.FATAL_EXCEPTION] = (CrashTypes.FATAL_EXCEPTION, failed_act, match, )

            failed_act, match = self.__check_for_win_death()
            if failed_act:
                errors[CrashTypes.WIN_DEATH] = (CrashTypes.WIN_DEATH, failed_act, match, )

            failed_act, match = self.__check_force_remove_record()
            if failed_act:
                errors[CrashTypes.WIN_DEATH] = (CrashTypes.WIN_DEATH, failed_act, match, )

            failed_act, match = self.__check_f_debug_crash()
            if match:
                errors[CrashTypes.FDEBUG_CRASH] = (CrashTypes.FDEBUG_CRASH, failed_act, match, )

            if self.__check_for_ANR():
                errors[CrashTypes.ANR] = (CrashTypes.ANR, "unknown activity", "ANR detected.", )

            if len(errors.keys()):
                return errors
        except Exception as error:
            p_alert(f"Error in ErrorDetector: {self.__transport_id=} {self.__package_name}", error)
            self.reset_start_time()
        return {CrashTypes.SUCCESS: (CrashTypes.SUCCESS, "", "",)}

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
