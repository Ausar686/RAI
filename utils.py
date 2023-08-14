def method_logger(func):
    """
    Special decorator for logging RAI ChatBot methods.
    """
    
    def start_log(func_name, args, kwargs):
        strings = [
            f"[INFO]: EXECUTING: {func.__name__}",
            f"[INFO]: Args: {args}",
            f"[INFO]: Kwargs: {kwargs}"
        ]
        print("\n".join(strings))
        return
    
    def end_log(func_name, args, kwargs):
        strings = [
            f"[INFO]: FINISHED: {func.__name__}",
            f"[INFO]: Args: {args}",
            f"[INFO]: Kwargs: {kwargs}"
        ]
        print("\n".join(strings))
        return
        
    def safe_log(logger, obj, func_name, args, kwargs):
        try:
            if obj.log:
                logger(func_name, args, kwargs)
        except Exception:
            pass
        return
    
    def wrapper(*args, **kwargs):
        obj = args[0]
        safe_log(start_log, obj, func.__name__, args, kwargs)
        res = func(*args, **kwargs)
        safe_log(end_log, obj, func.__name__, args, kwargs)
        return res
    
    return wrapper


def retry(n_retries: int=5):
    """
    Retrying decorator function.
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            n = n_retries
            while n >= 0:
                try:
                    return func(*args, **kwargs)
                except Exception:
                    n -= 1
            else:
                raise ValueError("Amount of retries exceeded. Abort.")
        return wrapper
    return decorator