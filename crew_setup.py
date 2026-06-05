import logging
from crewai import Agent, Task, Crew, Process, LLM
from models import TopicConceptList, QuestionItemList, ValidationResultList
from config import OLLAMA_MODEL, OLLAMA_BASE_URL, TEMPERATURE, SEED


logger = logging.getLogger(__name__)


logger.info(f"Инициализация LLM: модель={OLLAMA_MODEL}, температура={TEMPERATURE}")

llm = LLM(
    model=f"ollama/{OLLAMA_MODEL}",
    base_url=OLLAMA_BASE_URL,
    temperature=TEMPERATURE,
    seed=SEED
)


analyzer = Agent(
    role="Методист-аналитик учебных материалов",
    goal="Извлечь ключевые концепции и сопоставить их с таксономией Блума",
    backstory="Вы преподаватель с 10-летним опытом разработки КИМ. "
              "Умеете выделять суть и ранжировать по сложности.",
    llm=llm,
    allow_delegation=False,
    verbose=False
)

designer = Agent(
    role="Разработчик тестовых заданий",
    goal="Создать однозначные вопросы с корректными ответами и пояснениями",
    backstory="Вы эксперт по педагогическим измерениям. "
              "Знаете, как формулировать вопросы без двусмысленностей.",
    llm=llm,
    allow_delegation=False,
    verbose=False
)

validator = Agent(
    role="Контролёр качества КИМ",
    goal="Проверить задания на однозначность и соответствие материалу",
    backstory="Вы член аттестационной комиссии. "
              "Строги, но справедливы. Возвращаете на доработку при малейших сомнениях.",
    llm=llm,
    allow_delegation=False,
    verbose=False
)


def create_tasks(document_text: str) -> list[Task]:
    logger.info(f"Создание задач для {len(document_text)} символов текста")

    task_analyze = Task(
        description=(
            f"Проанализируй учебный материал и оцени его пригодность для генерации тестов.\n\n"
            f"ШАГ 1: Оцени пригодность (поле 'suitable'):\n"
            f"- true: если текст содержит учебный материал с предметными знаниями\n"
            f"- false: если текст бессвязный, состоит из повторяющихся символов, "
            f"не содержит предметного содержания или слишком абстрактный\n\n"
            f"ШАГ 2: Если suitable=true, выдели 5 ключевых концепций.\n"
            f"Если suitable=false, верни пустой список concepts и объясни причину в поле reason.\n\n"
            f"МАТЕРИАЛ:\n{document_text}"
        ),
        expected_output="Оценка пригодности и список концепций (если текст пригоден).",
        agent=analyzer,
        output_pydantic=TopicConceptList
    )

    task_design = Task(
        description=(
            "Сгенерируй по 1 вопросу на каждую извлечённую концепцию, на русском языке. "
            "Соблюдай тип, сложность и пояснения."
        ),
        expected_output="Список тестовых заданий в строгом формате.",
        agent=designer,
        output_pydantic=QuestionItemList,
        context=[task_analyze]
    )

    task_validate = Task(
        description=(
            "Проверь каждое задание на однозначность, корректность ответа "
            "и соответствие материалу. Верни status: approved или revise."
        ),
        expected_output="Список результатов валидации по каждому вопросу.",
        agent=validator,
        output_pydantic=ValidationResultList,
        context=[task_design]
    )

    return [task_analyze, task_design, task_validate]


def build_crew(document_text: str) -> Crew:
    logger.info("Сборка мультиагентной системы (3 агента, sequential process)")
    tasks = create_tasks(document_text)
    return Crew(
        agents=[analyzer, designer, validator],
        tasks=tasks,
        process=Process.sequential,
        verbose=True
    )