import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import re
import requests

# আপনার দেওয়া বটের টোকেন এবং গুগল শিটের ওয়েব অ্যাপ লিংক
TOKEN = '6905775685:AAFXrq64pmgYhL6Q-M2QNT_wTN-ynbLU5vI' 
WEB_APP_URL = 'https://script.google.com/macros/s/AKfycbwQ2mwI6-W15_NbfwaHwkAOvR7qcjm9hJGdCaZc90ppolYcmNEbBCtscsVOmaitb5NR/exec' 

bot = telebot.TeleBot(TOKEN)
temp_data = {}

# গুগল শিটে সেভ করার বাটন
def create_save_markup():
    markup = InlineKeyboardMarkup()
    btn_yes = InlineKeyboardButton("✅ শিটে সেভ করুন", callback_data="save_yes")
    btn_no = InlineKeyboardButton("❌ বাতিল", callback_data="save_no")
    markup.add(btn_yes, btn_no)
    return markup

# ১. আকর্ষণীয় ওয়েলকাম মেসেজ
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_msg = (
        "🤖 **অ্যাডভান্সড টেলিগ্রাম আইডি এক্সট্রাক্টর বটে আপনাকে স্বাগতম!**\n\n"
        "আমি খুব সহজেই যেকোনো টেলিগ্রাম চ্যানেল বা গ্রুপের নাম, ইউজারনেম এবং আইডি বের করে দিতে পারি। এরপর আপনি চাইলে সেই তথ্য সরাসরি আপনার **Google Sheet**-এ সেভ করতে পারবেন।\n\n"
        "📌 **যেভাবে ব্যবহার করবেন:**\n"
        "🔸 **লিংক দিন:** যেকোনো পাবলিক বা প্রাইভেট পোস্টের লিংক দিন।\n"
        "   👉 *যেমন: `t.me/c/123456789/10` বা `t.me/username/10`*\n"
        "🔸 **ইউজারনেম দিন:** যেকোনো চ্যানেলের ইউজারনেম লিখে পাঠান।\n"
        "   👉 *যেমন: `@yourchannel`*\n"
        "🔸 **ফরওয়ার্ড করুন:** যেকোনো চ্যানেল থেকে একটি মেসেজ বটের কাছে ফরওয়ার্ড করুন।\n\n"
        "💡 *যেকোনো তথ্য পাঠানোর পর আমি আপনাকে একটি বাটন দেবো, সেখানে ক্লিক করলেই ডেটা সেভ হয়ে যাবে!*"
    )
    bot.reply_to(message, welcome_msg, parse_mode='Markdown')

# ২. ফরওয়ার্ড করা মেসেজ হ্যান্ডেলার
@bot.message_handler(func=lambda message: message.forward_from_chat is not None)
def handle_forwarded_messages(message):
    processing_msg = bot.reply_to(message, "⏳ *তথ্য খোঁজা হচ্ছে...*", parse_mode='Markdown')
    
    try:
        chat = message.forward_from_chat
        title = chat.title if chat.title else "অজ্ঞাত নাম"
        username = f"@{chat.username}" if chat.username else "🔒 প্রাইভেট (No Username)"
        chat_id = chat.id

        response = f"✅ **সফলভাবে তথ্য পাওয়া গেছে!**\n\n📌 **নাম:** {title}\n🔗 **ইউজারনেম:** {username}\n🆔 **আইডি:** `{chat_id}`\n\n👇 *গুগল শিটে সেভ করতে নিচের বাটনে ক্লিক করুন:*"
        
        # প্রসেসিং মেসেজ এডিট করে রেজাল্ট বসানো
        bot.edit_message_text(response, chat_id=message.chat.id, message_id=processing_msg.message_id, parse_mode='Markdown', reply_markup=create_save_markup())
        
        temp_data[processing_msg.message_id] = {"title": title, "username": username, "chat_id": str(chat_id)}
    except Exception:
        bot.edit_message_text("⚠️ **দুঃখিত!** মেসেজটি থেকে তথ্য বের করা সম্ভব হয়নি।", chat_id=message.chat.id, message_id=processing_msg.message_id, parse_mode='Markdown')

