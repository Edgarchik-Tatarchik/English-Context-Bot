import re
import asyncio
from aiogram.filters import CommandStart, Command
from aiogram import Bot, Dispatcher, Router, F
from aiogram.enums import ParseMode
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from app.storage import init_db, save_term, list_saved, get_saved_item, get_random_saved_term, add_quiz_attempt


from app.ai_service import generate_explanation_and_examples, generate_quiz_distractors

router = Router()

WORD_RE = re.compile(r"^[A-Za-z][A-Za-z\s'\-]{0,60}$")
CACHE: dict[tuple[int, str], dict] = {}
STARTED_USERS: set[int] = set()
def escape_md_v2(text: str) -> str:
    
    return re.sub(r'([_*\[\]()~`>#+\-=|{}.!])', r'\\\1', text)


def build_actions_kb(term: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="➕ More examples", callback_data=f"more:{term}")
    kb.button(text="💾 Save", callback_data=f"save:{term}")
    kb.button(text="🧠 Quiz", callback_data=f"quiz:{term}")
    kb.button(text="📚 Saved words", callback_data="saved:1")
    kb.adjust(2, 2)
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

@router.message(CommandStart())
async def cmd_start(message: Message):
    STARTED_USERS.add(message.from_user.id)
    text = (
        "👋 Hi! I’m *English Context Bot*.\n\n"
        "Send me an English word or short phrase (1–4 words), and I will:\n"
        "• explain it in simple English\n"
        "• generate 10 example sentences\n\n"
        "Buttons:\n"
        "💾 Save — save this term\n"
        "🧠 Quiz — quiz from this saved term\n"
        "📚 Saved words — list your saved terms\n\n"
        "Try: `take a break`"
    )
    await message.answer(text)

@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "Send a word/phrase (1–4 words). Example: `make up`",
        parse_mode=ParseMode.MARKDOWN_V2
    )

@router.message(F.text)
async def handle_text(message: Message):
    if message.from_user.id not in STARTED_USERS:
        await message.answer("Please type /start first 🙂")
        return
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
    if callback.from_user.id not in STARTED_USERS:
        await callback.answer("Type /start first 🙂", show_alert=True)
        return
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

    
@router.callback_query(F.data.startswith("saved:"))
async def on_saved(callback: CallbackQuery):
    if callback.from_user.id not in STARTED_USERS:
        await callback.answer("Type /start first 🙂", show_alert=True)
        return
    page = int(callback.data.split(":")[1])
    terms = list_saved(callback.from_user.id, limit=300)  
    text, kb = render_saved_page(terms, page)
    await callback.message.answer(text, parse_mode=ParseMode.MARKDOWN_V2, reply_markup=kb)
    await callback.answer()
    
@router.message(F.text == "/saved")
async def saved_cmd(message: Message):
    terms = list_saved(message.from_user.id, limit=300)
    text, kb = render_saved_page(terms, 1)
    await message.answer(text, parse_mode=ParseMode.MARKDOWN_V2, reply_markup=kb)

PAGE_SIZE = 10

def render_saved_page(terms: list[str], page: int) -> tuple[str, InlineKeyboardMarkup | None]:
    total = len(terms)
    if total == 0:
        return "📚 You have no saved terms yet.", None

    pages = (total + PAGE_SIZE - 1) // PAGE_SIZE
    page = max(1, min(page, pages))

    start = (page - 1) * PAGE_SIZE
    chunk = terms[start:start + PAGE_SIZE]

    lines = "\n".join([f"{start+i+1}. {t}" for i, t in enumerate(chunk)])
    text = f"📚 *Saved terms* \\(page {page}/{pages}\\)\n\n{escape_md_v2(lines)}"


    kb = InlineKeyboardBuilder()
    if page > 1:
        kb.button(text="⬅ Prev", callback_data=f"saved:{page-1}")
    if page < pages:
        kb.button(text="Next ➡", callback_data=f"saved:{page+1}")
    kb.adjust(2)

    return text, kb.as_markup()


