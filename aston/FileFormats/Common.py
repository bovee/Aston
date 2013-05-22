import re


def find_offset(f, search_str, hint=None):
    if hint is None:
        hint = 0
    f.seek(hint)
    regexp = re.compile(search_str)
    while True:
        d = f.read(len(search_str) * 200)
        srch = regexp.search(d)
        if srch is not None:
            foff = f.tell() - len(d) + srch.end()
            break
        if len(d) == len(search_str):  # no data read: EOF
            return None
        f.seek(f.tell() - len(search_str))
    return foff
