import os
import shutil
import asyncio
import sqlite3
import logging
from pathlib import Path
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, Document
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from multi_separator import run_separator
from multi_contact_uploader import run_uploader

logging.basicConfig(level=logging.INFO)
BOT_TOKEN = os.getenv('BOT_TOKEN') or '8132539274:AAFZ2IogAB7ZSkmFPFhxoOEzekoN50DbvAY'
ADMIN_IDS = {6479873978, 1662443041, 1582876151, 7093915113}
GENERAL_IDS = {7325489011, 7536448353, 1303962316}
WORKSPACES = Path('workspaces')
STORAGE_ROOT = Path('_storage')
DB_PATH = 'sessions.db'
GLOBAL_MAIN_FILE = Path('all_data.txt')

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS global_config (
            id INTEGER PRIMARY KEY CHECK(id=1),
            cut_size INTEGER,
            batch_size INTEGER,
            workers_per_account INTEGER
        )''')
    conn.execute('INSERT OR IGNORE INTO global_config(id, cut_size, batch_size, workers_per_account) VALUES(1, NULL, NULL, NULL)')
    conn.commit()
    return conn

_db_conn = init_db()
task_queue: asyncio.Queue[int] = asyncio.Queue()

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot=bot, storage=MemoryStorage())

class UploadStates(StatesGroup):
    data = State()
    main = State()

def is_admin(uid: int) -> bool:
    return uid in ADMIN_IDS

def is_general(uid: int) -> bool:
    return uid in GENERAL_IDS

def get_workspace(uid: int) -> Path:
    ws = WORKSPACES / str(uid)
    ws.mkdir(parents=True, exist_ok=True)
    return ws

async def broadcast_to_admins(sender: int, text: str):
    for admin in ADMIN_IDS:
        if admin != sender:
            await bot.send_message(admin, text)

@dp.message(Command('start'))
async def cmd_start(message: Message):
    text = (
        "Welcome!\n"
        "Use /upload_data to upload your data.txt file.\n"
        "Use /run to start processing.\n"
    )
    await message.answer(text)

@dp.message(Command('set_cut_size'))
async def cmd_set_cut_size(message: Message):
    uid = message.from_user.id
    if not is_admin(uid):
        return await message.answer('Unauthorized')
    try:
        val = int(message.text.split(maxsplit=1)[1])
    except:
        return await message.answer('Usage: /set_cut_size <integer>')
    _db_conn.execute('UPDATE global_config SET cut_size=? WHERE id=1', (val,))
    _db_conn.commit()
    await message.answer(f'cut_size set to {val}')
    await broadcast_to_admins(uid, f'Admin {uid} set cut_size to {val}')
    logging.info(f'Global cut_size updated to {val} by {uid}')

@dp.message(Command('set_batch_size'))
async def cmd_set_batch_size(message: Message):
    uid = message.from_user.id
    if not is_admin(uid):
        return await message.answer('Unauthorized')
    try:
        val = int(message.text.split(maxsplit=1)[1])
    except:
        return await message.answer('Usage: /set_batch_size <integer>')
    _db_conn.execute('UPDATE global_config SET batch_size=? WHERE id=1', (val,))
    _db_conn.commit()
    await message.answer(f'batch_size set to {val}')
    await broadcast_to_admins(uid, f'Admin {uid} set batch_size to {val}')
    logging.info(f'Global batch_size updated to {val} by {uid}')

@dp.message(Command('set_workers'))
async def cmd_set_workers(message: Message):
    uid = message.from_user.id
    if not is_admin(uid):
        return await message.answer('Unauthorized')
    try:
        val = int(message.text.split(maxsplit=1)[1])
    except:
        return await message.answer('Usage: /set_workers <integer>')
    _db_conn.execute('UPDATE global_config SET workers_per_account=? WHERE id=1', (val,))
    _db_conn.commit()
    await message.answer(f'workers_per_account set to {val}')
    await broadcast_to_admins(uid, f'Admin {uid} set workers_per_account to {val}')
    logging.info(f'Global workers_per_account updated to {val} by {uid}')

@dp.message(Command('upload_data'))
async def cmd_upload_data(message: Message, state: FSMContext):
    uid = message.from_user.id
    if not (is_admin(uid) or is_general(uid)):
        return await message.answer('Unauthorized')
    await state.set_state(UploadStates.data)
    await message.answer('📥 Please send data.txt.')

@dp.message(UploadStates.data, F.document)
async def process_data_file(message: Message, state: FSMContext):
    uid = message.from_user.id
    ws = get_workspace(uid)
    target_path = ws / 'data.txt'
    try:
        await bot.download(message.document, destination=target_path)
        size = target_path.stat().st_size
        await message.answer(f'✅ Saved data.txt ({size} bytes)')
        logging.info(f'data.txt saved for user {uid}, size={size}')
    except Exception as e:
        await message.answer(f'❌ Failed to download data.txt: {e}')
        logging.error(f'Error downloading data.txt for user {uid}: {e}')
        return
    await state.clear()

@dp.message(Command('upload_main'))
async def cmd_upload_main(message: Message, state: FSMContext):
    uid = message.from_user.id
    if not is_admin(uid):
        return await message.answer('Unauthorized')
    await state.set_state(UploadStates.main)
    await message.answer('📥 Please send all_data.txt as a document.')

@dp.message(UploadStates.main, F.document)
async def process_main_file(message: Message, state: FSMContext):
    uid = message.from_user.id
    await message.answer('🔄 Downloading all_data.txt...')
    try:
        await bot.download(message.document, destination=GLOBAL_MAIN_FILE)
        size = GLOBAL_MAIN_FILE.stat().st_size
        await message.answer(f'✅ Saved all_data.txt ({size} bytes)')
        logging.info(f'all_data.txt saved by admin {uid}, size={size}')
        await broadcast_to_admins(uid, f'Admin {uid} updated global email list.')
    except Exception as e:
        await message.answer(f'❌ Failed to download all_data.txt: {e}')
        logging.error(f'Error downloading all_data.txt: {e}')
        return
    await state.clear()

@dp.message(Command('run'))
async def cmd_run(message: Message):
    uid = message.from_user.id
    if not (is_admin(uid) or is_general(uid)):
        return await message.answer('Unauthorized')
    if not GLOBAL_MAIN_FILE.exists():
        return await message.answer('⚠️ Main email file not uploaded.')
    cur = _db_conn.cursor()
    cur.execute('SELECT cut_size, batch_size, workers_per_account FROM global_config WHERE id=1')
    cut_size, batch_size, workers = cur.fetchone()
    if not all([cut_size, batch_size, workers]):
        return await message.answer('⚠️ Set cut_size, batch_size, and workers first.')
    ws = get_workspace(uid)
    if not (ws / 'data.txt').exists():
        return await message.answer('⚠️ Missing data.txt.')
    await message.answer('🚀 Job queued.')
    await task_queue.put(uid)

async def worker():
    while True:
        uid = await task_queue.get()
        try:
            ws = get_workspace(uid)
            storage = STORAGE_ROOT / str(uid)
            storage.mkdir(parents=True, exist_ok=True)
            users_file = ws / 'users.txt'
            emails = []
            with open(ws / 'data.txt') as df:
                for line in df:
                    l = line.strip()
                    if l:
                        emails.append(l.split('\t')[0])
            with open(users_file, 'w') as uf:
                uf.write('\n'.join(emails) + '\n')
            await bot.send_message(uid, f'✅ Generated users.txt with {len(emails)} entries')
            cur = _db_conn.cursor()
            cur.execute('SELECT cut_size, batch_size, workers_per_account FROM global_config WHERE id=1')
            cut_size, batch_size, workers = cur.fetchone()
            await bot.send_message(uid, '🔄 Starting separator...')
            await run_separator(str(users_file), str(GLOBAL_MAIN_FILE), cut_size, str(storage))
            await bot.send_message(uid, '🔄 Separator done, starting uploader...')
            await run_uploader(str(ws / 'data.txt'), str(storage), workers, batch_size)
            await bot.send_message(uid, '🎉 All tasks completed')
        except Exception as e:
            logging.error(f'Error processing job for {uid}: {e}')
            await bot.send_message(uid, f'❌ Processing failed: {e}')
        finally:
            task_queue.task_done()

async def on_startup():
    await bot.delete_webhook(drop_pending_updates=True)
    for _ in range(2):
        asyncio.create_task(worker())

if __name__ == '__main__':
    dp.startup.register(on_startup)
    asyncio.run(dp.start_polling(bot))
