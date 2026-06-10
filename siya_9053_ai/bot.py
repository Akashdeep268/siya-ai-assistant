import logging
import json
import asyncio
import random
import os
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from openai import OpenAI
try:
    from sentence_transformers import SentenceTransformer
    import faiss
    import numpy as np

    model = SentenceTransformer("all-MiniLM-L6-v2")
    VECTOR_MEMORY_ENABLED = True
except Exception as exc:
    SentenceTransformer = None
    faiss = None
    np = None
    model = None
    VECTOR_MEMORY_ENABLED = False
    logging.warning("Vector memory disabled: %s", exc)

# memory store
vector_memory = []
vector_texts = []



def system_control(command):
    cmd = command.lower()

    if "chrome" in cmd:
        os.system("open -a 'Google Chrome'")
        return "chrome khol diya"

    elif "youtube" in cmd:
        os.system("open https://youtube.com")
        return "youtube khol diya"

    elif "shutdown" in cmd:
        os.system("shutdown -h now")
        return "system band kar raha hu"

    return None

def add_to_vector_memory(text):
    if not VECTOR_MEMORY_ENABLED:
        return

    embedding = model.encode([text])
    vector_memory.append(embedding[0])
    vector_texts.append(text)


def search_vector_memory(query):
    if not VECTOR_MEMORY_ENABLED or not vector_memory:
        return []

    query_vec = model.encode([query])[0]

    vectors = np.array(vector_memory).astype("float32")
    index = faiss.IndexFlatL2(len(query_vec))
    index.add(vectors)

    D, I = index.search(np.array([query_vec]).astype("float32"), k=3)

    results = []
    for i in I[0]:
        if i < len(vector_texts):
            results.append(vector_texts[i])

    return results


# 🔑 KEYS
GROQ_API_KEY = "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"
BOT_TOKEN = "8519425195:AAG1sRCQOQ8STYbhbes8MMn9my09sG0RExo"

client = OpenAI(
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1"
)

# 🧠 MEMORY


def load_memory():
    try:
        with open("memory.json", "r") as f:
            return json.load(f)
    except:
        return {}


def save_memory(data):
    with open("memory.json", "w") as f:
        json.dump(data, f, indent=2)

# 😏 MOOD


def detect_mood(msg):
    msg = msg.lower()
    if any(w in msg for w in ["miss", "sad", "alone", "yaad"]):
        return "caring"
    elif "sorry" in msg:
        return "soft"
    elif any(w in msg for w in ["kyu", "kyun", "kya"]):
        return "attitude"
    return "normal"

# 🌍 LANGUAGE


def detect_language(text):
    text = text.lower()
    if any(w in text for w in ["ki haal", "kida", "kar reha"]):
        return "punjabi"
    elif any(w in text for w in ["ke kar rha", "thare", "se"]):
        return "haryanvi"
    elif any(w in text for w in ["janab", "aap"]):
        return "urdu"
    return "hinglish"
# 🧠 LONG MEMORY EXTRACT


def extract_memory(user_message):
    keywords = ["mera", "mujhe", "pasand", "name", "love", "like"]

    if any(word in user_message.lower() for word in keywords):
        return user_message
    return None


# 📚 KNOWLEDGE SEARCH
def search_knowledge(query):
    try:
        with open("knowledge.json", "r") as f:
            data = json.load(f)

        for key in data:
            if key in query.lower():
                return data[key]
    except:
        return None


# 🧠 LEARNING STORE
def learn_from_chat(user_message, reply):
    with open("learning.txt", "a") as f:
        f.write(f"User: {user_message}\nAI: {reply}\n\n")
# ❤️ INTEREST SYSTEM


def update_interest(user_data, msg):
    if "interest" not in user_data:
        user_data["interest"] = 50

    msg = msg.lower()

    if any(w in msg for w in ["ignore", "late", "reply nahi"]):
        user_data["interest"] -= 5
    elif any(w in msg for w in ["acha", "hmm", "ok"]):
        user_data["interest"] -= 1
    else:
        user_data["interest"] += 2

    user_data["interest"] = max(0, min(100, user_data["interest"]))

# ⏱ HUMAN DELAY


async def human_delay(user_data):
    interest = user_data.get("interest", 50)

    if interest > 70:
        delay = random.uniform(0.5, 2)
    elif interest > 40:
        delay = random.uniform(2, 6)
    else:
        delay = random.uniform(5, 12)

    await asyncio.sleep(delay)

# 👀 IGNORE SYSTEM


def should_ignore(user_data):
    interest = user_data.get("interest", 50)

    if interest < 30:
        return random.random() < 0.4
    return False

# 🧠 LEARNING


def update_profile(profile, user_msg):
    msg = user_msg.lower()

    if "simple bol" in msg:
        profile["style"] = "very simple hinglish"
    if "short bol" in msg:
        profile["style"] = "very short replies"

    return profile

# 💖 PERSONALITY


def get_personality(mood, profile, lang):
    return f"""
You are Siya, a real girl chatting naturally.
You remember user details.
You respond practically and emotionally.
Language: {lang}
Reply in {lang} (roman only)
Style: {profile.get('style')}

Rules:
- Reply only to last message
- Stay on topic
- No random lines
- Short replies

Mood: {mood}
"""

