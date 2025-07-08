import logging
from typing import Self

class LoggerService:
    def __init__(self : Self):
        logging.basicConfig(
            level=logging.DEBUG,
            filename="application.log", 
            filemode="a", 
            format='[%(asctime)s] (%(levelname)s) - %(message)s',
            datefmt='%d-%b-%y %H:%M:%S'
        )
        
        logging.getLogger("seleniumwire").setLevel(logging.WARNING)

        logging.getLogger("mitmproxy").setLevel(logging.WARNING)
        logging.getLogger("hpack").setLevel(logging.WARNING)

        console = logging.StreamHandler()
        console.setLevel(logging.DEBUG)
        formatter = logging.Formatter('[%(asctime)s] (%(levelname)s) - %(message)s', datefmt='%d-%b-%y %H:%M:%S')
        console.setFormatter(formatter)
        logging.getLogger().addHandler(console)