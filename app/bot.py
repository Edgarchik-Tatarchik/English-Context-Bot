import re
import asyncio
from aiogram import Bot, Dispatcher, Router, F
from aiogram.enums import ParseMode
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.ai_service import generate_explanation_and_examples

router = Router()

WORD_RE = re.compile(r"^[A-Za-z][A-Za-z\s'\-]{0,60}$")
def escape_md_v2(text: str) -> str:
    # Telegram MarkdownV2 special chars must be escaped:
    # _ * [ ] ( ) ~ ` > # + - = | { } . !
    return re.sub(r'([_*\[\]()~`>#+\-=|{}.!])', r'\\\1', text)


def build_actions_kb(term: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="➕ More examples", callback_data=f"more:{term}")
    kb.button(text="💾 Save", callback_data=f"save:{term}")
    kb.button(text="🧠 Quiz", callback_data=f"quiz:{term}")
    kb.adjust(2, 1)
    return kb.as_markup()


def format_answer(term: str, simple_explanation: str, examples: list[str]) -> tuple[str, str]:
    t = escape_md_v2(term)
    expl = escape_md_v2(simple_explanation)

    header = (
        f"📌 *Term:* `{t}`\n"
        f"🧾 *Simple explanation:*\n{expl}\n"
    )

    ex_lines = "\n".join([f"{i+1}\\) {escape_md_v2(s)}" for i, s in enumerate(examples)])
    examples_text = f"🧩 *Examples \\(10\\):*\n{ex_lines}"

    return header, examples_text


@router.message(F.text)
async def handle_text(message: Message):
    term = (message.text or "").strip()

    if not WORD_RE.match(term) or len(term.split()) > 4:
        await message.answer("Send me an English word or short phrase (1–4 words).")
        return

    wait_msg = await message.answer("⏳ Generating explanation + 10 examples...")

    try:
        data = await asyncio.to_thread(generate_explanation_and_examples, term)
        explanation = data["simple_explanation"]
        examples = data["examples"]

        header, examples_text = format_answer(term, explanation, examples)

        
        await wait_msg.edit_text(
            header,
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=build_actions_kb(term),
        )

        await message.answer(
            examples_text,
            parse_mode=ParseMode.MARKDOWN_V2,
        )

    except Exception as e:
        print("AI ERROR:", repr(e))


@router.callback_query(F.data.startswith("more:"))
async def on_more_examples(callback: CallbackQuery):
    term = callback.data.split(":", 1)[1].strip()

    await callback.answer("Generating more examples...")

    try:
        data = await asyncio.to_thread(generate_explanation_and_examples, term)
        examples = data["examples"]

        ex_lines = "\n".join([f"{i+1}\\) {escape_md_v2(s)}" for i, s in enumerate(examples)])
        text = f"➕ *More examples for* `{escape_md_v2(term)}`:\n{ex_lines}"

        await callback.message.answer(text, parse_mode=ParseMode.MARKDOWN_V2)

    except Exception as e:
        await callback.message.answer("⚠️ AI error while generating more examples.")
        print("AI ERROR (more):", repr(e))


@router.callback_query(F.data.startswith("save:"))
async def on_save(callback: CallbackQuery):
    await callback.answer("Saved ✅ (stub)")
    await callback.message.answer("💾 Save is not implemented yet. Next step: SQLite storage.")


@router.callback_query(F.data.startswith("quiz:"))
async def on_quiz(callback: CallbackQuery):
    await callback.answer("Quiz ✅ (stub)")
    await callback.message.answer("🧠 Quiz is not implemented yet. Next step: 3-question mini quiz.")


def create_bot_and_dispatcher(token: str):
    bot = Bot(token)
    dp = Dispatcher()
    dp.include_router(router)
    return bot, dp
