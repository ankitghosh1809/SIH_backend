_FAKE_STORE = {"scans": {}, "metrics": []}
def get_session():
    yield _FAKE_STORE
def init_db():
    pass