@router.callback_query(F.data.startswith("save:"))
async def on_save(callback: CallbackQuery):
    if callback.from_user.id not in STARTED_USERS:
        await callback.answer("Type /start first 🙂", show_alert=True)
        return
    term = callback.data.split(":", 1)[1].strip()
    user_id = callback.from_user.id

    payload = CACHE.get((user_id, term))
    if not payload:
        await callback.answer("No cached data. Send the term again, then press Save.", show_alert=True)
        return

    ok = save_term(
        user_id=user_id,
        term = term.lower(),
        explanation=payload["explanation"],
        examples=payload["examples"],
    )

    if ok:
        await callback.answer("Saved ✅")
    else:
        await callback.answer("Already saved 👍")


@router.callback_query(F.data.startswith("quiz:"))
async def on_quiz(callback: CallbackQuery):
    if callback.from_user.id not in STARTED_USERS:
        await callback.answer("Type /start first 🙂", show_alert=True)
        return
    user_id = callback.from_user.id
    term = callback.data.split(":", 1)[1].strip()  

    item = get_saved_item(user_id, term)
    if not item:
        await callback.answer("This term is not saved yet. Press 💾 Save first.", show_alert=True)
        return

    correct = item.explanation.strip()
    await callback.answer("Generating quiz...")

    try:
        distractors = await asyncio.to_thread(generate_quiz_distractors, term, correct)
    except Exception as e:
        print("AI ERROR (distractors):", repr(e))
        distractors = [
            "It describes something very expensive and luxurious.",
            "It means to stop doing something for a short time."
        ]

    if not isinstance(distractors, list) or len(distractors) != 2:
        distractors = [
            "It describes something very expensive and luxurious.",
            "It means to stop doing something for a short time."
        ]

    options = [correct] + distractors

    import random
    random.shuffle(options)
    correct_index = options.index(correct)

    kb = InlineKeyboardBuilder()
    for i in range(len(options)):
        kb.button(text=str(i + 1), callback_data=f"quiz_ans:{term}:{i}:{correct_index}")
    kb.adjust(3)

    lines = "\n".join([f"{i+1}\\) {escape_md_v2(o)}" for i, o in enumerate(options)])
    text = (
        f"🧠 *Quiz:* Choose the best explanation for `{escape_md_v2(term)}`\n\n"
        f"{lines}"
    )

    await callback.message.answer(text, parse_mode=ParseMode.MARKDOWN_V2, reply_markup=kb.as_markup())



@router.callback_query(F.data.startswith("quiz_ans:"))
async def on_quiz_answer(callback: CallbackQuery):
    if callback.from_user.id not in STARTED_USERS:
        await callback.answer("Type /start first 🙂", show_alert=True)
        return
    _, term, chosen_str, correct_str = callback.data.split(":")
    chosen = int(chosen_str)
    correct = int(correct_str)
    user_id = callback.from_user.id

    add_quiz_attempt(user_id, term, chosen, correct)

    item = get_saved_item(user_id, term)
    correct_text = item.explanation.strip() if item else "N/A"
    example = item.examples[0] if (item and item.examples) else ""

    if chosen == correct:
        await callback.answer("Correct ✅", show_alert=True)
    else:
        await callback.answer(f"Wrong ❌ Correct: {correct+1}", show_alert=True)

    msg = (
        f"✅ *Correct explanation for* `{escape_md_v2(term)}`:\n"
        f"{escape_md_v2(correct_text)}\n\n"
        f"📌 *Example:*\n{escape_md_v2(example)}"
    )
    await callback.message.answer(msg, parse_mode=ParseMode.MARKDOWN_V2)



def create_bot_and_dispatcher(token: str):
    init_db()
    bot = Bot(token)
    dp = Dispatcher()
    dp.include_router(router)
    return bot, dp