# 💬 MULTI MESSAGE


async def send_realistic_messages(context, chat_id, messages):
    for msg in messages:
        await asyncio.sleep(random.uniform(0.5, 2))
        await context.bot.send_message(chat_id=chat_id, text=msg)


def split_reply(reply, mood):
    if mood == "attitude":
        return [reply[:len(reply)//2], reply[len(reply)//2:]]
    elif mood == "caring":
        return [reply]
    elif mood == "angry":
        return [reply[i:i+15] for i in range(0, len(reply), 15)]
    else:
        return [reply]

# 🤖 AUTO MESSAGE


async def auto_message(context):
    memory = load_memory()

    for user_id in memory:
        if random.random() < 0.08:
            msgs = [
                "kya kar raha hai",
                "so gaya kya",
                "reply hi nahi karta",
                "acha ignore kar raha hai?",
                "hmm theek hai"
            ]

            await context.bot.send_message(
                chat_id=user_id,
                text=random.choice(msgs)
            )

# ⚙️ LOGGING
logging.basicConfig(level=logging.INFO)

# 🚀 MAIN


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
   
    if not update.message or not update.message.text:
        return

    if update.message.from_user.is_bot:
        return

    user_message = update.message.text.strip()
    control = system_control(user_message)
    if control:
        await update.message.reply_text(control)
        return
    if "time" in user_message.lower() or "kitna baj" in user_message.lower():
        now = datetime.now().strftime("%I:%M %p")
        await update.message.reply_text(f"abhi {now} ho raha hai")
        return
    if "date" in user_message.lower():
        today = datetime.now().strftime("%d %B %Y")
        await update.message.reply_text(f"aaj {today} hai")
        return
    # greeting
    if user_message.lower() in ["hi", "hlo", "hello"]:
        await update.message.reply_text("haan bol na")
        return

    user_id = str(update.message.chat_id)
    memory = load_memory()

    if user_id not in memory:
        memory[user_id] = {
            "history": [],
            "mood": "normal",
            "profile": {"style": "short hinglish"},
            "interest": 50
        }

    user_data = memory[user_id]

    # ensure interest
    if "interest" not in user_data:
        user_data["interest"] = 50
    # ✅ long memory
    if "long_memory" not in user_data:
        user_data["long_memory"] = []

    update_interest(user_data, user_message)

    # ensure profile
    if "profile" not in user_data:
        user_data["profile"] = {"style": "short hinglish"}

    # detect
    user_data["mood"] = detect_mood(user_message)

    if should_ignore(user_data):
        return

    lang = detect_language(user_message)

    # learn
    user_data["profile"] = update_profile(user_data["profile"], user_message)
    knowledge = search_knowledge(user_message)

    # 🧠 messages start
    messages = [
        {
            "role": "system",
            "content": get_personality(user_data["mood"], user_data["profile"], lang)
        }
    ]

    if knowledge:
        messages.insert(0, {
            "role": "system",
            "content": f"Useful info: {knowledge}"
        })

    # 🧠 vector memory recall
    related_memories = search_vector_memory(user_message)

    for mem in related_memories:
        messages.append({
            "role": "system",
            "content": f"Related memory: {mem}"
        })

    # 🧠 long memory
    if "long_memory" in user_data:
        for m in user_data["long_memory"][-5:]:
            messages.append({
                "role": "system",
                "content": f"User info: {m}"
            })

    # 🧠 chat history
    for msg in user_data["history"][-10:]:
        messages.append(msg)

    # 👤 current message
    messages.append({
        "role": "user",
        "content": user_message
    })

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=messages
        )

        reply = response.choices[0].message.content.strip()

        if any(word in reply.lower() for word in ["sooraj", "khubsurat", "chand"]):
            reply = "acha seedha bol kya kehna hai"

        if not reply:
            reply = "hmm bol na"

        # save memory
        user_data["history"].append({"role": "user", "content": user_message})
        user_data["history"].append({"role": "assistant", "content": reply})

        # 🧠 long memory
        mem = extract_memory(user_message)

        if mem:
            if "long_memory" not in user_data:
                user_data["long_memory"] = []

            user_data["long_memory"].append(mem)

        # 💾 save file
        save_memory(memory)

        # 🧠 learning
        learn_from_chat(user_message, reply)

        # 🧠 vector memory
        add_to_vector_memory(user_message)
    except Exception as e:
        reply = f"Error: {str(e)}"
        print("ERROR:", e)
     # 🔥 SEND REPLY (THIS WAS MISSING)
    await human_delay(user_data)
    msgs = split_reply(reply, user_data["mood"])
    await send_realistic_messages(context, update.message.chat_id, msgs)
# 🤖 START
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(MessageHandler(
    filters.TEXT & ~filters.COMMAND, handle_message))

# 🔥 AUTO MESSAGE
if app.job_queue:
    app.job_queue.run_repeating(auto_message, interval=60, first=10)
else:
    logging.warning("Job queue unavailable; auto_message disabled.")

print("🔥 Siya AI running...")
app.run_polling()
