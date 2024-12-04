from re import sub


CLEANUP_RE = r'(@.)|(\(\d,\d\))'


def get_clean_code(code: str) -> str:
    return sub(CLEANUP_RE, '', code)
