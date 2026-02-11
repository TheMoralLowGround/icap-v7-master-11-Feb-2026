"""
Organization: AIDocbuilder Inc.
File: timeout_utils.py
Version: 6.0
 
Authors:
    - Vinay - Initial implementation
 
Last Updated By: Vinay
Last Updated At: 2023-11-01
 
Description:
    This script execute a function with a specified timeout.
 
Dependencies:
    - Process from multiprocessing
 
Main Features:
    - Terminate the process when the timeout is reached.
"""
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
