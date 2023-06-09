from collections import defaultdict
from multiprocessing import Process, Queue
from typing import Any, Dict
from playstore.validation_report import ValidationReport
from utils.logging_utils import StatsLogger, p_alert, p_blue, p_cyan, p_purple
from utils.utils import AppStatus, nested_default_dict


class ValidationReportStats:
    ''' Given a list of reports, calculate stats section.
    '''
    def __init__(self, queue: Queue):
        self.__queue = queue
        self.process = None
        # self.nested_dict = nested_default_dict
        # self.nested_dict = lambda: defaultdict(self.nested_dict)
        self.reports = nested_default_dict()



    @staticmethod
    def default_item():
        return {
            'total_apps': 0,
            'total_invalid': 0,
            'total_failed': 0,
            'total_passed': 0,
        }

    def task(self, queue: Queue):

        reports = nested_default_dict()
        stats_by_device: Dict[Any] = defaultdict(dict)
        stats: Dict = dict()
        logger = StatsLogger()
        p_alert("Started stats task")
        while True:
            if not queue.empty():
                # Given some updated report
                status_obj: ValidationReport.default_dict = queue.get()
                reports[status_obj['report_title']][status_obj['package_name']] = status_obj

                stats, stats_by_device = ValidationReportStats.calc(reports)
                current_stats = ValidationReportStats.get_stats(stats, stats_by_device)
                logger.log(current_stats)

    def start(self):
        self.process = Process(target=self.task, args=(self.__queue, ))
        self.process.start()

    def stop(self):
        self.process.terminate()

    @staticmethod
    def calc(all_reports: Dict):
        '''

            Args:
             - all_reports: Is a nested default dictionary
        '''
        total_apps = 0
        all_invalid = defaultdict(str)
        total_invalid = 0
        total_failed = 0

        devices = defaultdict(ValidationReportStats.default_item)

        for report_title, dreport in all_reports.items():
            for package_name, status_obj in dreport.items():
                total_apps += 1
                devices[report_title]['total_apps'] += 1



                if status_obj["status"] == AppStatus.INVALID:
                    all_invalid[package_name] = status_obj['name']
                    devices[report_title]['total_invalid'] += 1

                if status_obj['status'] == AppStatus.FAIL:
                    total_failed += 1
                    devices[report_title]['total_failed'] += 1

                devices[report_title]['total_passed'] = devices[report_title]['total_apps'] - devices[report_title]['total_failed']




        total_invalid = len(all_invalid.keys())

        # self.stats_by_device = devices
        stats = ValidationReportStats.default_item()
        stats['total_apps'] =  total_apps
        stats['total_invalid'] =  total_invalid
        stats['total_failed'] =  total_failed
        stats['total_passed'] =  total_apps - total_failed

        return stats, devices

    @staticmethod
    def get_stats(stats: Dict, stats_by_device: defaultdict(Any)):
        '''
        self.stats_by_device=defaultdict({
            'helios_192.168.1.238:5555': {
                'total_apps': 3, 'total_invalid': 1, 'total_failed': 2
            },
            'coachz_192.168.1.113:5555': {
                'total_apps': 3, 'total_invalid': 1, 'total_failed': 2
            },
            'eve_192.168.1.125:5555': {
                'total_apps': 3, 'total_invalid': 1, 'total_failed': 2
            }
        })

        self.stats={
            'total_apps': 9,
            'total_invalid': 1,
            'total_failed': 6,

            'all_invalid': defaultdict({
                'com.softinit.iquitos.whatswebscan': 'Whats Web Scan'
            })
        }

        '''
        S = []
        sorder = StatsLogger.stat_order()
        S.append("All devices")
        for key in sorder:
            val = stats[key]
            if isinstance(val, int):
                # name = key.replace("_", " ").title()
                # Absoulte, if app failed due to these reasons, it failed on all devices
                if key in ['total_invalid']:
                    S.append(f"\t{val * len(stats_by_device.items())} ({val})")
                else:
                    S.append(f"\t{val}")

        S.append(f"\n")


        for device_name, stats in stats_by_device.items():
            S.append(f"{device_name}")
            for key in sorder:
                val = stats[key]
                # name = key.replace("_", " ").title()
                S.append(f"\t{val}")
            S.append(f"\n")
        return ''.join(S)

    @staticmethod
    def print_stats(stats: Dict, stats_by_device: defaultdict(Any)):
        '''
        self.stats_by_device=defaultdict({
            'helios_192.168.1.238:5555': {
                'total_apps': 3, 'total_invalid': 1, 'total_failed': 2
            },
            'coachz_192.168.1.113:5555': {
                'total_apps': 3, 'total_invalid': 1, 'total_failed': 2
            },
            'eve_192.168.1.125:5555': {
                'total_apps': 3, 'total_invalid': 1, 'total_failed': 2
            }
        })

        self.stats={
            'total_apps': 9,
            'total_invalid': 1,
            'total_failed': 6,
            'all_invalid': defaultdict({
                'com.softinit.iquitos.whatswebscan': 'Whats Web Scan'
            })
        }

        '''
        HEADER = """
          _  _     _  _     _  _     _____ _        _           _  _     _  _     _  _
        _| || |_ _| || |_ _| || |_  /  ___| |      | |        _| || |_ _| || |_ _| || |_
       |_  __  _|_  __  _|_  __  _| \ `--.| |_ __ _| |_ ___  |_  __  _|_  __  _|_  __  _|
        _| || |_ _| || |_ _| || |_   `--. \ __/ _` | __/ __|  _| || |_ _| || |_ _| || |_
       |_  __  _|_  __  _|_  __  _| /\__/ / || (_| | |_\__ \ |_  __  _|_  __  _|_  __  _|
         |_||_|   |_||_|   |_||_|   \____/ \__\__,_|\__|___/   |_||_|   |_||_|   |_||_|  """

        p_cyan(HEADER, "\n\n")
        for key, val in stats.items():
            if isinstance(val, int):
                name = key.replace("_", " ").title()
                # Absoulte, if app failed, it failed on all devices
                if key in ['total_invalid']:
                    p_cyan(f"\t{name}: {val * len(stats_by_device.items())} ({val})")
                else:
                    p_cyan(f"\t{name}: {val}")

        p_blue("\n\n\tStats by device\n")
        for device_name, stats in stats_by_device.items():
            p_purple(f"\t{device_name}")
            for key, val in stats.items():
                name = key.replace("_", " ").title()
                p_cyan(f"\t\t{name}: {val}")

if __name__ == "__main__":
    pass