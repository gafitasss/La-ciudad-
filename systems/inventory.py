import sqlite3

from database import get_connection


RARITIES = {
    "common": "⚪ Común",
    "uncommon": "🟢 Poco común",
    "rare": "🔵 Raro",
    "epic": "🟣 Épico",
    "legendary": "🟠 Legendario",
    "mythic": "🔴 Mítico",
}


def init_inventory():
    connection = get_connection()

    connection.execute("""
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id INTEGER NOT NULL,
            item_name TEXT NOT NULL,
            rarity TEXT NOT NULL,
            attack INTEGER DEFAULT 0,
            defense INTEGER DEFAULT 0,
            luck INTEGER DEFAULT 0
        )
    """)

    connection.commit()
    connection.close()


def add_item(
    player_id,
    item_name,
    rarity="common",
    attack=0,
    defense=0,
    luck=0
):
    connection = get_connection()

    connection.execute(
        """
        INSERT INTO inventory
        (
            player_id,
            item_name,
            rarity,
            attack,
            defense,
            luck
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            player_id,
            item_name,
            rarity,
            attack,
            defense,
            luck
        )
    )

    connection.commit()
    connection.close()


def get_inventory(player_id):
    connection = get_connection()

    items = connection.execute(
        """
        SELECT *
        FROM inventory
        WHERE player_id = ?
        ORDER BY id DESC
        """,
        (player_id,)
    ).fetchall()

    connection.close()

    return items


def format_inventory(player_id):
    items = get_inventory(player_id)

    if not items:
        return """
🎒 INVENTARIO

Está vacío.

Consigue objetos mediante:

💼 Trabajos
🕵️ Misiones
🎲 Eventos
⚔️ Combates
🎁 Cofres
"""

    text = "🎒 INVENTARIO\n\n"

    for item in items:

        rarity = RARITIES.get(
            item["rarity"],
            "⚪ Común"
        )

        text += (
            f"{rarity} {item['item_name']}\n"
            f"⚔️ +{item['attack']} "
            f"🛡️ +{item['defense']} "
            f"🍀 +{item['luck']}\n\n"
        )

    return text
