import asyncio
import re
from pyrogram import Client, filters

# Костыль для работы на Python 3.14
try:
    asyncio.get_event_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())

API_ID = 25186383
API_HASH = "ea2bbc60e23bdd24d1e137021795746f"
SOURCE_CHAT = "turktrendkatalog_obuv"
TARGET_CHAT = "turkshop_2026"

app = Client("my_session", api_id=API_ID, api_hash=API_HASH)

def update_price(text):
    if not text: return text
    # Ищем цену перед $$ (учитываем точки и пробелы: 18.5$$, 15 .5 $$, 35 $$)
    pattern = r"(\d+[\s\.]?\d*)\s*\$\$"
    
    def replacement(match):
        try:
            clean_num = match.group(1).replace(" ", "")
            new_price = float(clean_num) + 2.0
            # Форматируем: если число целое (20.0), пишем 20, если дробное (20.5) — 20.5
            return f"{new_price:g} $$"
        except:
            return match.group(0) # Если ошибка, возвращаем как было

    return re.sub(pattern, replacement, text)

async def send_msg(message):
    """Универсальная функция пересылки"""
    text = message.text or message.caption
    new_text = update_price(text) if text else text
    
    try:
        if message.photo:
            await app.send_photo(TARGET_CHAT, message.photo.file_id, caption=new_text)
        elif message.video:
            await app.send_video(TARGET_CHAT, message.video.file_id, caption=new_text)
        elif text:
            await app.send_message(TARGET_CHAT, new_text)
        # Если это просто файл или альбом (без текста и не фото/видео)
        elif not text:
            await message.copy(TARGET_CHAT)
    except Exception as e:
        print(f"Ошибка при отправке: {e}")

# Этот блок ловит НОВЫЕ сообщения
@app.on_message(filters.chat(SOURCE_CHAT))
async def auto_forward(client, message):
    print("Пришел новый пост, копирую...")
    await send_msg(message)

async def run_bot():
    print("Запуск бота Шамиля...")
    await app.start()
    
    # --- РАЗОВАЯ ВЫКАЧКА ИСТОРИИ ---
    print("Начинаю загрузку последних 300 постов для заполнения канала...")
    history = []
    async for message in app.get_chat_history(SOURCE_CHAT, limit=300):
        history.append(message)
    
    # Переворачиваем, чтобы посты шли от старых к новым
    for msg in reversed(history):
        await send_msg(msg)
        await asyncio.sleep(1.5) # Пауза 1.5 сек, чтобы не поймать бан от Telegram за спам
    
    print("Канал заполнен! Теперь бот следит за новыми постами в реальном времени.")
    # --- КОНЕЦ ВЫКАЧКИ ---

    from pyrogram import idle
    await idle()
    await app.stop()

if __name__ == "__main__":
    asyncio.run(run_bot())
