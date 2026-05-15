from typing import Optional
from pydantic import BaseModel

class AgentResult(BaseModel):
    """Structured result from an agent execution."""
    success: bool
    output: str
    error: Optional[str] = None
