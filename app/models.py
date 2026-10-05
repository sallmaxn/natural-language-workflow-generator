from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


StepType = Literal["api", "tool", "transform", "validation", "condition", "approval", "error_handler"]


class WorkflowStep(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    type: StepType
    action: Optional[str] = None
    condition: Optional[str] = None
    approver: Optional[str] = None
    input: Dict[str, Any] = Field(default_factory=dict)
    on_success: Optional[str] = None
    on_failure: Optional[str] = None

    @field_validator("id", "on_success", "on_failure", mode="before")
    @classmethod
    def normalize_step_references(cls, value):
        # Models may emit JSON numbers for IDs; normalize IDs and their edges identically.
        if isinstance(value, int) and not isinstance(value, bool):
            return str(value)
        return value


class Workflow(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=120)
    description: Optional[str] = None
    steps: List[WorkflowStep] = Field(min_length=1)
