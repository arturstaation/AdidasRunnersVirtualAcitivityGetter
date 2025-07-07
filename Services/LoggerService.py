import logging

class LoggerService:
    def __init__(self):
        logging.basicConfig(
            level=logging.DEBUG,
            filename="application.log", 
            filemode="a", 
            format='[%(asctime)s] (%(levelname)s) - %(message)s',
            datefmt='%d-%b-%y %H:%M:%S'
        )

        console = logging.StreamHandler()
        console.setLevel(logging.DEBUG)
        formatter = logging.Formatter('[%(asctime)s] (%(levelname)s) - %(message)s', datefmt='%d-%b-%y %H:%M:%S')
        console.setFormatter(formatter)
        logging.getLogger().addHandler(console)