import logging
import sys


def get_logger(name):
    # Setting up logger
    logger = logging.getLogger(name)
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    # All levels should pass root logger
    logger.setLevel(logging.DEBUG)

    # Creating handler for stdout logging levels DEBUG <= WARN
    out = logging.StreamHandler(sys.stdout)
    out.setFormatter(formatter)
    out.setLevel(logging.DEBUG)
    out.addFilter(type('', (logging.Filter,),
                       {'filter': staticmethod(lambda r: r.levelno <= logging.WARN)}))

    # Creating handler for stderr logging levels ERROR <
    err = logging.StreamHandler()
    err.setFormatter(formatter)
    err.setLevel(logging.ERROR)

    logger.addHandler(out)
    logger.addHandler(err)
    return logger
