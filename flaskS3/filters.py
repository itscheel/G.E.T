import arrow, mimetypes, os

def dateformat(date):
    date_format = arrow.get(date)
    return date_format.humanize()

def gettype(file):
    data = os.path.splitext(file)
    extension = data[1]
    try:
        return mimetypes.types_map[extension]
    except Keyerror():
        return 'None'