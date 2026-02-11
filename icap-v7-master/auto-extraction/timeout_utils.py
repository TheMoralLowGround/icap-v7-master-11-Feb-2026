from multiprocessing import Process


class FunctionTimedOut(Exception):
    pass


def func_timeout(timeout, func, args=(), kwargs={}):
    """Execute a function with a timeout limit"""
    p1 = Process(target=func, args=args, kwargs=kwargs)
    p1.start()
    p1.join(timeout)
    if p1.is_alive():
        p1.kill()
        raise FunctionTimedOut()
