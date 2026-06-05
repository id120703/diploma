import json
import sys
import logging
from pathlib import Path
from pypdf import PdfReader

import psutil
import tiktoken
import time


from crew_setup import build_crew, create_tasks
from config import MIN_TEXT_LENGTH, MAX_TEXT_LENGTH


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-7s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


class InputValidationError(Exception):
    pass


def load_and_validate_text(filepath: str) -> str:
    path = Path(filepath)


    if not path.exists():
        raise InputValidationError(f"Файл '{filepath}' не найден")
    if not path.is_file():
        raise InputValidationError(f"'{filepath}' не является файлом")

    file_size = path.stat().st_size
    if file_size == 0:
        raise InputValidationError("Файл пустой (0 байт)")
    if file_size > MAX_TEXT_LENGTH * 3:
        raise InputValidationError(
            f"Файл слишком большой ({file_size} байт). "
            f"Максимальный размер: ~{MAX_TEXT_LENGTH} символов."
        )

    ext = path.suffix.lower()
    text = ""

    logger.debug(f"Определён формат файла: {ext or '(без расширения)'}")

    try:
        if ext == ".pdf":
            logger.info("Обнаружен PDF-файл, извлечение текста через pypdf")
            reader = PdfReader(filepath)
            text = "\n".join(page.extract_text() or "" for page in reader.pages)


        elif ext in (".txt", ".md", ".log", ".csv", ""):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    text = f.read()
            except UnicodeDecodeError:
                logger.warning("UTF-8 не сработал, попытка чтения в Windows-1251")
                with open(filepath, "r", encoding="windows-1251") as f:
                    text = f.read()

        else:
            raise InputValidationError(
                f"Неподдерживаемый формат: '{ext}'. "
                f"Используйте .txt, .pdf"
            )

    except InputValidationError:
        raise
    except Exception as e:
        raise InputValidationError(f"Ошибка чтения файла: {e}")


    text = text.strip()
    if len(text) < MIN_TEXT_LENGTH:
        raise InputValidationError(
            f"Текст слишком короткий ({len(text)} символов). "
            f"Минимум: {MIN_TEXT_LENGTH} символов."
        )
    if len(text) > MAX_TEXT_LENGTH:
        raise InputValidationError(
            f"Текст слишком длинный ({len(text)} символов). "
            f"Максимум: {MAX_TEXT_LENGTH}. Разделите материал на части."
        )

    logger.info(f"Файл загружен: {len(text)} символов. Передача в мультиагентную систему.")
    return text

def save_result(result: dict, path: str = "output_test.json"):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    logger.info(f"Результат сохранён в {path}")



def display_questions(questions: list):
    print("\n" + "=" * 70)
    print("УТВЕРЖДЁННЫЕ ТЕСТОВЫЕ ЗАДАНИЯ")
    print("=" * 70)
    for i, q in enumerate(questions, 1):
        print(f"\n🔹 Вопрос {i} [{q['type'].upper()}] (Сложность: {q['difficulty']})")
        print(f"   {q['stem']}")
        if q.get("options"):
            print(f"   Варианты: {', '.join(q['options'])}")
        print(f"   ✅ Ответ: {q['correct_answer']}")
        print(f"   💡 Пояснение: {q['explanation']}")
    print("\n" + "=" * 70)




