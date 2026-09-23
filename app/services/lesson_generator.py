from app.models.curriculum import CurriculumData
from app.models.lesson import LessonPlan


def generate_lesson(data: CurriculumData) -> LessonPlan:
    outcomes = data.learning_outcomes or [
        f"Demonstrate understanding of {data.sub_strand or 'the selected concept'}."
    ]

    resources = data.resources or ["Curriculum design document", "Teacher-prepared learning resources"]

    return LessonPlan(
        title=f"{data.learning_area or 'Lesson'}: {data.sub_strand or data.strand or 'Selected Topic'}",
        learning_area=data.learning_area,
        grade=data.grade,
        strand=data.strand,
        sub_strand=data.sub_strand,
        specific_learning_outcomes=outcomes,
        core_competencies=[
            "Communication and Collaboration",
            "Critical Thinking and Problem Solving",
            "Self-Efficacy",
        ],
        values=[
            "Respect",
            "Responsibility",
            "Unity",
        ],
        pcis=[
            "Use the curriculum context to identify relevant Pertinent and Contemporary Issues."
        ],
        resources=resources,
        introduction=(
            "Teacher activates prior knowledge through a short question, observation, "
            "or locally relevant example connected to the sub-strand."
        ),
        development=(
            "Teacher introduces the concept using the curriculum learning outcomes. "
            "Learners work individually, in pairs, or in groups to explore the concept "
            "through guided activities and discussion."
        ),
        learner_activities=(
            "Learners participate actively, explain their thinking, collaborate with peers, "
            "complete the selected task, and present or compare their findings."
        ),
        assessment=(
            "Use oral questioning, observation, learner work, and a short exit task. "
            "Assessment should directly measure the stated learning outcomes."
        ),
        differentiation=(
            "Provide additional scaffolding, examples, peer support, enlarged/alternative "
            "resources, or extension tasks according to learner needs."
        ),
        reflection=(
            "What evidence showed that learners achieved the outcomes? Which learners "
            "need additional support? What should be adjusted in the next lesson?"
        ),
        homework="Provide a short curriculum-aligned practice or observation task where appropriate.",
    )
