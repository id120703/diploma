ШАГ 1: Установка Ollama

Windows: 
1. Скачайте установщик с [официального сайта](https://ollama.com/download)
2. Запустите '.exe' и следуйте инструкциям
3. Перезагрузите компьютер (если потребуется)

MacOS:
brew install Ollama

Linux:
curl -fsSL https://ollama.com/install.sh | sh

Или скачайте .zip с официального сайта

Проверка установки: ollama --version

ШАГ 2: Установка модели

Откройте терминал и выполните: ollama pull qwen2.5:7b-instruct

Проверка установки модели: ollama list(в списке будут представлены все установленные модели)

ШАГ 3: Запуск Ollama Server

Откройте терминал и выполните: ollama run qwen2.5:7b

Проверка запуска сервера: откройте второе окно терминала и выполните ollama ps(в списке будут представлены запущенные модели)

ШАГ 4: Клонирование репозитория

ШАГ 5: Создание виртуального окружения :

Windows: 
python -m venv .venv
.venv\Scripts\activate

Linux/MacOS:
python3 -m venv .venv
source .venv/bin/activate

ШАГ 6: Установка зависимостей

pip install --upgrade pip
pip install -r requirements.txt

ШАГ 7: Запуск
Поддерживаемые форматы: txt, pdf

Изначально программа ищет .txt файл, он должен находиться в корне проекта, иметь название sample_lecture.txt. Эти параметры(название файла и формат txt/pdf) можно изменить в main.py строка 118

Убедитесь, что документ содержит до 50.000 символов

Запустить: python main.py

Ожидаемый вывод: INFO logs, логи работы агентов, результат в json формате в корне проекта

Возможные проблемы и их решения:

ConnectionError: не удалось подключиться к Ollama: Запустить сервер вручную командой ollama serve

FileNotFoundError: sample_lecture.txt: Файл с учебным материалом отсутсвует, создайте файл sample_lecture.txt в корне проекта или измените имя в main.py строка 118

ModuleNotFoundError: No module named 'crewai'(или другой модуль): не установлен модуль или не активировано виртуальное окружение. Проверить активацию .venv, установить недостающие модули вручную pip install "module_name"

ollama: command not found: Ollama не установлена или не добавлена в PATH
Windows: Перезапустите терминал или добавьте C:\Users\ВАШ_USER\AppData\Local\Programs\Ollama в PATH
macOS/Linux: export PATH="$PATH:/usr/local/bin"

UnicodeDecodeError: can't decode byte: Файл в нестандартной кодировке: Система автоматически пробует UTF-8 и Windows-1251. Если ошибка остаётся — сохраните файл в UTF-8 через текстовый редактор.

Агент-аналитик отклонил материал: Текст не содержит осмысленного учебного материала.

Очень медленная работа (>10 минут): Работа на CPU со слабой производительностью
Закройте лишние приложения для освобождения RAM
Убедитесь, что модель загружена: ollama list
Проверьте доступную память: должно быть минимум 6 ГБ свободно 

Model 'qwen2.5:7b-instruct' not found: Модель не скачана: 
ollama pull qwen2.5:7b-instruct
ollama list  (Проверьте, что модель появилась)

ТЕСТИРОВАНИЕ:
Тестирование производилось на процессоре i5 12600K, 16GB RAM
Потребление ресурсов составило: ~4GB RAM, время выполнения ~60сек
А так же, на процессоре i3 14100, 8GB RAM
Потребление ресурсов для этой машины составило: ~4.5GB RAM, время выполнения ~115сек


ДОПОЛНИТЕЛЬНЫЕ РЕСУРСЫ
docs.crewai.com
github.com/ollama/ollama
docs.pydantic.dev/latest
qwenlm.github.io/blog/qwen2.5/
