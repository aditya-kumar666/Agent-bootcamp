from pydantic import BaseModel

class AgentResult(BaseModel):
    agent: str
    output: str
