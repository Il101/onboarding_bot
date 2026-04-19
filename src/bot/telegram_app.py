from __future__ import annotations

from collections.abc import Callable
from contextlib import contextmanager
from typing import Any

from sqlalchemy.orm import Session
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from src.ai.langgraph.graph import build_graph
from src.ai.langgraph.state import BotAnswer, SourceRef, build_thread_id
from src.bot.auth import authorize_telegram_user, build_access_denied_answer
from src.bot.feedback import save_feedback_event
from src.bot.presenters import render_bot_message
from src.core.config import settings
from src.core.logging import get_logger

logger = get_logger(__name__)


def _feedback_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("👍", callback_data="feedback:up"), InlineKeyboardButton("👎", callback_data="feedback:down")]]
    )


def _safe_error_answer() -> BotAnswer:
    return BotAnswer(
        answer="Не удалось обработать запрос. Попробуйте снова или обратитесь к коллеге.",
        confidence=0.0,
        fallback_used=True,
        sources=[
            SourceRef(
                source_id="policy:error",
                excerpt="Внутренняя ошибка обработана безопасным ответом.",
                timestamp="1970-01-01T00:00:00",
            )
        ],
    )


@contextmanager
def _session_scope(factory: Callable[[], Session]):
    db = factory()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None or update.effective_user is None:
        return
    decision = authorize_telegram_user(update.effective_user.id)
    if not decision.allowed:
        denied = build_access_denied_answer(reason=decision.reason)
        await update.message.reply_text(text=render_bot_message(denied))
        return
    await update.message.reply_text(text="Бот готов. Задайте рабочий вопрос.")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None or update.effective_chat is None or update.effective_user is None:
        return
    decision = authorize_telegram_user(update.effective_user.id)
    if not decision.allowed:
        denied = build_access_denied_answer(reason=decision.reason)
        await update.message.reply_text(text=render_bot_message(denied))
        return

    thread_id = build_thread_id(chat_id=update.effective_chat.id, user_id=update.effective_user.id)
    graph = context.application.bot_data["graph"]
    try:
        result = await graph.ainvoke(
            {
                "role": decision.role,
                "query": update.message.text or "",
                "user_id": str(update.effective_user.id),
                "chat_id": str(update.effective_chat.id),
            },
            config={"configurable": {"thread_id": thread_id}},
        )
        answer: BotAnswer = result.get("result") or _safe_error_answer()
    except Exception as exc:  # noqa: BLE001
        logger.error("telegram message handler failed: %s", exc)
        answer = _safe_error_answer()

    message_id = int(getattr(update.message, "message_id", 0) or 0)
    context.application.bot_data[f"confidence:{thread_id}:{message_id}"] = answer.confidence
    await update.message.reply_text(text=render_bot_message(answer), reply_markup=_feedback_keyboard())


async def handle_feedback_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if query is None or query.message is None:
        return

    try:
        with _session_scope(context.application.bot_data["db_session_factory"]) as db:
            user_id = int(query.from_user.id)
            chat_id = int(query.message.chat.id)
            thread_id = build_thread_id(chat_id=chat_id, user_id=user_id)
            confidence = context.application.bot_data.get(
                f"confidence:{thread_id}:{query.message.message_id}",
                0.0,
            )
            save_feedback_event(
                db,
                callback_data=query.data or "",
                thread_id=thread_id,
                message_id=int(query.message.message_id),
                user_id=user_id,
                chat_id=chat_id,
                answer_confidence=float(confidence),
            )
        await query.answer(text="Спасибо за оценку!")
    except ValueError:
        await query.answer(text="Некорректный формат оценки.")
    except Exception as exc:  # noqa: BLE001
        logger.error("telegram feedback handler failed: %s", exc)
        await query.answer(text="Не удалось сохранить оценку.")


def build_application(
    *,
    token: str | None = None,
    graph: Any | None = None,
    db_session_factory: Callable[[], Session] | None = None,
) -> Application:
    from src.api.deps import SessionLocal

    app = Application.builder().token(token or settings.telegram_bot_token).build()
    app.bot_data["graph"] = graph or build_graph()
    app.bot_data["db_session_factory"] = db_session_factory or SessionLocal
    app.add_handler(CommandHandler("start", handle_start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(handle_feedback_callback, pattern=r"^feedback:"))
    return app
