import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import StreamingResponse
from config.db_conf import get_db
from schemas.ai import ChatRequest
from services.langchain_service import run_agent, stream_agent, DASHSCOPE_API_KEY

router = APIRouter(prefix="/api/ai", tags=["ai"])

@router.post("/chat")
async def chat(req: ChatRequest, db: AsyncSession = Depends(get_db)):
    if not DASHSCOPE_API_KEY:
        raise HTTPException(status_code=503, detail="AI service not configured")
    if not req.stream:
        reply = await run_agent(db, req.message)
        return {"code": 200, "data": {"reply": reply}}

    async def event_stream():
        try:
            async for chunk in stream_agent(db, req.message):
                yield "data: " + json.dumps({"content": chunk}, ensure_ascii=False) + "\n\n"
        except Exception as e:
            yield "data: " + json.dumps({"error": str(e)}, ensure_ascii=False) + "\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
