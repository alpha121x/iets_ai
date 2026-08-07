from app.models.ielts import IELTSLesson, IELTSResult, PracticeAttempt, WritingSubmission
from app.models.transcript import Transcript
from app.models.university import University, UniversityProgram
from app.models.user import User

__all__ = [
    "User",
    "IELTSResult",
    "WritingSubmission",
    "IELTSLesson",
    "PracticeAttempt",
    "Transcript",
    "University",
    "UniversityProgram",
]
