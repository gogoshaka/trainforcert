
from pydantic import BaseModel

class Question(BaseModel):
    question: str
    answers: list[str]
    correct_answer: str
    explanation: str

class Questions(BaseModel):
    questions: list[Question]

class LearningPathQuestions(BaseModel):
    learning_path_title: str
    questions: list[Question]

class CertificationQuestions(BaseModel):
    certification_title: str
    questions: list[LearningPathQuestions]
