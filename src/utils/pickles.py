from copy import deepcopy
from playstore.app_validator import AppValidator
from playstore.validation_report import ValidationReport


class ValidationReportPickle:
    ''' Bundles the information needed to pass through the queue.
     '''
    def __init__(self, report: ValidationReport):
        self.report_title = report.report_title
        self.report = report.report

class AppValidatorPickle:
    ''' Bundles the information needed to pass through the queue.

        ObjDetector uses yolo code and it has lambdas, cannot pickle entire class.

     '''
    def __init__(self, validator: AppValidator):
        self.report = deepcopy(ValidationReportPickle(validator.report))
