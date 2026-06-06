"""
Quiz handler for Technologia Club Bot
Sends AI-generated multiple choice questions as Telegram quiz polls
"""
import asyncio
import json
import logging
import re
from datetime import datetime

logger = logging.getLogger(__name__)

from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from ai import ai_manager
from config import BOT_OWNER_ID, GROUP_CHAT_ID, QUIZ_TOPIC_ID

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
    except Exception as e:
        logger.warning("is_admin check failed: %s", e)
        return False


def clean_user_topic(raw_args: list) -> str:
    """Cleans up messy user input like 'about the react make it for' -> 'React'"""
    raw_text = " ".join(raw_args)
    
    # Remove common conversational filler words users type
    filler_words = r'\b(about|the|a|an|make|it|for|to|generate|create|give|me|please|quiz|question)\b'
    clean_text = re.sub(filler_words, '', raw_text, flags=re.IGNORECASE)
    
    # Remove basic sentence punctuation (but keep +, #, . for things like C++ or Node.js)
    clean_text = re.sub(r'[,!?;:]', '', clean_text)
    
    # Clean up extra spaces
    clean_text = ' '.join(clean_text.split()).strip()
    
    # Title case it so the AI gets a clean topic
    return clean_text.title() if clean_text else ""


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


def build_quiz_prompt(topic: str) -> str:
    return f"""You are an expert quiz creator for a university tech club called Technologia Club.

Generate EXACTLY ONE multiple-choice question about: "{topic}"

STRICT FORMAT — Respond ONLY with a valid JSON array containing exactly ONE object. No markdown, no extra text.

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
- Generate EXACTLY 1 question. No more, no less.
- Exactly 4 options per question: A, B, C, D
- "answer" = one letter only: A, B, C, or D
- Options MUST be short (maximum 80 characters each). Keep them concise!
- Questions must be clear, unambiguous, and educational
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
    for i, q in enumerate(questions):
        try:
                        # Build options list: ["A. text", "B. text", ...]
            # Telegram limit is 100 chars per option. We truncate to 97 + "..." to be safe.
            options = []
            for k, v in q["options"].items():
                opt_text = f"{k}. {v}"
                if len(opt_text) > 100:
                    opt_text = opt_text[:97] + "..."
                options.append(opt_text)

            # Find the correct option index (0-based)
            keys = list(q["options"].keys())
            correct_idx = keys.index(q["answer"]) if q["answer"] in keys else 0

            # Since it's always 1 question, no need for "Q1/1" prefix
            question_text = f"❓ {q['question']}"

            # Telegram poll question limit = 300 chars
            if len(question_text) > 300:
                question_text = question_text[:297] + "..."

            kwargs = dict(
                chat_id=chat_id,
                question=question_text,
                options=options,
                type="quiz",
                correct_option_id=correct_idx,
                is_anonymous=True,
            )

            if thread_id:
                kwargs["message_thread_id"] = thread_id

            explanation = q.get("explanation", "")
            if explanation:
                # Telegram explanation limit is 200 chars
                if len(explanation) > 200:
                    explanation = explanation[:197] + "..."
                kwargs["explanation"] = explanation

            await bot.send_poll(**kwargs)

            # Delay between polls so it doesn't flood
            if i < len(questions) - 1:
                await asyncio.sleep(delay)

        except Exception as e:
            logger.error("Failed to send poll (Q%d): %s", i + 1, e, exc_info=True)
            raise e


# ─────────────────────────────────────────────
# /quiz command handler
# ─────────────────────────────────────────────

async def handle_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /quiz <topic>

    Examples:
        /quiz React Programming
        /quiz Machine Learning advanced
        /quiz about python, make it intermediate
    
    Limits:
        - Admins: Unlimited
        - Members: 1 quiz per 24 hours
    """
    user = update.effective_user
    admin = user.id == BOT_OWNER_ID or await is_admin(update, context)
    logger.info("/quiz called by user_id=%s username=%s admin=%s", user.id, user.username, admin)

    # Check rate limit for non-admins
    if not admin:
        allowed, reason = await can_user_take_quiz(user.id)
        if not allowed:
            await update.message.reply_text(reason)
            return

    if not context.args:
        await update.message.reply_text(
            "📋 *Quiz Generator*\n\n"
            "Usage: `/quiz <topic>`\n\n"
            "Examples:\n"
            "`/quiz React Programming`\n"
            "`/quiz Machine Learning advanced`\n\n"
            "_Limits: 1 quiz per 24h for members, unlimited for admins_",
            parse_mode='Markdown'
        )
        return

    # Parse args: topic [difficulty]
    args = context.args

    # Clean the topic (removes "about the", "make it for", etc.)
    topic = clean_user_topic(args)
    if not topic:
        topic = "Technology"

    logger.debug("quiz topic=%r difficulty=%r", topic)

    # Show typing action while generating
    try:
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    except Exception as e:
        logger.debug("send_chat_action failed (non-critical): %s", e)

    try:
        # Note: Removed 'count' argument here to match the function definition
        prompt = build_quiz_prompt(topic)

        # Call AI - use Qwen for quizzes (cheapest), charge tokens for non-admins
        result = await ai_manager.generate_response(
            prompt=prompt,
            user_id=user.id,
            is_owner=admin,  # Admins get free quiz generation
            provider='qwen'  # Force cheapest model for quizzes
        )

        if not result["success"]:
            logger.warning("AI generation failed for topic=%r: %s", topic, result['response'])
            await update.message.reply_text(f"\u274c AI error: {result['response']}")
            return

        # Record usage for rate limiting (only for non-admins)
        if not admin:
            record_quiz_usage(user.id)

        # Parse quiz
        try:
            questions = parse_quiz_json(result["response"])
            logger.debug("Parsed %d question(s) from AI response", len(questions))
            # Force exactly 1 question just in case the AI hallucinates more
            if len(questions) > 1:
                logger.warning("AI returned %d questions, trimming to 1", len(questions))
                questions = [questions[0]]
        except Exception as e:
            logger.error("JSON parse error for topic=%r: %s\nRaw response:\n%s",
                         topic, e, result.get("response", ""), exc_info=True)
            await update.message.reply_text(
                f"\u274c Failed to parse quiz from AI response.\n"
                f"Error: {str(e)}\n\n"
                f"Try again or rephrase your topic."
            )
            return

        if not questions:
            await update.message.reply_text("❌ AI returned empty quiz. Please try again.")
            return

        # Send polls to configured quiz channel/topic
        chat_id = GROUP_CHAT_ID if GROUP_CHAT_ID else update.effective_chat.id
        thread_id = QUIZ_TOPIC_ID if GROUP_CHAT_ID else None
        logger.info("Sending quiz poll → chat_id=%s thread_id=%s topic=%r",
                    chat_id, thread_id, topic)

        await send_quiz_polls(
            bot=context.bot,
            chat_id=chat_id,
            questions=questions,
            thread_id=thread_id,
            delay=2.0
        )

        # Send status/success message to the user who requested the quiz
        provider_emojis = {
            'gemini': '🔮',
            'deepseek': '🧠',
            'openrouter': '🌐',
            'qwen': '🐼'
        }
        prov = result.get("provider", "qwen")
        provider_emoji = provider_emojis.get(prov, "🤖")
        provider_name = prov.title()
        tokens_left = result.get("tokens_left", 0)

        status_text = (
            f"✅ *Quiz on {topic} sent successfully to the channel!*\n\n"
            f"{provider_emoji} *Provider:* {provider_name}\n"
        )
        if admin:
            status_text += f"🎫 *Admin:* ∞ tokens"
        else:
            status_text += f"🎫 *Tokens Left:* {tokens_left}/3"

        logger.info("Quiz sent successfully: topic=%r provider=%s tokens_left=%s",
                    topic, prov, tokens_left)
        await update.message.reply_text(status_text, parse_mode='Markdown')

    except Exception as e:
        logger.exception("Unhandled exception in handle_quiz for user_id=%s topic=%r", user.id, topic)
        await update.message.reply_text(f"\u274c Unexpected error: {str(e)}")


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