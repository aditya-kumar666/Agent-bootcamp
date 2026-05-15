from pydantic import BaseModel, Field

class UserTask(BaseModel):
    """Structured user task input for the agent pipeline.
    
    Attributes:
        title: Brief title of the task
        description: Detailed description of what needs to be done
        acceptance_criteria: Explicit criteria that must be met for task success
    """
    title: str = Field(..., min_length=1, description="Task title")
    description: str = Field(..., min_length=1, description="Task description")
    acceptance_criteria: str = Field(..., min_length=1, description="Acceptance criteria")

    class Config:
        """Pydantic config for JSON serialization."""
        json_schema_extra = {
            "example": {
                "title": "Add user authentication",
                "description": "Implement JWT-based authentication for the API",
                "acceptance_criteria": "Users can register, login, and access protected endpoints"
            }
        }
