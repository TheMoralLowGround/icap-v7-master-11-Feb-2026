def populate_error_response(data={}, error="", traceback=None, messages=[]):
    response = {
        "data": data,
        "error": str(error),
        "traceback": traceback,
        "messages": messages,
    }
    return response
