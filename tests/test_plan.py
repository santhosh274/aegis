from core.analyze.utility_ranker import CandidateAction
from core.plan.planner import Planner


def test_planner_uses_utility_only_for_action_selection():
    selected = Planner().choose_next([
        CandidateAction("low", 0.1, 0.1, 0.9, 0.9),
        CandidateAction("high", 0.9, 0.9, 0.1, 0.1),
    ])
    assert selected.name == "high"