# ৩. লিংক বা ইউজারনেম থেকে ডেটা বের করার হ্যান্ডেলার
@bot.message_handler(func=lambda message: message.forward_from_chat is None, content_types=['text', 'photo', 'video'])
def handle_text_or_links(message):
    text = message.text or message.caption
    if not text:
        return

    # প্রাইভেট এবং পাবলিক লিংক খোঁজার জন্য অ্যাডভান্সড রেগুলার এক্সপ্রেশন
    private_ids = re.findall(r't\.me/c/(\d+)', text)
    public_usernames = re.findall(r't\.me/(?!c/|joinchat/)([a-zA-Z0-9_]+)', text)
    mentions = re.findall(r'@([a-zA-Z0-9_]+)', text)
    
    # সব ইউজারনেম একসাথে করা
    all_public_targets = set(public_usernames + mentions)

    if not private_ids and not all_public_targets:
        if message.text.startswith('/'): return
        bot.reply_to(message, "⚠️ **কোনো সঠিক লিংক বা ইউজারনেম পাওয়া যায়নি!**\nঅনুগ্রহ করে একটি সঠিক টেলিগ্রাম লিংক বা মেসেজ ফরওয়ার্ড করুন।", parse_mode='Markdown')
        return

    processing_msg = bot.reply_to(message, "⏳ *লিংক স্ক্যান করা হচ্ছে...*", parse_mode='Markdown')
    found_any = False

    # ক. প্রাইভেট লিংকের কাজ
    for channel_num in set(private_ids):
        full_id = int(f"-100{channel_num}")
        try:
            chat = bot.get_chat(full_id)
            title = chat.title if chat.title else "অজ্ঞাত নাম"
            uname = f"@{chat.username}" if chat.username else "🔒 প্রাইভেট"
        except Exception:
            title = "🔒 প্রাইভেট চ্যানেল (বট জয়েন নেই)"
            uname = "নাই"
        
        response = f"✅ **তথ্য পাওয়া গেছে!**\n\n📌 **নাম:** {title}\n🔗 **ইউজারনেম:** {uname}\n🆔 **আইডি:** `{full_id}`"
        bot.edit_message_text(response, chat_id=message.chat.id, message_id=processing_msg.message_id, parse_mode='Markdown', reply_markup=create_save_markup())
        temp_data[processing_msg.message_id] = {"title": title, "username": uname, "chat_id": str(full_id)}
        found_any = True
        break # একসাথে একটি লিংকের জন্য কাজ করবে

    # খ. পাবলিক লিংক বা ইউজারনেমের কাজ
    if not found_any:
        for uname in all_public_targets:
            try:
                chat = bot.get_chat(f"@{uname}")
                title = chat.title if chat.title else "অজ্ঞাত নাম"
                real_uname = f"@{chat.username}" if chat.username else f"@{uname}"
                
                response = f"✅ **তথ্য পাওয়া গেছে!**\n\n📌 **নাম:** {title}\n🔗 **ইউজারনেম:** {real_uname}\n🆔 **আইডি:** `{chat.id}`"
                bot.edit_message_text(response, chat_id=message.chat.id, message_id=processing_msg.message_id, parse_mode='Markdown', reply_markup=create_save_markup())
                temp_data[processing_msg.message_id] = {"title": title, "username": real_uname, "chat_id": str(chat.id)}
                found_any = True
                break
            except Exception:
                continue

    if not found_any:
        bot.edit_message_text("⚠️ **তথ্য পাওয়া যায়নি!**\nহয়তো চ্যানেলটি ডিলিট হয়ে গেছে অথবা ইউজারনেমটি ভুল।", chat_id=message.chat.id, message_id=processing_msg.message_id, parse_mode='Markdown')

# ৪. বাটন ক্লিকের অ্যাকশন (গুগল শিটে ডেটা পাঠানো)
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    msg_id = call.message.message_id
    
    if call.data == "save_yes":
        if msg_id in temp_data:
            data = temp_data[msg_id]
            try:
                bot.edit_message_reply_markup(call.message.chat.id, msg_id, reply_markup=None)
                # গুগল শিটে রিকোয়েস্ট পাঠানো
                requests.post(WEB_APP_URL, json=data)
                
                bot.answer_callback_query(call.id, "✅ গুগল শিটে সেভ হয়েছে!")
                bot.send_message(call.message.chat.id, f"✔️ **সফলভাবে গুগল শিটে সেভ হয়েছে!**\n(নাম: {data['title']})", reply_to_message_id=msg_id, parse_mode='Markdown')
                del temp_data[msg_id]
            except Exception:
                bot.answer_callback_query(call.id, "⚠️ শিটে সেভ হতে সমস্যা হয়েছে!", show_alert=True)
        else:
            bot.answer_callback_query(call.id, "⚠️ ডেটা এক্সপায়ার হয়ে গেছে! আবার লিংক দিন।", show_alert=True)

    elif call.data == "save_no":
        bot.answer_callback_query(call.id, "❌ বাতিল করা হয়েছে।")
        bot.edit_message_reply_markup(call.message.chat.id, msg_id, reply_markup=None)
        if msg_id in temp_data:
            del temp_data[msg_id]

print("বটটি রকেটের গতিতে চালু হয়েছে! 🚀", flush=True)
bot.infinity_polling(timeout=10, long_polling_timeout=5)
