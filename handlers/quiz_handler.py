"""
Quiz handler for Technologia Club Bot
Sends AI-generated multiple choice questions as Telegram quiz polls
"""
import asyncio
import json
import re
from datetime import datetime

from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from ai import ai_manager
from config import BOT_OWNER_ID, ANNOUNCEMENT_TOPIC_ID

# ─────────────────────────────────────────────
# Rate limiting for members
# ─────────────────────────────────────────────

# Track last quiz time per user: {user_id: timestamp}
_user_quiz_cooldown = {}
QUIZ_COOLDOWN_SECONDS = 86400  # 24 hours


async def can_user_take_quiz(user_id: int) -> tuple[bool, str]:
    """Check if user can generate a quiz (admin = always yes)"""
    if user_id == BOT_OWNER_ID:
        return True, ""
    
    now = asyncio.get_event_loop().time()
    last_time = _user_quiz_cooldown.get(user_id, 0)
    
    if now - last_time < QUIZ_COOLDOWN_SECONDS:
        remaining = int(QUIZ_COOLDOWN_SECONDS - (now - last_time))
        hours = remaining // 3600
        minutes = (remaining % 3600) // 60
        return False, f"⏳ You can generate another quiz in {hours}h {minutes}m (1 per day limit)"
    
    return True, ""


def record_quiz_usage(user_id: int):
    """Record that user generated a quiz"""
    _user_quiz_cooldown[user_id] = asyncio.get_event_loop().time()


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    try:
        member = await context.bot.get_chat_member(
            chat_id=update.effective_chat.id,
            user_id=update.effective_user.id
        )
        return member.status in ['creator', 'administrator']
    except Exception:
        return False


def parse_quiz_json(raw: str) -> list:
    """Extract and parse JSON array from LLM response"""
    clean = raw.strip()
    # Strip markdown fences
    clean = re.sub(r'^```json\s*', '', clean, flags=re.IGNORECASE)
    clean = re.sub(r'^```\s*', '', clean, flags=re.IGNORECASE)
    clean = re.sub(r'\s*```$', '', clean)

    # Find [ ... ]
    start = clean.find('[')
    end = clean.rfind(']')
    if start == -1 or end == -1:
        raise ValueError("No JSON array found in LLM response")

    return json.loads(clean[start:end + 1])


def build_quiz_prompt(topic: str, count: int, difficulty: str = "intermediate") -> str:
    return f"""You are a quiz creator for a university tech club called Technologia Club.

Generate exactly {count} multiple choice quiz questions about: "{topic}"
Difficulty: {difficulty}

STRICT FORMAT — Respond ONLY with a valid JSON array. No markdown, no extra text.

[
  {{
    "question": "Full question text here?",
    "options": {{
      "A": "First option text",
      "B": "Second option text",
      "C": "Third option text",
      "D": "Fourth option text"
    }},
    "answer": "A",
    "explanation": "Brief explanation why this answer is correct"
  }}
]

Rules:
- Exactly 4 options per question: A, B, C, D
- "answer" = one letter only: A, B, C, or D
- Questions must be clear, unambiguous, and educational
- Vary which letter is correct across questions
- Return ONLY the JSON array, nothing else"""


# ─────────────────────────────────────────────
# Send polls
# ─────────────────────────────────────────────

async def send_quiz_polls(
    bot,
    chat_id: int,
    questions: list,
    thread_id: int = None,
    delay: float = 2.0
):
    """Send each quiz question as a Telegram quiz poll"""
    total = len(questions)

    for i, q in enumerate(questions):
        try:
            # Build options list: ["A. text", "B. text", ...]
            options = [f"{k}. {v}" for k, v in q["options"].items()]

            # Find the correct option index (0-based)
            keys = list(q["options"].keys())
            correct_idx = keys.index(q["answer"]) if q["answer"] in keys else 0

            question_text = f"❓ Q{i + 1}/{total}: {q['question']}"

            # Telegram poll question limit = 300 chars
            if len(question_text) > 300:
                question_text = question_text[:297] + "..."

            kwargs = dict(
                chat_id=chat_id,
                question=question_text,
                options=options,
                type="quiz",
                correct_option_id=correct_idx,
                is_anonymous=False,
            )

            if thread_id:
                kwargs["message_thread_id"] = thread_id

            explanation = q.get("explanation", "")
            if explanation:
                kwargs["explanation"] = explanation[:200]  # Telegram limit

            await bot.send_poll(**kwargs)

            # Delay between polls so it doesn't flood
            if i < total - 1:
                await asyncio.sleep(delay)

        except Exception as e:
            print(f"❌ Failed to send poll Q{i + 1}: {e}")


# ─────────────────────────────────────────────
# /quiz command handler
# ─────────────────────────────────────────────

