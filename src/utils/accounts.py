import json
import sys
import requests
from utils.logging_utils import p_alert

from utils.utils import users_home_dir



class __AccountsAPI:
    def __init__(self):
        self.__filename = "apikey.txt"
        self.__api_key = self.__get_key()
        self.__base_url = "https://api.jsonbin.io/v3/b/6424ab5dc0e7653a05991f64"
        self.__accounts = dict()
        self.__fetch_accounts()

    @property
    def accounts(self):
        return self.__accounts

    def __get_key(self):
        ''' Reads API key from apikey.txt from home dir. '''
        key = ""
        with open(f"{users_home_dir()}/{self.__filename}") as f:
            key = f.readline()
        return key

    def __fetch_accounts(self):
        res = requests.get(f"{self.__base_url}", headers={'X-Access-Key': self.__api_key})
        if res.status_code == 200:
            self.__accounts = dict(json.loads(res.text)['record'])
            print(f"{self.__accounts=}")
        else:
            p_alert("Failed to load account information from jsonbin.io")
            sys.exit(1)


ACCOUNTS = __AccountsAPI().accounts