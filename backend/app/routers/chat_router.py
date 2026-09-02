import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas, auth, crisis
from app.rag.retriever import retrieve_and_format
from app.llm.groq_client import generate_response, GroqNotConfiguredError

router = APIRouter(prefix="/chat", tags=["chat"])

SYSTEM_PROMPT_TEMPLATE = """You are Jane, a supportive listening companion on the Mentalist platform, grounded in \
evidence-based psychological frameworks (CBT, DBT, mindfulness-based approaches, trauma-informed care). You are not \
a licensed therapist and you do not diagnose. Your role is to listen actively, validate emotions, help the person \
think through what they're experiencing, and gently draw on the reference material provided below when it's \
genuinely relevant - don't force it in if it doesn't fit the moment.

Be warm, concise, and conversational - not clinical or lecture-y. Ask at most one question at a time. Never claim \
to be a licensed professional. When appropriate, encourage professional support.

{crisis_directive}

{context_block}
"""

CRISIS_DIRECTIVE = f"""IMPORTANT - CRISIS PROTOCOL ACTIVE: This message has been flagged for possible crisis \
content (suicidal ideation or self-harm language). Respond calmly and directly, take it seriously, and clearly \
include these resources in your reply: {crisis.CRISIS_RESOURCE_MESSAGE} Do not minimize what they've shared. \
Stay present and supportive."""

REPORT_PROMPT_TEMPLATE = """You are generating a private end-of-session summary for the person who just finished \
talking with Jane, a supportive listening companion. This is for their own reflection, not a clinical document.

Based on the conversation transcript below, write a warm, honest, well-organized summary covering:
1. The main things they talked about today (2-4 key themes).
2. How their tone/emotional state seemed to shift over the conversation, if at all.
3. Any coping strategies, reframes, or reference material that came up which they might want to revisit.
4. One or two gentle, non-prescriptive suggestions for what might help going forward.

Keep it under 300 words, written directly to the person ("you"), in a caring but plain-spoken tone. Do not \
diagnose. If crisis content came up in the conversation, end the report by repeating the crisis resources clearly.

Transcript:
{transcript}
"""


def _get_or_create_session(db: Session, user: models.User, session_id: int | None) -> models.ChatSession:
    if session_id:
        session = db.query(models.ChatSession).filter(
            models.ChatSession.id == session_id, models.ChatSession.user_id == user.id
        ).first()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        return session

    session = models.ChatSession(user_id=user.id)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@router.post("", response_model=schemas.ChatResponse)
async def chat(
    payload: schemas.ChatRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    session = _get_or_create_session(db, current_user, payload.session_id)

    crisis_detected = crisis.detect_crisis(payload.message)

    retrieval = retrieve_and_format(payload.message, top_k=4)

    context_block = retrieval["context_block"]
    if crisis_detected:
        context_block = (
            f"[CRISIS PROTOCOL REFERENCE FORCE-INCLUDED]\n{crisis.CRISIS_RESOURCE_MESSAGE}\n\n" + context_block
        )

    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
        crisis_directive=CRISIS_DIRECTIVE if crisis_detected else "",
        context_block=context_block or "(No closely matching reference material for this message - respond from general supportive-listening principles.)",
    )

    history = db.query(models.Message).filter(models.Message.session_id == session.id).order_by(
        models.Message.created_at.desc()
    ).limit(10).all()
    history.reverse()
    conversation = [{"role": m.role, "content": m.content} for m in history]
    conversation.append({"role": "user", "content": payload.message})

    try:
        reply_text = await generate_response(system_prompt, conversation)
    except GroqNotConfiguredError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Generation failed: {e}")

    user_msg = models.Message(
        session_id=session.id, role="user", content=payload.message,
        crisis_flag=1 if crisis_detected else 0,
    )
    assistant_msg = models.Message(
        session_id=session.id, role="assistant", content=reply_text,
        retrieved_sources=retrieval["sources"],
    )
    db.add_all([user_msg, assistant_msg])
    db.commit()

    return schemas.ChatResponse(
        session_id=session.id,
        reply=reply_text,
        sources=retrieval["sources"],
        crisis_detected=crisis_detected,
    )


@router.get("/sessions", response_model=list[schemas.SessionOut])
def list_sessions(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    return db.query(models.ChatSession).filter(models.ChatSession.user_id == current_user.id).order_by(
        models.ChatSession.started_at.desc()
    ).all()


@router.post("/sessions/{session_id}/report", response_model=schemas.ReportResponse)
async def generate_session_report(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """
    Generates a human-readable end-of-session report by summarizing the
    full message transcript for this session through the LLM. Real
    generation (not a template fill-in) - the report reflects what was
    actually discussed.
    """
    session = db.query(models.ChatSession).filter(
        models.ChatSession.id == session_id, models.ChatSession.user_id == current_user.id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    messages = db.query(models.Message).filter(models.Message.session_id == session_id).order_by(
        models.Message.created_at.asc()
    ).all()
    if not messages:
        raise HTTPException(status_code=400, detail="This session has no messages yet - nothing to report on.")

    transcript_lines = []
    any_crisis = False
    for m in messages:
        speaker = "You" if m.role == "user" else "Jane"
        transcript_lines.append(f"{speaker}: {m.content}")
        if m.crisis_flag:
            any_crisis = True
    transcript = "\n".join(transcript_lines)

    report_prompt = REPORT_PROMPT_TEMPLATE.format(transcript=transcript)

    try:
        report_text = await generate_response(
            system_prompt="You write clear, kind, well-organized personal reflection summaries.",
            conversation_messages=[{"role": "user", "content": report_prompt}],
            temperature=0.4,
            max_tokens=500,
        )
    except GroqNotConfiguredError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Report generation failed: {e}")

    if any_crisis and crisis.CRISIS_RESOURCE_MESSAGE not in report_text:
        report_text += f"\n\n{crisis.CRISIS_RESOURCE_MESSAGE}"

    now = datetime.datetime.utcnow()
    session.report_text = report_text
    session.report_generated_at = now
    session.ended_at = session.ended_at or now
    db.commit()

    return schemas.ReportResponse(
        session_id=session.id,
        report=report_text,
        generated_at=now,
        message_count=len(messages),
    )
