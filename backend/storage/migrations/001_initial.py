from backend.app.database import init_main_db, init_lake_db


def run():
    init_main_db()
    init_lake_db()
