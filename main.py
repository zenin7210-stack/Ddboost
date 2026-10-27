import os
import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

CARDS = {
    "uzcard": os.getenv("UZCARD", "Karta hali qo'shilmagan"),
    "humo": os.getenv("HUMO", "Karta hali qo'shilmagan"),
    "visa": os.getenv("VISA", "Karta hali qo'shilmagan"),
}

RANKS = [
    "Kalibrovka",
    "Bronza",
    "Silver",
    "Gold",
    "Fenix",
    "Ranger",
    "Champion",
    "Master",
    "Elita",
    "The Legend",
]

# Har bir keyingi rankga o'tish narxi.
# Jami: Kalibrovka -> The Legend = 120 000 so'm.
PRICES = [
    3000,
    4000,
    6000,
    9000,
    13000,
    18000,
    25000,
    35000,
    7000,
]

MODES = {
    "nap": "Напарники",
    "sor": "Соревновательный",
    "duel": "Дуэль",
}


def keyboard(rows):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(text, callback_data=data)
         for text, data in row]
        for row in rows
    ])


def rank_keyboard(prefix, start=0):
    rows = []
    for i in range(start, len(RANKS)):
        rows.append([(RANKS[i], f"{prefix}:{i}")])
    return keyboard(rows)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()

    text = (
        "🔥 DD BOOST | STANDOFF 2\n\n"
        "Assalomu alaykum!\n"
        "Rank ko'tarish xizmatiga xush kelibsiz.\n\n"
        "🎮 O'yin rejimini tanlang:"
    )

    rows = [
        [("Напарники", "mode:nap")],
        [("Соревновательный", "mode:sor")],
        [("Дуэль", "mode:duel")],
    ]

    if update.message:
        await update.message.reply_text(
            text, reply_markup=keyboard(rows)
        )
    else:
        await update.callback_query.edit_message_text(
            text, reply_markup=keyboard(rows)
        )


async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    user = context.user_data

    if data.startswith("mode:"):
        mode = data.split(":")[1]
        user.clear()
        user["mode"] = mode

        await query.edit_message_text(
            f"🎮 Rejim: {MODES[mode]}\n\n"
            "Hozirgi rankingizni tanlang:",
            reply_markup=rank_keyboard("from")
        )

    elif data.startswith("from:"):
        current = int(data.split(":")[1])
        user["from"] = current

        if current == len(RANKS) - 1:
            await query.edit_message_text(
                "Siz allaqachon eng yuqori rankdasiz!",
                reply_markup=keyboard([
                    [("🔙 Bosh menyu", "home")]
                ])
            )
            return

        await query.edit_message_text(
            f"📍 Hozirgi rank: {RANKS[current]}\n\n"
            "Qaysi rankgacha ko'tarmoqchisiz?",
            reply_markup=rank_keyboard("to", current + 1)
        )

    elif data.startswith("to:"):
        target = int(data.split(":")[1])
        current = user.get("from")

        if current is None or target <= current:
            await query.edit_message_text(
                "Xatolik. /start ni bosing."
            )
            return

        user["to"] = target

        price = sum(PRICES[current:target])
        user["price"] = price

        mode = MODES[user["mode"]]

        text = (
            "🛒 DD BOOST | BUYURTMA\n\n"
            f"🎮 Rejim: {mode}\n"
            f"📍 Hozirgi rank: {RANKS[current]}\n"
            f"🏆 Kerakli rank: {RANKS[target]}\n\n"
            f"💰 Narx: {price:,} so'm\n\n"
            "To'lov turini tanlang:"
        )

        await query.edit_message_text(
            text,
            reply_markup=keyboard([
                [("💳 Uzcard", "pay:uzcard")],
                [("💳 Humo", "pay:humo")],
                [("💳 Visa", "pay:visa")],
                [("🔙 Bosh menyu", "home")],
            ])
        )

    elif data.startswith("pay:"):
        method = data.split(":")[1]

        if "price" not in user:
            await query.edit_message_text(
                "Buyurtma topilmadi. /start ni bosing."
            )
            return

        user["payment"] = method
        user["state"] = "receipt"

        await query.edit_message_text(
            "💳 TO'LOV\n\n"
            f"Karta turi: {method.upper()}\n"
            f"Karta: {CARDS[method]}\n\n"
            f"💰 Summa: {user['price']:,} so'm\n\n"
            "To'lov qilganingizdan keyin "
            "chek rasmini shu yerga yuboring.\n\n"
            "⚠️ To'lov admin tomonidan tekshiriladi."
        )

    elif data == "home":
        await start(update, context)


async def receipt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = context.user_data

    if user.get("state") != "receipt":
        await update.message.reply_text(
            "Buyurtma berish uchun /start ni bosing."
        )
        return

    if not update.message.photo:
        await update.message.reply_text(
            "Iltimos, chekni rasm shaklida yuboring."
        )
        return

    if not ADMIN_ID:
        await update.message.reply_text(
            "Admin hali sozlanmagan. "
            "Iltimos, keyinroq urinib ko'ring."
        )
        return

    telegram_user = update.effective_user

    username = (
        f"@{telegram_user.username}"
        if telegram_user.username
        else "Username yo'q"
    )

    caption = (
        "🔔 YANGI BUYURTMA | DD BOOST\n\n"
        f"👤 Mijoz: {username}\n"
        f"🆔 Telegram ID: {telegram_user.id}\n"
        f"🎮 Rejim: {MODES[user['mode']]}\n"
        f"📍 Rank: {RANKS[user['from']]}\n"
        f"🏆 Maqsad: {RANKS[user['to']]}\n"
        f"💰 Narx: {user['price']:,} so'm\n"
        f"💳 To'lov: {user['payment'].upper()}\n\n"
        "⚠️ To'lovni tekshiring."
    )

    try:
        await context.bot.send_photo(
            chat_id=ADMIN_ID,
            photo=update.message.photo[-1].file_id,
            caption=caption
        )
    except Exception:
        logging.exception("Admin xabarini yuborib bo'lmadi")
        await update.message.reply_text(
            "Buyurtmani yuborishda xatolik yuz berdi. "
            "Iltimos, qayta urinib ko'ring."
        )
        return

    user.clear()

    await update.message.reply_text(
        "✅ Buyurtmangiz adminga yuborildi!\n\n"
        "To'lov tekshirilgandan keyin "
        "admin siz bilan bog'lanadi.\n\n"
        "Yangi buyurtma: /start"
    )


def main():
    if not TOKEN:
        raise RuntimeError(
            "BOT_TOKEN muhit o'zgaruvchisi kiritilmagan!"
        )

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(buttons))
    app.add_handler(
        MessageHandler(
            filters.PHOTO | filters.TEXT,
            receipt
        )
    )

    print("DD BOOST ishga tushdi!")
    app.run_polling()


if __name__ == "__main__":
    main()
