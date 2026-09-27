import os
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

TOKEN = os.getenv("BOT_TOKEN")
DB = "data/game.db"


def get_db():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS players (
            id INTEGER PRIMARY KEY,
            username TEXT,
            money INTEGER DEFAULT 1000,
            xp INTEGER DEFAULT 0,
            level INTEGER DEFAULT 1,
            energy INTEGER DEFAULT 100,
            health INTEGER DEFAULT 100,
            fame INTEGER DEFAULT 0
        )
    """)

    conn.commit()
    conn.close()


def get_player(user):
    conn = get_db()

    player = conn.execute(
        "SELECT * FROM players WHERE id = ?",
        (user.id,)
    ).fetchone()

    if player is None:
        conn.execute("""
            INSERT INTO players
            (id, username)
            VALUES (?, ?)
        """, (
            user.id,
            user.username or user.first_name
        ))

        conn.commit()

        player = conn.execute(
            "SELECT * FROM players WHERE id = ?",
            (user.id,)
        ).fetchone()

    conn.close()
    return player


def menu():
    keyboard = [
        [
            InlineKeyboardButton("👤 PERFIL", callback_data="profile"),
            InlineKeyboardButton("💼 TRABAJAR", callback_data="work"),
        ],
        [
            InlineKeyboardButton("🎒 INVENTARIO", callback_data="inventory"),
            InlineKeyboardButton("⚔️ COMBATE", callback_data="combat"),
        ],
        [
            InlineKeyboardButton("🎁 REGALO", callback_data="daily"),
            InlineKeyboardButton("🏆 RANKING", callback_data="ranking"),
        ],
        [
            InlineKeyboardButton("🏴 CLANES", callback_data="clans"),
        ],
    ]

    return InlineKeyboardMarkup(keyboard)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    player = get_player(update.effective_user)

    await update.message.reply_text(
        f"""
🌆 LA CIUDAD 24/7

Bienvenido, {player['username']}.

⭐ Nivel: {player['level']}
💰 Dinero: {player['money']} 🪙
⭐ XP: {player['xp']}
⚡ Energía: {player['energy']}
❤️ Vida: {player['health']}
🔥 Fama: {player['fame']}

¿Qué quieres hacer?
""",
        reply_markup=menu()
    )


async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    player = get_player(query.from_user)

    if query.data == "profile":
        text = f"""
👤 PERFIL

👤 {player['username']}

⭐ Nivel: {player['level']}
⭐ XP: {player['xp']}

💰 Dinero: {player['money']} 🪙
⚡ Energía: {player['energy']}
❤️ Vida: {player['health']}
🔥 Fama: {player['fame']}
"""

    elif query.data == "work":
        if player["energy"] < 10:
            text = "⚡ No tienes suficiente energía."
        else:
            conn = get_db()

            conn.execute("""
                UPDATE players
                SET money = money + 100,
                    xp = xp + 25,
                    energy = energy - 10
                WHERE id = ?
            """, (query.from_user.id,))

            conn.commit()
            conn.close()

            text = """
💼 TRABAJO COMPLETADO

💰 +100 🪙
⭐ +25 XP
⚡ -10 energía
"""

    elif query.data == "inventory":
        text = """
🎒 INVENTARIO

🎒 Vacío

Próximamente podrás conseguir:

⚪ Común
🟢 Poco común
🔵 Raro
🟣 Épico
🟠 Legendario
🔴 Mítico
"""

    elif query.data == "combat":
        text = """
⚔️ COMBATE

Todavía no tienes enemigos.

Próximamente podrás enfrentarte a:

👤 Jugadores
👹 Jefes
🐺 Criaturas
🏴 Clanes
"""

    elif query.data == "daily":
        text = """
🎁 REGALO DIARIO

💰 +250 🪙
⭐ +50 XP

Sistema de rachas próximamente.
"""

        conn = get_db()

        conn.execute("""
            UPDATE players
            SET money = money + 250,
                xp = xp + 50
            WHERE id = ?
        """, (query.from_user.id,))

        conn.commit()
        conn.close()

    elif query.data == "ranking":
        conn = get_db()

        players = conn.execute("""
            SELECT username, level, xp, money
            FROM players
            ORDER BY level DESC, xp DESC
            LIMIT 10
        """).fetchall()

        conn.close()

        text = "🏆 RANKING\n\n"

        for i, p in enumerate(players, 1):
            text += (
                f"{i}️⃣ {p['username']} "
                f"⭐ {p['level']} "
                f"💰 {p['money']}\n"
            )

    elif query.data == "clans":
        text = """
🏴 CLANES

Sistema de clanes próximamente.

👥 Mínimo para fundar: 5
👥 Máximo inicial: 10
👥 Máximo final: 20

⚔️ Guerras: 10 vs 10
⚖️ Emparejamiento equilibrado
"""

    else:
        text = "❓ Acción desconocida."

    await query.edit_message_text(
        text,
        reply_markup=menu()
    )


def main():
    init_db()

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(buttons))

    print("🌆 LA CIUDAD 24/7 iniciada")

    app.run_polling()


if __name__ == "__main__":
    main()
