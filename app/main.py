from fastapi import FastAPI, Request
from aiogram.types import Update
from aiogram.exceptions import TelegramBadRequest
from app.config import BOT_TOKEN, PUBLIC_BASE_URL, WEBHOOK_PATH
from app.bot import create_bot_and_dispatcher

app = FastAPI()

bot, dp = create_bot_and_dispatcher(BOT_TOKEN)

@app.on_event("startup")
async def on_startup():
    if not PUBLIC_BASE_URL:
        print("PUBLIC_BASE_URL is empty -> webhook NOT set (ok for local dev)")
        return

    webhook_url = f"{PUBLIC_BASE_URL}{WEBHOOK_PATH}"
    try:
        await bot.set_webhook(webhook_url)
        print(f"Webhook set to: {webhook_url}")
    except TelegramBadRequest as e:
        print(f"Webhook NOT set (will continue without it): {e}")
    except Exception as e:
        print(f"Unexpected error while setting webhook: {repr(e)}")

@app.on_event("shutdown")
async def on_shutdown():
    await bot.session.close()

@app.post(WEBHOOK_PATH)
async def telegram_webhook(request: Request):
    data = await request.json()
    update = Update.model_validate(data)
    await dp.feed_update(bot, update)
    return {"ok": True}

@app.get("/health")
async def health():
    return {"status": "ok"}
