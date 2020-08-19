import logging

logging.basicConfig(level=logging.DEBUG)


class ETest(Exception):
    pass


try:
    raise ETest("Hi!")
except ETest as e:
    print(e)
    print(repr(e))
    print(type(e))
    print(e.__dict__)
    logging.debug(e)
    logging.error(e)
    logging.warning(e)
    logging.info(e)
    logging.critical(e)