async def handle_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /quiz <topic> [count] [difficulty]

    Examples:
        /quiz AI Development
        /quiz Machine Learning 5
        /quiz Python advanced 3
    
    Limits:
        - Admins: Unlimited
        - Members: 1 quiz per 24 hours
    """
    user = update.effective_user
    admin = user.id == BOT_OWNER_ID or await is_admin(update, context)

    # Check rate limit for non-admins
    if not admin:
        allowed, reason = await can_user_take_quiz(user.id)
        if not allowed:
            await update.message.reply_text(reason)
            return

    if not context.args:
        await update.message.reply_text(
            "📋 *Quiz Generator*\n\n"
            "Usage: `/quiz <topic> [count] [difficulty]`\n\n"
            "Examples:\n"
            "`/quiz AI Development`\n"
            "`/quiz Machine Learning 5`\n"
            "`/quiz Python advanced 3`\n\n"
            "Difficulty: `beginner` | `intermediate` | `advanced` | `mixed`\n\n"
            "_Limits: 1 quiz per 24h for members, unlimited for admins_",
            parse_mode='Markdown'
        )
        return

    # Parse args: topic [count] [difficulty]
    args = context.args
    difficulty = "intermediate"
    count = 4

    # Check last arg for difficulty keyword
    diff_keywords = {"beginner", "intermediate", "advanced", "mixed"}
    if args[-1].lower() in diff_keywords:
        difficulty = args[-1].lower()
        args = args[:-1]

    # Check last remaining arg for count (number)
    if args and args[-1].isdigit():
        count = max(1, min(10, int(args[-1])))  # Reduced max to 10 to save tokens
        args = args[:-1]

    topic = " ".join(args) if args else "AI Development"

    # Status message
    provider_emoji = "🔮" if ai_manager.get_current_provider() == "gemini" else "🧠"
    status_msg = await update.message.reply_text(
        f"{provider_emoji} Generating *{count} quiz questions* about *{topic}*...\n"
        f"_Difficulty: {difficulty}_",
        parse_mode='Markdown'
    )

    try:
        prompt = build_quiz_prompt(topic, count, difficulty)

        # Call AI - use Qwen for quizzes (cheapest), charge tokens for non-admins
        result = await ai_manager.generate_response(
            prompt=prompt,
            user_id=user.id,
            is_owner=admin,  # Admins get free quiz generation
            provider='qwen'  # Force cheapest model for quizzes
        )

        if not result["success"]:
            await status_msg.edit_text(f"❌ AI error: {result['response']}")
            return

        # Record usage for rate limiting (only for non-admins)
        if not admin:
            record_quiz_usage(user.id)

        # Parse quiz
        try:
            questions = parse_quiz_json(result["response"])
        except Exception as e:
            await status_msg.edit_text(
                f"❌ Failed to parse quiz from AI response.\n"
                f"Error: {str(e)}\n\n"
                f"Try again or rephrase your topic."
            )
            return

        if not questions:
            await status_msg.edit_text("❌ AI returned empty quiz. Please try again.")
            return

        # Update status
        await status_msg.edit_text(
            f"✅ Generated *{len(questions)} questions*! Sending polls...",
            parse_mode='Markdown'
        )

        # Send intro message
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            message_thread_id=ANNOUNCEMENT_TOPIC_ID,
            text=(
                f"📚 *Quiz Time!*\n\n"
                f"Topic: *{topic}*\n"
                f"Questions: *{len(questions)}*\n"
                f"Difficulty: *{difficulty.title()}*\n\n"
                f"Answer each poll before the explanation shows! 🎯"
            ),
            parse_mode='Markdown'
        )

        await asyncio.sleep(1)

        # Send polls to announcement topic
        await send_quiz_polls(
            bot=context.bot,
            chat_id=update.effective_chat.id,
            questions=questions,
            thread_id=ANNOUNCEMENT_TOPIC_ID,
            delay=2.0
        )

        # Final message
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            message_thread_id=ANNOUNCEMENT_TOPIC_ID,
            text=(
                f"🏁 *Quiz Complete!*\n\n"
                f"That's all {len(questions)} questions for today's *{topic}* quiz.\n"
                f"Good luck! 🤓"
            ),
            parse_mode='Markdown'
        )

        # Delete the generating status
        await status_msg.delete()

    except Exception as e:
        await status_msg.edit_text(f"❌ Unexpected error: {str(e)}")
        print(f"Quiz error: {e}")


# ─────────────────────────────────────────────
# /quizstatus - show current quiz provider
# ─────────────────────────────────────────────

async def handle_quiz_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show available quiz topics and current AI provider"""
    provider = ai_manager.get_current_provider()
    available = ai_manager.get_available_providers()

    text = (
        "📋 *Quiz Generator Status*\n\n"
        f"AI Provider: `{provider.title()}`\n"
        f"Available: `{', '.join(available)}`\n\n"
        "*Quick topic ideas:*\n"
        "• AI Development\n"
        "• Machine Learning\n"
        "• Python Programming\n"
        "• Computer Networks\n"
        "• Cybersecurity Basics\n"
        "• Web Development\n"
        "• Data Structures\n\n"
        "Use `/switchllm <provider>` to change AI"
    )

    await update.message.reply_text(text, parse_mode='Markdown')


# ─────────────────────────────────────────────
# Register handlers (add to your bot.py)
# ─────────────────────────────────────────────

def register_quiz_handlers(application):
    """Call this in your bot.py setup"""
    application.add_handler(CommandHandler("quiz", handle_quiz))
    application.add_handler(CommandHandler("quizstatus", handle_quiz_status))
