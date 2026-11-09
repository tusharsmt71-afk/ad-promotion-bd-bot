main.py
import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# =========================
# BOT SETTINGS
# =========================

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
CHANNEL = os.getenv("CHANNEL_USERNAME", "@AdPromotionBD")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# =========================
# START COMMAND
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📢 বিজ্ঞাপন জমা দিন", callback_data="submit")]
    ]

    await update.message.reply_text(
        "🎉 স্বাগতম Ad Promotion BD-তে!\n\n"
        "এখানে আপনি আপনার ব্যবসা বা প্রতিষ্ঠানের বিজ্ঞাপন "
        "প্রচার করতে পারবেন।\n\n"
        "বিজ্ঞাপন জমা দিতে নিচের বাটনে ক্লিক করুন।",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================
# SUBMIT AD
# =========================

async def submit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    context.user_data["awaiting_ad"] = True

    await query.message.reply_text(
        "📢 আপনার বিজ্ঞাপনটি এখন পাঠান।\n\n"
        "আপনি ছবি, লেখা অথবা ছবিসহ বিজ্ঞাপন পাঠাতে পারবেন।\n\n"
        "বাতিল করতে /cancel লিখুন।"
    )


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["awaiting_ad"] = False
    await update.message.reply_text("❌ বিজ্ঞাপন জমা বাতিল করা হয়েছে।")


# =========================
# RECEIVE AD
# =========================

async def receive_ad(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("awaiting_ad"):
        return

    if ADMIN_ID == 0:
        await update.message.reply_text(
            "⚠️ বটের অ্যাডমিন সেটিংস এখনো সম্পূর্ণ হয়নি।"
        )
        return

    user = update.effective_user
    message = update.message

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "✅ Approve",
                callback_data=f"approve|{message.chat_id}|{message.message_id}"
            ),
            InlineKeyboardButton(
                "❌ Reject",
                callback_data=f"reject|{message.chat_id}|{message.message_id}"
            )
        ]
    ])

    try:
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=(
                "📢 নতুন বিজ্ঞাপন জমা পড়েছে!\n\n"
                f"👤 নাম: {user.full_name}\n"
                f"🆔 User ID: {user.id}\n"
                f"📛 Username: @{user.username or 'নেই'}\n\n"
                "নিচের বিজ্ঞাপনটি যাচাই করে সিদ্ধান্ত নিন।"
            )
        )

        await context.bot.copy_message(
            chat_id=ADMIN_ID,
            from_chat_id=message.chat_id,
            message_id=message.message_id,
            reply_markup=keyboard
        )

        context.user_data["awaiting_ad"] = False

        await message.reply_text(
            "✅ আপনার বিজ্ঞাপন সফলভাবে জমা হয়েছে!\n\n"
            "অ্যাডমিন যাচাই করার পর বিজ্ঞাপন প্রকাশ করা হবে।"
        )

    except Exception:
        logging.exception("Ad submission failed")
        await message.reply_text(
            "⚠️ বিজ্ঞাপন জমা দিতে সমস্যা হয়েছে। পরে আবার চেষ্টা করুন।"
        )


# =========================
# ADMIN APPROVAL
# =========================

async def admin_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    if query.from_user.id != ADMIN_ID:
        await query.answer("আপনার অনুমতি নেই!", show_alert=True)
        return

    await query.answer()

    try:
        action, chat_id, message_id = query.data.split("|")
        chat_id = int(chat_id)
        message_id = int(message_id)

        if action == "approve":
            await context.bot.copy_message(
                chat_id=CHANNEL,
                from_chat_id=chat_id,
                message_id=message_id
            )

            await context.bot.send_message(
                chat_id=chat_id,
                text="🎉 অভিনন্দন! আপনার বিজ্ঞাপন অনুমোদিত হয়েছে।"
            )

            await query.edit_message_reply_markup(reply_markup=None)
            await query.message.reply_text("✅ বিজ্ঞাপন চ্যানেলে প্রকাশিত হয়েছে!")

        elif action == "reject":
            await context.bot.send_message(
                chat_id=chat_id,
                text="❌ দুঃখিত! আপনার বিজ্ঞাপনটি অনুমোদিত হয়নি।"
            )

            await query.edit_message_reply_markup(reply_markup=None)
            await query.message.reply_text("❌ বিজ্ঞাপন বাতিল করা হয়েছে।")

    except Exception:
        logging.exception("Admin action failed")
        await query.message.reply_text(
            "⚠️ কাজটি সম্পন্ন করা যায়নি। সেটিংস পরীক্ষা করুন।"
        )


# =========================
# MAIN FUNCTION
# =========================

def main():
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN সেট করা হয়নি!")

    if ADMIN_ID == 0:
        raise ValueError("ADMIN_ID সেট করা হয়নি!")

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("cancel", cancel))
    app.add_handler(CallbackQueryHandler(submit, pattern="^submit$"))
    app.add_handler(
        CallbackQueryHandler(admin_action, pattern="^(approve|reject)\\|")
    )
    app.add_handler(
        MessageHandler(
            (filters.TEXT | filters.PHOTO) & ~filters.COMMAND,
            receive_ad
        )
    )

    print("Ad Promotion BD Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
