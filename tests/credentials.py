import os


class PakedgeCredentials():
    user = os.environ.get("PAKEDGE_USER")
    password = os.environ.get("PAKEDGE_PASS")
    host = os.environ.get("PAKEDGE_HOST")
