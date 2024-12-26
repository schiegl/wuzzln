import sqlite3

from wuzzln.data import Game


def insert(db: sqlite3.Connection, value: Game):
    if isinstance(value, Game):
        fields = Game._fields
    else:
        raise NotImplementedError(f"Unsupported insert type: {type(value)}")

    qmarks = ",".join("?" for _ in fields)
    fields_str = ",".join(fields)
    table = type(value).__name__
    query = f"INSERT INTO {table}({fields_str}) VALUES ({qmarks})"

    db.execute(query, value)


def exists(db: sqlite3.Connection, table: str, column: str, value) -> bool:
    query = f"SELECT exists(SELECT * FROM {table} WHERE {column} == ?)"
    row = db.execute(query, (value,)).fetchone()
    return row[0] == 1