def run_predefense_demo():
    input_file = "sample_lecture.txt"

    start_time = time.time()
    process = psutil.Process()
    start_ram = process.memory_info().rss
    peak_ram = start_ram


    logger.info(f"Начало работы. Входной файл: {input_file}")
    try:
        text = load_and_validate_text(input_file)
    except InputValidationError as e:
        logger.error(f"Ошибка входных данных: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Непредвиденная ошибка чтения: {e}", exc_info=True)
        sys.exit(1)

    logger.info("Запуск мультиагентной цепочки (3 агента)...")
    try:
        tasks = create_tasks(text)
        crew = build_crew(text)
        result = crew.kickoff()
    except ConnectionError:
        logger.error(
            "Не удалось подключиться к Ollama. "
            "Убедитесь, что сервер запущен: ollama serve"
        )
        sys.exit(1)
    except TimeoutError:
        logger.error(
            "Превышено время ожидания ответа от модели. "
            "Попробуйте более короткий текст."
        )
        sys.exit(1)
    except Exception as e:
        logger.error(f"Ошибка выполнения CrewAI: {e}", exc_info=True)
        sys.exit(1)

    try:
        concepts_wrapper = result.tasks_output[0].pydantic
        questions_wrapper = result.tasks_output[1].pydantic
        validation_wrapper = result.tasks_output[2].pydantic

        if not concepts_wrapper.suitable:
            logger.warning(
                f"Агент-аналитик отклонил материал: {concepts_wrapper.reason}"
            )
            print(f"\n⚠️ Материал не подходит для генерации тестов.")
            print(f"Причина: {concepts_wrapper.reason}")
            sys.exit(1)

        logger.info("Агент-аналитик подтвердил пригодность материала.")

        concepts = [c.model_dump() for c in concepts_wrapper.concepts]
        questions = [q.model_dump() for q in questions_wrapper.questions]
        validations = [v.model_dump() for v in validation_wrapper.validations]

        if len(concepts) == 0:
            logger.warning(
                "Агент-аналитик не выделил ни одной концепции. "
                "Возможно, материал слишком общий или абстрактный."
            )
            sys.exit(1)

        logger.info(f"Извлечено концепций: {len(concepts)}")
        logger.info(f"Сгенерировано вопросов: {len(questions)}")


        if len(questions) != len(validations):
            logger.warning(
                f"Рассинхрон данных: сгенерировано {len(questions)} вопросов, "
                f"но получено {len(validations)} результатов валидации. "
                f"Обрабатываются только первые {min(len(questions), len(validations))} элементов."
            )
            min_len = min(len(questions), len(validations))
            questions = questions[:min_len]
            validations = validations[:min_len]

        approved_questions = [
            q for q, v in zip(questions, validations)
            if v["status"] == "approved"
        ]

        if len(approved_questions) == 0:
            logger.warning(
                "Ни один вопрос не прошёл валидацию. "
                "Сохранение отладочных данных в output_debug.json"
            )
            save_result({
                "error": "no_approved_questions",
                "generated_questions": questions,
                "validation_summary": validations,
                "concepts": concepts
            }, path="output_debug.json")
            sys.exit(1)

        logger.info(
            f"Финальная статистика: "
            f"утверждено {len(approved_questions)} из {len(questions)} вопросов"
        )

        display_questions(approved_questions)

        save_result({
            "approved_questions": approved_questions,
            "total_generated": len(questions),
            "validation_summary": validations,
            "concepts": concepts
        })

        end_time = time.time()
        end_ram = process.memory_info().rss
        peak_ram = max(peak_ram, end_ram)

        duration_sec = round(end_time - start_time, 2)
        peak_ram_mb = round(peak_ram / (1024 * 1024), 2)

        try:
            encoder = tiktoken.get_encoding("cl100k_base")
            input_tokens = len(encoder.encode(text))
            output_text = json.dumps({
                "concepts": concepts,
                "questions": questions,
                "validations": validations
            }, ensure_ascii=False)
            output_tokens = len(encoder.encode(output_text))
            total_tokens = input_tokens + output_tokens
        except Exception:
            input_tokens = output_tokens = total_tokens = None
            logger.warning("Не удалось подсчитать токены (tiktoken недоступен)")

        logger.info("=" * 60)
        logger.info(" МЕТРИКИ ВЫПОЛНЕНИЯ")
        logger.info("=" * 60)
        logger.info(f"  Общее время выполнения: {duration_sec} сек")
        logger.info(f" Пиковое потребление RAM: {peak_ram_mb} МБ")
        if total_tokens is not None:
            logger.info(f" Токены входного текста: {input_tokens}")
            logger.info(f" Токены выходного JSON: {output_tokens}")
            logger.info(f" Всего токенов: {total_tokens}")
        logger.info("=" * 60)


        logger.info("✅ Успешное завершение работы системы")

    except AttributeError as e:
        logger.error(
            f"Ошибка доступа к результатам: {e}. "
            f"Модель вернула неожиданный формат."
        )
        sys.exit(1)
    except Exception as e:
        logger.error(f"Непредвиденная ошибка парсинга: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    try:
        run_predefense_demo()
    except KeyboardInterrupt:
        logger.warning("Выполнение прервано пользователем (Ctrl+C)")
        sys.exit(130)