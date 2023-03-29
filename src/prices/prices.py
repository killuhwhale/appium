

import logging
from multiprocessing import Process, Queue

from utils.utils import users_home_dir

class PriceLogger:
    ''' Logs stats as each app is completed.  '''

    def __init__(self):
        self.filename = f'{users_home_dir()}/app_prices.tsv'
        logger = logging.getLogger('app_prices')
        logger.setLevel(logging.DEBUG)

        self.__header = f"App title\tPackage name\tPrice\n"
        # Create a file handler for the logger

        file_handler = logging.FileHandler(self.filename)
        file_handler.setLevel(logging.DEBUG)

        # Create a formatter for the file handler
        formatter = logging.Formatter('%(message)s')
        file_handler.setFormatter(formatter)

        # Add the file handler to the logger
        logger.addHandler(file_handler)
        self.__logger = logger
        self.__clear()

    @property
    def logger(self):
        return self.__logger

    def __clear(self):
        with open(self.filename, 'w') as f:
            f.write(self.__header)


    def log(self, *args, **kwargs):
        message = ' '.join(map(str, args))
        self.__logger.info(message)



def task(queue: Queue, logger: PriceLogger):
    print("Started prices task.")
    while True:
        if not queue.empty():

            price_info = queue.get()  # [title, packagename, price]
            print("Recv'd price info: ",  price_info)
            logger.log(*price_info)


class Prices:
    ''' A class to start a task and manage a task.
        The task is to record price of apps.
    '''
    def __init__(self, price_queue: Queue):
        self.__price_logger = PriceLogger()
        self.__price_queue = price_queue
        self.process = None


    def start(self):
        self.process = Process(target=task, args=(self.__price_queue, self.__price_logger, ))
        self.process.start()

    def stop(self):
        try:
            self.process.kill()
        except Exception as e:
            print("Error prices: ", e)
