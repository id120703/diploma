from pydantic import BaseModel, Field, StringConstraints
from typing import List, Optional, Literal, Annotated

StrippedStr = Annotated[str, StringConstraints(strip_whitespace=True)]


class TopicConcept(BaseModel):
    """Ключевая концепция, извлечённая из учебного материала."""
    name: StrippedStr = Field(description="Название концепции/темы")
    bloom_level: Literal[
        "remember", "understand", "apply", "analyze", "evaluate", "create"
    ] = Field(description="Уровень по таксономии Блума")
    weight: float = Field(ge=0.0, le=1.0, description="Вес в тесте (0.0-1.0)")


class QuestionItem(BaseModel):
    """Тестовое задание с метаданными."""
    type: Literal["mcq", "true_false", "open"] = Field(description="Тип вопроса")
    stem: StrippedStr = Field(description="Текст вопроса")
    options: Optional[List[StrippedStr]] = Field(
        default=None, description="Варианты ответа (для mcq)"
    )
    correct_answer: StrippedStr = Field(description="Правильный ответ")
    explanation: StrippedStr = Field(description="Пояснение для студента")
    difficulty: int = Field(ge=1, le=3, description="1=лёгкий, 2=средний, 3=сложный")


class ValidationResult(BaseModel):
    """Результат проверки задания валидатором."""
    status: Literal["approved", "revise"] = Field(description="Результат проверки")
    issues: List[StrippedStr] = Field(
        default_factory=list, description="Список проблем"
    )
    suggestions: List[StrippedStr] = Field(
        default_factory=list, description="Рекомендации по исправлению"
    )



class TopicConceptList(BaseModel):
    """Результат анализа учебного материала."""
    suitable: bool = Field(
        default=True,
        description="Пригоден ли текст для генерации тестов (false если мусор/бессвязный)"
    )
    reason: Optional[StrippedStr] = Field(
        default=None,
        description="Причина непригодности (только если suitable=false)"
    )
    concepts: List[TopicConcept] = Field(
        default_factory=list,
        description="Список извлечённых концепций (пустой если suitable=false)"
    )


class QuestionItemList(BaseModel):
    """Список сгенерированных вопросов."""
    questions: List[QuestionItem] = Field(description="Список тестовых заданий")


class ValidationResultList(BaseModel):
    """Список результатов валидации."""
    validations: List[ValidationResult] = Field(description="Список результатов валидации")