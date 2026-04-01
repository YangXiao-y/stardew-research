from typing import List, Literal, Optional
from pydantic import BaseModel, Field


QuestionType = Literal["knowledge_qa", "strategy_qa", "deep_research"]


class RouteResult(BaseModel):
    question_type: QuestionType


class SubTask(BaseModel):
    id: int
    task: str
    intent: str
    status: Literal["pending", "running", "done", "failed"] = "pending"
    round_id: int = 1


class SearchPlan(BaseModel):
    subtask_id: int
    search_queries: List[str] = Field(default_factory=list)
    preferred_sources: List[str] = Field(default_factory=list)
    search_focus: List[str] = Field(default_factory=list)


class SearchResultItem(BaseModel):
    title: str
    link: str
    snippet: str = ""


class EvidenceItem(BaseModel):
    subtask_id: int
    source_type: Literal["wiki", "guide", "forum", "other"]
    title: str
    url: str
    snippet: str
    evidence_role: Literal["fact", "strategy", "constraint", "tradeoff"]
    confidence: float = 0.7


class GapAnalysis(BaseModel):
    enough: bool
    missing_points: List[str] = Field(default_factory=list)
    new_subtasks: List[SubTask] = Field(default_factory=list)


class FinalReport(BaseModel):
    conclusion: str
    analysis: str
    phased_suggestions: str
    cautions: str