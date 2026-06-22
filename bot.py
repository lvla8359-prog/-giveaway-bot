import asyncio, random, json
import aiofiles
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ChatMemberStatus

BOT_TOKEN = "8634401356:AAFDAAFnGP0AOcqDNCaRT54itK9M5L680PQ"
CHANNEL_ID = "@CentralPodBarnaul"
ADMIN_ID = 8293301430

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
DATA_FILE = "users.json"

async def load_data():
    try:
        async with aiofiles.open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.loads(await f.read())
    except:
        return {}

async def save_data(data):
    async with aiofiles.open(DATA_FILE, "w", encoding="utf-8") as f:
        await f.write(json.dumps(data, indent=2, ensure_ascii=False))

async def is_subscribed(user_id):
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status in [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR]
    except:
        return False

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    args = message.text.split()
    data = await load_data()
    bot_info = await bot.get_me()

    if len(args) >= 2 and args[1].startswith("ref_"):
        referrer_id = int(args[1].replace("ref_", ""))
        if referrer_id == user_id:
            await message.answer("🚫 Нельзя приглашать самого себя.")
            return
        if not await is_subscribed(user_id):
            await message.answer("❌ Сначала подпишитесь на канал.")
            return
        if str(user_id) in data and data[str(user_id)].get("invited_by"):
            await message.answer("⚠️ Вы уже были приглашены ранее.")
            return
        if str(referrer_id) not in data:
            data[str(referrer_id)] = {"invites": 0, "qualified": False}
        data[str(referrer_id)]["invites"] += 1
        data[str(user_id)] = {"invited_by": referrer_id, "qualified": False}
        invites = data[str(referrer_id)]["invites"]
        if invites >= 3:
            data[str(referrer_id)]["qualified"] = True
            await bot.send_message(referrer_id, "🎉 Вы собрали 3 приглашения и участвуете в розыгрыше!")
        else:
            await bot.send_message(referrer_id, f"👥 Новое приглашение! Прогресс: {invites} / 3")
        await save_data(data)
        await message.answer("✅ Вы засчитаны как приглашённый!")
        return

    if str(user_id) in data and data[str(user_id)].get("qualified", False):
        await message.answer("✅ Вы уже участвуете в розыгрыше! Ждите результатов.")
        return

    if not await is_subscribed(user_id):
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📢 Подписаться на канал", url=f"https://t.me/{CHANNEL_ID[1:]}")],
            [InlineKeyboardButton(text="🔄 Проверить подписку", callback_data="check_sub")]
        ])
        await message.answer(
            "❌ Для участия нужно подписаться на канал!\n"
            "После подписки нажмите «Проверить подписку».",
            reply_markup=kb
        )
        return

    ref_link = f"https://t.me/{bot_info.username}?start=ref_{user_id}"
    invites = data.get(str(user_id), {}).get("invites", 0)
    await message.answer(
        f"✅ Вы подписаны!\n\n"
        f"🔗 Ваша ссылка для приглашения:\n{ref_link}\n\n"
        f"👥 Пригласите 3 друзей (каждый должен подписаться на канал).\n"
        f"Прогресс: {invites} / 3"
    )

@dp.callback_query(lambda c: c.data == "check_sub")
async def check_sub(callback: types.CallbackQuery):
    if await is_subscribed(callback.from_user.id):
        await callback.message.edit_text("✅ Подписка подтверждена! Используйте /start для получения ссылки.")
    else:
        await callback.answer("❌ Вы ещё не подписаны!", show_alert=True)

@dp.message(Command("draw"))
async def draw_winner(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔️ Доступно только администратору.")
        return
    data = await load_data()
    qualified = [uid for uid, info in data.items() if info.get("qualified", False)]
    if not qualified:
        await message.answer("❌ Нет участников, выполнивших условия.")
        return
    winner_id = random.choice(qualified)
    await bot.send_message(winner_id, "🏆 Вы выиграли розыгрыш! Напишите администратору @admin_username")
    await message.answer(f"✅ Победитель выбран! (ID: {winner_id})")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())