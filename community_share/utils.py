class StatusCodes(object):
    NOT_AUTHORIZED = 401
    OK = 200
    FORBIDDEN = 403
    NOT_FOUND = 404
    BAD_REQUEST = 400
    SERVER_ERROR = 500

def is_integer(s):
    try:
        f = float(s)
        if f % 1 == 0:
            return True
        else:
            return False
    except ValueError:
        return False

def is_email(s):
    if len(s) > 7:
        if re.match("^.+\\@(\\[?)[a-zA-Z0-9\\-\\.]+\\.([a-zA-Z]{2,3}|[0-9]{1,3})(\\]?)$", s) != None:
            return True
    return False

        

