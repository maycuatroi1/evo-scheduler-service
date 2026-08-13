from dataclasses import dataclass, field


@dataclass
class Assignment:
    session_id: int
    session_code: str
    timeslot_index: int
    day: int
    period: int
    day_name: str
    resource_code: str
    teacher_codes: list
    auto_assigned_teachers: bool = False


@dataclass
class RulePenalty:
    rule_id: int
    rule_type: str
    hardness: str
    weight: int
    penalty: int
    detail: str = ""


@dataclass
class SolveResult:
    status: str
    objective_value: float
    assignments: list = field(default_factory=list)
    penalties: list = field(default_factory=list)
    violations: list = field(default_factory=list)
    solver_log: str = ""
    num_constraints: int = 0
    num_booleans: int = 0
    wall_time: float = 0.0

    @property
    def is_feasible(self) -> bool:
        return self.status in ("OPTIMAL", "FEASIBLE")
