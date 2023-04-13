
from dataclasses import dataclass, fields


@dataclass
class AppLoginResults:
    google_logged_in: bool = False
    has_google: bool = False
    facebook_logged_in: bool = False
    has_facebook: bool = False
    email_logged_in: bool = False
    has_email: bool = False
    error_detected: bool = False


    def update_field(self, attempt_num: int, logged_in: bool, has_login: bool):
        '''
        0 - 0
        1 - 2
        2 - 4
        '''
        logged_in_idx = attempt_num*2
        has_log_in_idx = logged_in_idx + 1
        setattr(self, fields(self)[logged_in_idx].name, logged_in)
        setattr(self, fields(self)[has_log_in_idx].name, has_login)

    def to_byte(self):
        ''' Produce an int representing a byte.

        Useful for storing results in a single column.
        '''
        byte_str = "".join([str(int(val) )for val in self.__dict__.values()])
        print(f"{self.__dict__=}")
        print(f"{byte_str=}", int(byte_str, 2))
        return int(byte_str, 2)


    @staticmethod
    def from_byte(n: int):
        ''' Converts a number to an instance of this class.
        '''
        n = len(fields(AppLoginResults))
        bits = [False]*n
        if n > int("1"*n, 2) or n < 0:
            return AppLoginResults(*[False]*n)
        byte_str = bin(n)[2:]
        for i in range(len(byte_str)):
            bits[n-1-i] = bool(int((byte_str[i])))
        return AppLoginResults(*bits)


