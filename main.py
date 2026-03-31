import asyncio
import re

# Костыль для Python 3.14
try:
    asyncio.get_event_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())

from pyrogram import Client, filters

# Твои данные
API_ID = 25186383
API_HASH = "ea2bbc60e23bdd24d1e137021795746f"
SOURCE_CHAT = "turktrendkatalog_obuv"
TARGET_CHAT = "turkshop_2026"

app = Client("my_session", api_id=API_ID, api_hash=API_HASH)

def update_price(text):
    if not text: return text
    # Ищем цену перед $$ (учитываем точки и пробелы)
    pattern = r"(\d+[\s\.]?\d*)\s*\$\$"
    def replacement(match):
        try:
            clean_num = match.group(1).replace(" ", "")
            new_price = float(clean_num) + 2.0
            return f"{new_price:g} $$"
        except:
            return match.group(0)
    return re.sub(pattern, replacement, text)

@app.on_message(filters.chat(SOURCE_CHAT))
async def forward_logic(client, message):
    text = message.text or message.caption
    new_text = update_price(text) if text else text
    try:
        if message.photo:
            await client.send_photo(TARGET_CHAT, message.photo.file_id, caption=new_text)
        elif message.video:
            await client.send_video(TARGET_CHAT, message.video.file_id, caption=new_text)
        else:
            await client.send_message(TARGET_CHAT, new_text)
    except Exception as e:
        print(f"Ошибка пересылки: {e}")

async def run_bot():
    print("Бот запущен и мониторит канал...")
    await app.start()
    # Держим бота запущенным
    from pyrogram import idle
    await idle()
    await app.stop()

if __name__ == "__main__":
    asyncio.run(run_bot())
