import asyncio
import re
from pyrogram import Client, filters

# Исправление для Python 3.14 (создаем цикл событий до импорта)
try:
    asyncio.get_event_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())

# Твои данные (НЕ МЕНЯЙ, ЕСЛИ ОНИ ВЕРНЫЕ)
API_ID = 25186383
API_HASH = "ea2bbc60e23bdd24d1e137021795746f"
SOURCE_CHAT = "turktrendkatalog_obuv"
TARGET_CHAT = "turkshop_2026"

app = Client("my_session", api_id=API_ID, api_hash=API_HASH)

def update_price(text):
    if not text:
        return text
    
    # Улучшенное правило: ищет число (целое или с точкой/запятой)
    # после которого идет один или два знака доллара ($ или $$)
    # Ловит: "34$", "18.5$$", "15 . 5 $", "35 $$"
    pattern = r"(\d+[\s\.,]?\d*)\s*\$+"
    
    def replacement(match):
        try:
            # Чистим число от пробелов и меняем запятую на точку для расчетов
            raw_num = match.group(1).replace(" ", "").replace(",", ".")
            # Прибавляем 2 доллара
            new_price = float(raw_num) + 2.0
            
            # Возвращаем красивое число (без лишних нулей после точки) и знак $
            return f"{new_price:g}$"
        except Exception as e:
            # Если что-то пошло не так (например, не число), оставляем как было
            return match.group(0)

    return re.sub(pattern, replacement, text)

async def send_msg(message):
    """Функция для обработки и пересылки сообщения"""
    try:
        text = message.text or message.caption
        new_text = update_price(text) if text else text
        
        # Если в сообщении есть фото
        if message.photo:
            await app.send_photo(TARGET_CHAT, message.photo.file_id, caption=new_text)
        # Если в сообщении есть видео
        elif message.video:
            await app.send_video(TARGET_CHAT, message.video.file_id, caption=new_text)
        # Если это просто текст
        elif text:
            await app.send_message(TARGET_CHAT, new_text)
        # Если это какой-то другой файл (документ, стикер и т.д.) без текста
        else:
            await message.copy(TARGET_CHAT)
            
    except Exception as e:
        print(f"Ошибка при обработке сообщения {message.id}: {e}")

# Слушаем новые посты в реальном времени
@app.on_message(filters.chat(SOURCE_CHAT))
async def auto_forward(client, message):
    print(f"Поступил новый пост (ID: {message.id}). Копирую с наценкой...")
    await send_msg(message)

async def run_bot():
    print("--- Бот Шамиля запущен ---")
    await app.start()
    
    # --- БЛОК РАЗОВОЙ ВЫКАЧКИ ИСТОРИИ ---
    # Если история больше не нужна, можно удалить строки ниже до надписи "КОНЕЦ ВЫКАЧКИ"
    print("Заполняю канал: выкачиваю последние 300 постов...")
    history = []
    async for message in app.get_chat_history(SOURCE_CHAT, limit=300):
        history.append(message)
    
    # Пересылаем от старых к новым
    for msg in reversed(history):
        await send_msg(msg)
        # Пауза 1.5 сек, чтобы Telegram не заблокировал за спам
        await asyncio.sleep(1.5) 
    
    print("Заполнение истории завершено!")
    # --- КОНЕЦ ВЫКАЧКИ ---

    print("Бот перешел в режим ожидания новых постов...")
    from pyrogram import idle
    await idle()
    await app.stop()

if __name__ == "__main__":
    # Запуск через современный метод asyncio
    try:
        asyncio.run(run_bot())
    except KeyboardInterrupt:
        pass
