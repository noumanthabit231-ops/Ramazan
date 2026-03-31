import asyncio
import re
from pyrogram import Client, filters
from pyrogram.types import InputMediaPhoto, InputMediaVideo

# Исправление для Python 3.14
try:
    asyncio.get_event_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())

# Настройки
API_ID = 25186383
API_HASH = "ea2bbc60e23bdd24d1e137021795746f"
SOURCE_CHAT = "turktrendkatalog_obuv"
TARGET_CHAT = "turkshop_2026"

app = Client("my_session", api_id=API_ID, api_hash=API_HASH)

# Временное хранилище для альбомов
media_groups = {}

def update_price(text):
    if not text: return text
    
    # Регулярка ловит: "34$", "$34", "18.5 $", "$ 15,5"
    # Ищет число рядом со знаком доллара
    pattern = r"(\$?\s*\d+[\s\.,]?\d*\s*\$?)"
    
    def replacement(match):
        part = match.group(0)
        if '$' not in part: return part
        try:
            # Вытаскиваем только цифры, меняем запятую на точку
            clean_num = re.sub(r'[^\d\.,]', '', part).replace(',', '.')
            if not clean_num: return part
            
            new_val = float(clean_num) + 2.0
            # Возвращаем в формате "Число$"
            return f"{new_val:g}$"
        except:
            return part

    return re.sub(pattern, replacement, text)

async def get_enhanced_text(message):
    """Меняет цену в тексте или подписи"""
    text = message.text or message.caption
    return update_price(text) if text else text

async def forward_smart(message):
    """Умная пересылка: одиночки или альбомы"""
    try:
        # Если это часть альбома, обрабатываем через copy_media_group
        if message.media_group_id:
            # Для альбомов лучше использовать встроенный метод копирования
            # Он сохранит структуру, а мы просто подменим подпись
            await app.copy_media_group(
                chat_id=TARGET_CHAT,
                from_chat_id=SOURCE_CHAT,
                message_id=message.id,
                captions=lambda m: update_price(m.caption) if m.caption else None
            )
        else:
            # Одиночное сообщение
            new_text = await get_enhanced_text(message)
            if message.photo:
                await app.send_photo(TARGET_CHAT, message.photo.file_id, caption=new_text)
            elif message.video:
                await app.send_video(TARGET_CHAT, message.video.file_id, caption=new_text)
            elif message.text:
                await app.send_message(TARGET_CHAT, new_text)
            else:
                await message.copy(TARGET_CHAT)
    except Exception as e:
        print(f"Ошибка при пересылке {message.id}: {e}")

# Обработка новых сообщений в реальном времени
@app.on_message(filters.chat(SOURCE_CHAT))
async def handle_new_message(client, message):
    # Если это альбом, ждем немного, чтобы все части долетели
    if message.media_group_id:
        mid = message.media_group_id
        if mid not in media_groups:
            media_groups[mid] = True
            await asyncio.sleep(2) # Ждем сборки альбома
            await forward_smart(message)
            # Очистка через некоторое время
            await asyncio.sleep(10)
            media_groups.pop(mid, None)
    else:
        await forward_smart(message)

async def run_bot():
    print("--- Бот Шамиля (v2.0 Smart) запущен ---")
    await app.start()
    
    # --- СИНХРОНИЗАЦИЯ ИСТОРИИ (500 постов) ---
    print("Начинаю анализ последних 500 сообщений...")
    history = []
    processed_groups = set()
    
    async for msg in app.get_chat_history(SOURCE_CHAT, limit=500):
        history.append(msg)
    
    # Пересылаем от старых к новым
    for msg in reversed(history):
        if msg.media_group_id:
            if msg.media_group_id in processed_groups:
                continue
            processed_groups.add(msg.media_group_id)
        
        await forward_smart(msg)
        await asyncio.sleep(1.2) # Чтобы не словить FloodWait
        
    print("Синхронизация завершена. Бот работает в режиме LIVE.")
    
    from pyrogram import idle
    await idle()
    await app.stop()

if __name__ == "__main__":
    asyncio.run(run_bot())
