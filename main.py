import logging
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils import executor
from datetime import datetime
import openpyxl
import asyncio

# Танзими бот
TOKEN = "7522856876:AAG4h3FtTHEVQ9zfHpQV8pPWk7G-oMyP47Y"
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

logging.basicConfig(level=logging.INFO)

# Истифодабарандаи Админ ва рӯйхати корбарон
ADMIN_USER_ID = 7983949632
USER_LIST = [6816678410, 987654321]

tasks = []
user_task_times = {}

# Эҷоди файл барои сабти вазифаҳо
wb = openpyxl.Workbook()
sheet = wb.active
sheet.title = "Вазифаҳо"
sheet.append(["Истифодабаранда", "Вазифа", "Сана", "Соат", "Вақти оғоз", "Вақти анҷом"])

# Фармони /start
@dp.message_handler(commands=["start"])
async def start_command(message: types.Message):
    if message.from_user.id == ADMIN_USER_ID:
        await message.answer("Салом, Админ! Барои фиристодани хабар, фармони /send_message-ро истифода баред.")
    else:
        today = datetime.now().strftime("%d-%m-%Y")
        current_time = datetime.now().strftime("%H:%M")
        today_tasks = [task for task in tasks if task["date"] == today and task["time"] >= current_time]
        
        if today_tasks:
            task_texts = "\n\n".join([f"📝 {task['text']} ({task['time']})" for task in today_tasks])
            await message.answer(f"Салом! Вазифаҳои имрӯз:\n\n{task_texts}")
        else:
            await message.answer("Салом! Имрӯз вазифа вуҷуд надорад.")

# Фармони /send_message барои фиристодани вазифаҳо
@dp.message_handler(commands=["send_message"])
async def send_message_to_user(message: types.Message):
    if message.from_user.id != ADMIN_USER_ID:
        return

    parts = message.text.replace("/send_message", "").strip().split("|")
    if len(parts) < 3:
        await message.answer("Лутфан, вазифаро чунин нависед: /send_message [матни вазифа] | [сана dd-mm-yyyy] | [соат hh:mm]")
        return

    task_text, task_date, task_time = parts[0].strip(), parts[1].strip(), parts[2].strip()
    
    tasks.append({"text": task_text, "date": task_date, "time": task_time})
    
    full_message = f"📅 Сана: {task_date}\n⏰ Соат: {task_time}\n📝 Вазифа: {task_text}"
    for user_id in USER_LIST:
        markup = InlineKeyboardMarkup().add(
            InlineKeyboardButton("Иҷро кардан", callback_data=f"execute_task_{user_id}_{task_date}_{task_time}")
        )
        await bot.send_message(user_id, full_message, reply_markup=markup)

    await message.answer("Хабар ба истифодабарандагон фиристода шуд.")

# Иҷро кардани вазифа
@dp.callback_query_handler(lambda c: c.data.startswith('execute_task_'))
async def execute_task(callback_query: types.CallbackQuery):
    _, user_id, task_date, task_time = callback_query.data.split("_")
    user_id = int(user_id)
    
    if callback_query.from_user.id != user_id:
        return await bot.answer_callback_query(callback_query.id, text="Ин вазифа ба шумо тааллуқ надорад.")
    
    start_time = datetime.now().strftime("%H:%M:%S")
    user_task_times[user_id] = {"start": start_time, "task_date": task_date, "task_time": task_time}
    
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(user_id, f"✅ Вазифа оғоз шуд!\nВақти оғоз: {start_time}")

    markup = InlineKeyboardMarkup().add(
        InlineKeyboardButton("Анҷом додан", callback_data=f"complete_task_{user_id}_{task_date}_{task_time}")
    )
    await bot.send_message(user_id, "Вазифа иҷро шуда истодааст. Барои анҷом додан, 'Анҷом додан'-ро пахш кунед.", reply_markup=markup)

# Анҷоми вазифа
@dp.callback_query_handler(lambda c: c.data.startswith('complete_task_'))
async def complete_task(callback_query: types.CallbackQuery):
    _, user_id, task_date, task_time = callback_query.data.split("_")
    user_id = int(user_id)
    
    if callback_query.from_user.id != user_id:
        return await bot.answer_callback_query(callback_query.id, text="Ин вазифа ба шумо тааллуқ надорад.")

    end_time = datetime.now().strftime("%H:%M:%S")
    start_time = user_task_times[user_id].get("start", "Номаълум вақт")
    
    username = callback_query.from_user.full_name
    
    sheet.append([username, task_text, task_date, task_time, start_time, end_time])
    wb.save("vazifaho.xlsx")

    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(user_id, f"✅ Вазифа анҷом шуд!\nОғоз: {start_time}\nАнҷом: {end_time}")

# Фармони /delete_task барои нест кардани вазифа
@dp.message_handler(commands=["delete_task"])
async def delete_task(message: types.Message):
    if message.from_user.id != ADMIN_USER_ID:
        return

    parts = message.text.replace("/delete_task", "").strip().split("|")
    if len(parts) < 2:
        await message.answer("Лутфан, вазифаро чунин ворид кунед: /delete_task [сана dd-mm-yyyy] | [соат hh:mm]")
        return
    
    task_date, task_time = parts[0].strip(), parts[1].strip()
    
    global tasks
    tasks = [task for task in tasks if not (task["date"] == task_date and task["time"] == task_time)]
    
    await message.answer("✅ Вазифа нест карда шуд.")
    for user_id in USER_LIST:
        await bot.send_message(user_id, f"❌ Вазифа ({task_date} {task_time}) бекор карда шуд.")

# Оғози бот
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
