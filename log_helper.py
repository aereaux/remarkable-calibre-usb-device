def log_args_kwargs(func):
    def wrapper(*args, **kwargs):
        print(f"__ calibre_remarkable_usb_device call: {func.__name__}, Arguments: {args}, Keyword Arguments: {kwargs}")
        return func(*args, **kwargs)

    return wrapper
