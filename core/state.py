from typing import List, Optional
from pydantic import BaseModel, Field
from core.schemas import SubTask, EvidenceItem


class ResearchState(BaseModel):
    question: str
    question_type: str = "deep_research"
    round_id: int = 1
    subtasks: List[SubTask] = Field(default_factory=list)
    evidence_pool: List[EvidenceItem] = Field(default_factory=list)
    missing_points: List[str] = Field(default_factory=list)
    final_answer: Optional[str] = None

    def pending_subtasks(self) -> List[SubTask]:
        return [x for x in self.subtasks if x.status == "pending"]

    def mark_running(self, subtask_id: int):
        for task in self.subtasks:
            if task.id == subtask_id:
                task.status = "running"

    def mark_done(self, subtask_id: int):
        for task in self.subtasks:
            if task.id == subtask_id:
                task.status = "done"

    def add_subtasks(self, new_tasks: List[SubTask]):
        existing_ids = {x.id for x in self.subtasks}
        for task in new_tasks:
            if task.id not in existing_ids:
                self.subtasks.append(task)

    def add_evidence(self, items: List[EvidenceItem]):
        self.evidence_pool.extend(items)