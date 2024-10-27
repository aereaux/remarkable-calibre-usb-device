import logging


def log_args_kwargs(func):
    logger = logging.getLogger()

    def wrapper(*args, **kwargs):
        logger.debug(f"__ calibre_remarkable_usb_device call: {func.__name__}, Arguments: {args}, Keyword Arguments: {kwargs}")
        return func(*args, **kwargs)

    return wrapper
