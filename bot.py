import os
from datetime import datetime, timedelta

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
            user.username or user.first_name or "Jugador"
        )
        player = get_player(user.id)

    return player


def calculate_level(xp):
    return max(1, (xp // 100) + 1)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    player = ensure_player(user)

    # Regalo inicial
    if not get_inventory(user.id):
        add_item(
            user.id,
            "🔧 Herramienta oxidada",
            "common",
            attack=2,
            defense=1,
            luck=1
        )

    text = f"""
🌆 LA CIUDAD 24/7

Bienvenido, {player['username']}.

⭐ Nivel: {player['level']}
⭐ XP: {player['xp']}

💰 Dinero: {player['money']} 🪙
⚡ Energía: {player['energy']}
❤️ Vida: {player['health']}
🔥 Fama: {player['fame']}

¿Qué quieres hacer?
"""

    await update.message.reply_text(
        text,
        reply_markup=main_menu()
    )


async def buttons(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query
    await query.answer()

    player = ensure_player(query.from_user)
    user_id = query.from_user.id

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

⚔️ Ataque: {player['attack']}
🛡️ Defensa: {player['defense']}
🍀 Suerte: {player['luck']}
"""

    elif query.data == "work":

        now = datetime.utcnow()

        last_work = player["last_work"]

        if last_work:
            try:
                last_time = datetime.fromisoformat(last_work)
                elapsed = now - last_time

                if elapsed < timedelta(minutes=5):
                    remaining = 5 - int(elapsed.total_seconds() // 60)

                    text = f"""
⏳ TRABAJO

Todavía estás descansando.

Vuelve dentro de aproximadamente
{remaining} minuto(s).
"""
                    await query.edit_message_text(
                        text,
                        reply_markup=main_menu()
                    )
                    return

            except ValueError:
                pass

        if player["energy"] < 10:

            text = """
⚡ SIN ENERGÍA

Necesitas al menos 10 de energía
para trabajar.
"""

        else:

            new_money = player["money"] + 100
            new_xp = player["xp"] + 25
            new_energy = player["energy"] - 10
            new_level = calculate_level(new_xp)

            update_player(
                user_id,
                money=new_money,
                xp=new_xp,
                energy=new_energy,
                level=new_level,
                last_work=now.isoformat()
            )

            level_message = ""

            if new_level > player["level"]:
                level_message = f"""

🎉 ¡HAS SUBIDO AL NIVEL {new_level}!
"""

            text = f"""
💼 TRABAJO COMPLETADO

Has trabajado en la ciudad.

💰 +100 🪙
⭐ +25 XP
⚡ -10 energía
{level_message}
"""

    elif query.data == "inventory":

        text = format_inventory(user_id)

    elif query.data == "combat":

        text = """
⚔️ COMBATE

La arena todavía está preparándose.

Próximamente:

👤 Jugadores
👹 Jefes
🐺 Criaturas
🏴 Clanes

⚔️ El sistema de combate será
uno de los grandes sistemas de
LA CIUDAD 24/7.
"""

    elif query.data == "daily":

        now = datetime.utcnow()
        last_daily = player["last_daily"]

        if last_daily:
            try:
                last_time = datetime.fromisoformat(last_daily)
                elapsed = now - last_time

                if elapsed < timedelta(hours=24):

                    remaining = timedelta(hours=24) - elapsed
                    hours = int(
                        remaining.total_seconds() // 3600
                    )
                    minutes = int(
                        (remaining.total_seconds() % 3600) // 60
                    )

                    text = f"""
🎁 REGALO DIARIO

Ya has recogido tu regalo.

⏳ Próximo regalo:
{hours}h {minutes}min
"""

                    await query.edit_message_text(
                        text,
                        reply_markup=main_menu()
                    )
                    return

            except ValueError:
                pass

        new_money = player["money"] + 250
        new_xp = player["xp"] + 50
        new_level = calculate_level(new_xp)

        update_player(
            user_id,
            money=new_money,
            xp=new_xp,
            level=new_level,
            last_daily=now.isoformat()
        )

        text = f"""
🎁 REGALO DIARIO

💰 +250 🪙
⭐ +50 XP

🔥 ¡Vuelve mañana!

Tu racha diaria será ampliada
en una próxima actualización.
"""

    elif query.data == "ranking":

        from database import get_connection

        connection = get_connection()

        players = connection.execute(
            """
            SELECT username, level, xp, money
            FROM players
            ORDER BY level DESC, xp DESC, money DESC
            LIMIT 10
            """
        ).fetchall()

        connection.close()

        text = "🏆 RANKING\n\n"

        if not players:
            text += "Todavía no hay jugadores."

        else:
            for position, p in enumerate(players, 1):

                username = p["username"] or "Jugador"

                text += (
                    f"{position}️⃣ "
                    f"{username} "
                    f"⭐ {p['level']} "
                    f"💰 {p['money']} 🪙\n"
                )

    elif query.data == "clans":

        text = """
🏴 CLANES

El sistema de clanes está
en construcción.

👥 Mínimo para fundar: 5
👥 Máximo final: 20

⚔️ Guerra: 10 vs 10
⚖️ Emparejamiento equilibrado
⏱️ Preparación: 24 horas

Próximamente podrás crear
tu propio clan.
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
