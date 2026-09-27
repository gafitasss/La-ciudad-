import os
import sqlite3

DB_PATH = "data/game.db"


def get_connection():
    os.makedirs("data", exist_ok=True)

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    return connection


def init_database():
    connection = get_connection()

    connection.execute("""
        CREATE TABLE IF NOT EXISTS players (
            id INTEGER PRIMARY KEY,
            username TEXT,
            money INTEGER DEFAULT 1000,
            xp INTEGER DEFAULT 0,
            level INTEGER DEFAULT 1,
            health INTEGER DEFAULT 100,
            energy INTEGER DEFAULT 100,
            fame INTEGER DEFAULT 0
        )
    """)

    connection.commit()
    connection.close()


def get_player(player_id):
    connection = get_connection()

    player = connection.execute(
        """
        SELECT *
        FROM players
        WHERE id = ?
        """,
        (player_id,)
    ).fetchone()

    connection.close()

    return player


def create_player(player_id, username):
    connection = get_connection()

    connection.execute(
        """
        INSERT OR IGNORE INTO players
        (id, username)
        VALUES (?, ?)
        """,
        (player_id, username)
    )

    connection.commit()
    connection.close()


def update_player(player_id, **values):
    if not values:
        return

    connection = get_connection()

    fields = ", ".join(
        f"{key} = ?" for key in values
    )

    parameters = list(values.values())
    parameters.append(player_id)

    connection.execute(
        f"""
        UPDATE players
        SET {fields}
        WHERE id = ?
        """,
        parameters
    )

    connection.commit()
    connection.close()
