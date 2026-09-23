from pydantic import BaseModel, Field


class LessonPlan(BaseModel):
    title: str = ""
    learning_area: str = ""
    grade: str = ""
    strand: str = ""
    sub_strand: str = ""
    duration: str = "40 minutes"
    specific_learning_outcomes: list[str] = Field(default_factory=list)
    core_competencies: list[str] = Field(default_factory=list)
    values: list[str] = Field(default_factory=list)
    pcis: list[str] = Field(default_factory=list)
    resources: list[str] = Field(default_factory=list)
    introduction: str = ""
    development: str = ""
    learner_activities: str = ""
    assessment: str = ""
    differentiation: str = ""
    reflection: str = ""
    homework: str = ""
