OLLAMA_MODEL = "qwen2.5:7b"
OLLAMA_BASE_URL = "http://localhost:11434"


TEMPERATURE = 0.1
SEED = 41
MAX_RETRY = 2


MIN_TEXT_LENGTH = 50
MAX_TEXT_LENGTH = 50_000


def validate_config():
    if not (0.0 <= TEMPERATURE <= 1.0):
        raise ValueError(
            f"Недопустимая температура: {TEMPERATURE}. Должна быть в диапазоне [0.0, 1.0]"
        )
    if not OLLAMA_BASE_URL.startswith("http"):
        raise ValueError(
            f"Некорректный URL Ollama: {OLLAMA_BASE_URL}. Должен начинаться с 'http'"
        )
    if MAX_RETRY < 0:
        raise ValueError("MAX_RETRY не может быть отрицательным")
    if MIN_TEXT_LENGTH >= MAX_TEXT_LENGTH:
        raise ValueError(
            f"MIN_TEXT_LENGTH ({MIN_TEXT_LENGTH}) должен быть меньше MAX_TEXT_LENGTH ({MAX_TEXT_LENGTH})"
        )

validate_config()