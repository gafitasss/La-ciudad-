0import os

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

from database import (
    init_database,
    get_player,
    create_player,
    update_player,
)


from systems.inventory import (
    init_inventory,
    format_inventory,
    add_item,
    get_inventory,
)

TOKEN = os.getenv("BOT_TOKEN")


def main_menu():
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


def ensure_player(user):
    player = get_player(user.id)

    if player is None:
        create_player(
            user.id,
            user.username or user.first_name
        )

        player = get_player(user.id)

    return player


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    player = ensure_player(update.effective_user)
if not get_inventory(update.effective_user.id):

    add_item(
        update.effective_user.id,
        "🔧 Herramienta oxidada",
        "common",
        attack=2,
        defense=1,
        luck=1
    )
    await update.message.reply_text(
        f"""
🌆 LA CIUDAD 24/7

Bienvenido, {player['username']}.

⭐ Nivel: {player['level']}
⭐ XP: {player['xp']}

💰 Dinero: {player['money']} 🪙
⚡ Energía: {player['energy']}
❤️ Vida: {player['health']}
🔥 Fama: {player['fame']}

¿Qué quieres hacer?
""",
        reply_markup=main_menu()
    )


async def buttons(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query

    await query.answer()

    player = ensure_player(query.from_user)

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

            text = """
⚡ SIN ENERGÍA

Necesitas al menos 10 de energía
para trabajar.
"""

        else:

            update_player(
                query.from_user.id,
                money=player["money"] + 100,
                xp=player["xp"] + 25,
                energy=player["energy"] - 10
            )

            text = """
💼 TRABAJO COMPLETADO

Has trabajado en la ciudad.

💰 +100 🪙
⭐ +25 XP
⚡ -10 energía
"""

    elif query.data == "inventory":

    items = get_inventory(
        query.from_user.id
    )

    if not items:
        add_item(
            query.from_user.id,
            "🔧 Herramienta oxidada",
            "common",
            attack=2,
            defense=1,
            luck=1
        )

    text = format_inventory(
        query.from_user.id
    )

    elif query.data == "combat":

        text = """
⚔️ COMBATE

Todavía estás empezando.

Próximamente podrás luchar contra:

👤 Jugadores
👹 Jefes
🐺 Criaturas
🏴 Clanes
"""

    elif query.data == "daily":

        update_player(
            query.from_user.id,
            money=player["money"] + 250,
            xp=player["xp"] + 50
        )

        text = """
🎁 REGALO DIARIO

💰 +250 🪙
⭐ +50 XP

🔥 Próximamente tendremos
rachas diarias.
"""

    elif query.data == "ranking":

        from database import get_connection

        connection = get_connection()

        players = connection.execute(
            """
            SELECT username, level, xp, money
            FROM players
            ORDER BY level DESC, xp DESC
            LIMIT 10
            """
        ).fetchall()

        connection.close()

        text = "🏆 RANKING\n\n"

        if not players:

            text += "Todavía no hay jugadores."

        else:

            for position, p in enumerate(players, 1):

                text += (
                    f"{position}️⃣ "
                    f"{p['username']} "
                    f"⭐ {p['level']} "
                    f"💰 {p['money']} 🪙\n"
                )

    elif query.data == "clans":

        text = """
🏴 CLANES

El sistema de clanes está
en construcción.

👥 Mínimo para fundar: 5
👥 Máximo inicial: 10
👥 Máximo final: 20

⚔️ Guerra: 10 vs 10
⚖️ Emparejamiento equilibrado
⏱️ Preparación: 24 horas
"""

    else:

        text = "❓ Acción desconocida."

    await query.edit_message_text(
        text,
        reply_markup=main_menu()
    )


def main():

    if not TOKEN:
        raise RuntimeError(
            "BOT_TOKEN no está configurado."
        )

init_database()
init_inventory()

    application = (
        Application.builder()
        .token(TOKEN)
        .build()
    )

    application.add_handler(
        CommandHandler("start", start)
    )

    application.add_handler(
        CallbackQueryHandler(buttons)
    )

    print("🌆 LA CIUDAD 24/7 iniciada")

    application.run_polling()


if __name__ == "__main__":
    main()
