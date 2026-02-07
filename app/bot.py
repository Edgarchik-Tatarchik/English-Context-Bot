import re
import asyncio
from aiogram import Bot, Dispatcher, Router, F
from aiogram.enums import ParseMode
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from app.storage import init_db, save_term, list_saved, get_saved_item, get_random_saved_term, add_quiz_attempt


from app.ai_service import generate_explanation_and_examples

router = Router()

WORD_RE = re.compile(r"^[A-Za-z][A-Za-z\s'\-]{0,60}$")
CACHE: dict[tuple[int, str], dict] = {}
def escape_md_v2(text: str) -> str:
    
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
        CACHE[(message.from_user.id, term)] = {
            "explanation": explanation,
            "examples": examples,
        }

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

@router.message(F.text == "/saved")
async def saved_cmd(message: Message):
    items = list_saved(message.from_user.id, limit=20)
    if not items:
        await message.answer("You haven't saved any terms yet. Use 💾 Save under an answer.")
        return
    text = "💾 Saved terms (latest 20):\n" + "\n".join([f"- {t}" for t in items])
    await message.answer(text)


@router.callback_query(F.data.startswith("save:"))
async def on_save(callback: CallbackQuery):
    term = callback.data.split(":", 1)[1].strip()
    user_id = callback.from_user.id

    payload = CACHE.get((user_id, term))
    if not payload:
        await callback.answer("No cached data. Send the term again, then press Save.", show_alert=True)
        return

    ok = save_term(
        user_id=user_id,
        term=term,
        explanation=payload["explanation"],
        examples=payload["examples"],
    )

    if ok:
        await callback.answer("Saved ✅")
    else:
        await callback.answer("Already saved 👍")


@router.callback_query(F.data.startswith("quiz:"))
async def on_quiz(callback: CallbackQuery):
    user_id = callback.from_user.id

    term = get_random_saved_term(user_id)
    if not term:
        await callback.answer("Save some terms first 🙂", show_alert=True)
        return

    item = get_saved_item(user_id, term)
    if not item:
        await callback.answer("Quiz data not found. Try again.", show_alert=True)
        return

    correct = item.explanation.strip()
    fake1 = f"It is related to '{term}', but not exactly."
    fake2 = f"It means the opposite of '{term}'."
    options = [correct, fake1, fake2]

    import random
    random.shuffle(options)
    correct_index = options.index(correct)

    kb = InlineKeyboardBuilder()
    for i in range(len(options)):
        kb.button(text=str(i + 1), callback_data=f"quiz_ans:{term}:{i}:{correct_index}")
    kb.adjust(3)

    # ВАЖНО: экранируем для MarkdownV2
    lines = "\n".join([f"{i+1}\\) {escape_md_v2(o)}" for i, o in enumerate(options)])
    text = (
        f"🧠 *Quiz:* What is the best explanation for `{escape_md_v2(term)}`?\n\n"
        f"{lines}"
    )

    await callback.message.answer(text, parse_mode=ParseMode.MARKDOWN_V2, reply_markup=kb.as_markup())
    await callback.answer()

@router.callback_query(F.data.startswith("quiz_ans:"))
async def on_quiz_answer(callback: CallbackQuery):
    _, term, chosen_str, correct_str = callback.data.split(":")
    chosen = int(chosen_str)
    correct = int(correct_str)
    user_id = callback.from_user.id

    add_quiz_attempt(user_id, term, chosen, correct)

    if chosen == correct:
        await callback.answer("Correct ✅", show_alert=True)
    else:
        await callback.answer(f"Not quite ❌ Correct: {correct+1}", show_alert=True)


def create_bot_and_dispatcher(token: str):
    init_db()
    bot = Bot(token)
    dp = Dispatcher()
    dp.include_router(router)
    return bot, dp
