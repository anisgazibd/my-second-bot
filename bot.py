import telebot
import re

# এখানে BotFather থেকে পাওয়া আপনার নতুন বট টোকেন দিন
TOKEN = 'YOUR_BOT_TOKEN_HERE'
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        "👋 **স্বাগতম!**\n\n"
        "আমি পাবলিক ও প্রাইভেট সব ধরণের চ্যানেল এবং গ্রুপের নাম, ইউজারনেম ও আইডি বের করতে পারি।\n\n"
        "📌 **ব্যবহারের নিয়ম:**\n"
        "1️⃣ **প্রাইভেট পোস্ট লিংক:** `https://t.me/c/1234567890/10` (একসাথে একাধিক পাঠাতে পারেন)\n"
        "2️⃣ **পাবলিক ইউজারনেম/লিংক:** `@channel` বা `t.me/channel`\n"
        "3️⃣ **পোস্ট ফরওয়ার্ড:** যেকোনো চ্যানেল/গ্রুপ থেকে বার্তা ফরওয়ার্ড করুন।"
    )
    bot.reply_to(message, welcome_text, parse_mode='Markdown')

# ১. ফরওয়ার্ড করা মেসেজ প্রসেস করা
@bot.message_handler(func=lambda message: message.forward_from_chat is not None)
def handle_forwarded_messages(message):
    try:
        chat = message.forward_from_chat
        title = chat.title if chat.title else "অজ্ঞাত নাম"
        username = f"@{chat.username}" if chat.username else "❌ প্রাইভেট (No Username)"
        chat_id = chat.id

        response = (
            f"📌 **নাম:** {title}\n"
            f"🔗 **ইউজারনেম:** {username}\n"
            f"🆔 **আইডি:** `{chat_id}`"
        )
        bot.reply_to(message, response, parse_mode='Markdown')
    except Exception:
        bot.reply_to(message, "⚠️ মেসেজটি প্রসেস করতে সমস্যা হয়েছে।")

# ২. লিংক বা ইউজারনেম থেকে আইডি ও নাম বের করা
@bot.message_handler(func=lambda message: message.forward_from_chat is None, content_types=['text', 'photo', 'video', 'document', 'sticker'])
def handle_text_or_links(message):
    try:
        text = message.text or message.caption
        if not text:
            bot.reply_to(message, "⚠️ অনুগ্রহ করে সঠিক লিংক, ইউজারনেম বা পোস্ট ফরওয়ার্ড করুন।")
            return

        response_text = "✅ **খুঁজে পাওয়া চ্যানেল/গ্রুপের বিস্তারিত তথ্য:**\n\n"
        found = False

        # ক. প্রাইভেট পোস্ট লিংক প্রসেস করা (যেমন: t.me/c/1234567890/10)
        private_channel_ids = re.findall(r't\.me/c/(\d+)', text)
        for channel_num in set(private_channel_ids):
            full_id = int(f"-100{channel_num}")
            found = True
            
            try:
                # বট যদি চ্যানেলে যুক্ত থাকে তবে নাম টেনে আনবে
                chat = bot.get_chat(full_id)
                title = chat.title if chat.title else "অজ্ঞাত নাম"
                uname = f"@{chat.username}" if chat.username else "❌ প্রাইভেট (No Username)"
                response_text += f"📌 **নাম:** {title}\n🔗 **ইউজারনেম:** {uname}\n🆔 **আইডি:** `{chat.id}`\n\n"
            except Exception:
                # বট চ্যানেলে যুক্ত না থাকলে শুধু আইডি দেখাবে
                response_text += f"🔒 **প্রাইভেট চ্যানেল/গ্রুপ**\n📌 **নাম:** ❌ বট এই চ্যানেলে জয়েন নেই (তাই নাম গোপন রয়েছে)\n🆔 **আইডি:** `{full_id}`\n\n"

        # খ. পাবলিক ইউজারনেম ও লিংক প্রসেস করা
        words = text.split()
        for word in words:
            if 't.me/c/' in word:
                continue

            clean_username = None
            if word.startswith('@'):
                clean_username = word
            elif 't.me/' in word:
                parts = word.split('t.me/')[-1].split('/')
                if parts[0] and parts[0] != 'c':
                    clean_username = '@' + parts[0]

            if clean_username:
                try:
                    chat = bot.get_chat(clean_username)
                    uname = f"@{chat.username}" if chat.username else "নাই"
                    response_text += f"📌 **নাম:** {chat.title}\n🔗 **ইউজারনেম:** {uname}\n🆔 **আইডি:** `{chat.id}`\n\n"
                    found = True
                except Exception:
                    response_text += f"❌ `{clean_username}`: তথ্য পাওয়া যায়নি।\n\n"

        if not found:
            bot.reply_to(message, "⚠️ কোনো সঠিক পোস্ট লিংক বা ইউজারনেম পাওয়া যায়নি।")
        else:
            bot.reply_to(message, response_text, parse_mode='Markdown')

    except Exception:
        bot.reply_to(message, "⚠️ প্রসেস করার সময় সমস্যা হয়েছে, সঠিক লিংক দিন।")

print("বট সফলভাবে চালু হয়েছে...", flush=True)
bot.infinity_polling(timeout=10, long_polling_timeout=5)
