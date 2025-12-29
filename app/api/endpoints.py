from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from app.schemas import NewsRequest, AgentState
from app.services.workflow import app_graph
import json
import asyncio

router = APIRouter()

@router.post("/analyze")
async def analyze_news(request: NewsRequest):
    print(f"📥 Received request: Topic='{request.topic}', URLs={request.urls}")
    async def event_generator():
        # Initial input for the graph
        initial_state = {"urls": request.urls, "topic": request.topic, "messages": []}
        
        # Stream the graph execution
        # LangGraph stream yields (node_name, state_update)
        try:
            async for event in app_graph.astream(initial_state):
                for node_name, state_update in event.items():
                    # Construct AgentState
                    # In a real app, we might extract more specific content from state_update
                    # Here we just take the last message added
                    messages = state_update.get("messages", [])
                    content = str(messages[-1]) if messages else "Processing..."
                    
                    agent_state = AgentState(
                        agent_name=node_name.capitalize(),
                        step_content=content,
                        status="thinking"
                    )
                    
                    # Yield SSE format
                    yield f"data: {agent_state.model_dump_json()}\n\n"
            
            # Final event
            final_state = AgentState(
                agent_name="System",
                step_content="Analysis Complete",
                status="finished"
            )
            yield f"data: {final_state.model_dump_json()}\n\n"
            
        except Exception as e:
            error_state = AgentState(
                agent_name="System",
                step_content=f"Error: {str(e)}",
                status="error"
            )
            yield f"data: {error_state.model_dump_json()}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
