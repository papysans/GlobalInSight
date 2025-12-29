from pydantic import BaseModel
from typing import List, Optional

class NewsRequest(BaseModel):
    urls: List[str]
    topic: str

class AgentState(BaseModel):
    agent_name: str
    step_content: str
    status: str  # 'thinking' | 'finished'
