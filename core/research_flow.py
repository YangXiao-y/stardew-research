from config import settings
from core.state import ResearchState
from agents.router import RouterAgent
from agents.planner import PlannerAgent
from agents.research_planner import ResearchPlannerAgent
from agents.critic import CriticAgent
from agents.writer import WriterAgent
from tools.serper_search import serper_search
from tools.web_reader import fetch_page_text
from tools.evidence_extractor import EvidenceExtractor


class DeepResearchFlow:
    def __init__(self):
        self.router = RouterAgent()
        self.planner = PlannerAgent()
        self.research_planner = ResearchPlannerAgent()
        self.critic = CriticAgent()
        self.writer = WriterAgent()
        self.extractor = EvidenceExtractor()

    def run(self, question: str) -> ResearchState:
        route = self.router.run(question)
        state = ResearchState(question=question, question_type=route.question_type)

        # 非 deep_research 也先复用同一套流程，但任务更少
        if route.question_type == "deep_research":
            state.subtasks = self.planner.run(question)
        else:
            state.subtasks = self.planner.run(question)[:2]

        next_task_id = max(x.id for x in state.subtasks) + 1 if state.subtasks else 1

        for round_id in range(1, settings.MAX_RESEARCH_ROUNDS + 1):
            state.round_id = round_id

            pending = state.pending_subtasks()
            if not pending:
                break

            for subtask in pending:
                state.mark_running(subtask.id)

                search_plan = self.research_planner.run(question, subtask)

                all_evidence = []
                for query in search_plan.search_queries[:2]:
                    search_results = serper_search(query, num=settings.MAX_SEARCH_RESULTS)

                    for item in search_results[:settings.MAX_PAGE_PER_SUBTASK]:
                        try:
                            page_text = fetch_page_text(item.link)
                            evs = self.extractor.run(
                                subtask=subtask,
                                title=item.title,
                                url=item.link,
                                page_text=page_text
                            )
                            all_evidence.extend(evs)
                        except Exception:
                            continue

                state.add_evidence(all_evidence)
                state.mark_done(subtask.id)

            gap_result = self.critic.run(
                question=question,
                subtasks=state.subtasks,
                evidence_pool=[x.model_dump() for x in state.evidence_pool],
                next_task_id_start=next_task_id
            )

            state.missing_points = gap_result.missing_points

            if gap_result.enough:
                break

            if gap_result.new_subtasks:
                state.add_subtasks(gap_result.new_subtasks)
                next_task_id = max(x.id for x in state.subtasks) + 1

        state.final_answer = self.writer.run(
            question=question,
            subtasks=[x.model_dump() for x in state.subtasks],
            evidence_pool=[x.model_dump() for x in state.evidence_pool]
        )

        return state