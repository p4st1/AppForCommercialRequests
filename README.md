# AppForCommercialRequests

Desktop-приложение на `PySide6` для подготовки коммерческих предложений, ведения базы клиентов и экспорта документов (`.docx`/`.xlsx`).

## Основные возможности
- Работа с табличными данными позиций КП.
- Расчет формул и параметров (логистика, наценка, сроки).
- Экспорт коммерческих предложений в `DOCX` и таблиц в `XLSX`.
- История созданных предложений в SQLite.
- Управление клиентами и поиск потенциальных дублей.
- Импорт/экспорт базы данных из интерфейса.

## Технологии
- Python 3.10+
- PySide6
- SQLite (`sqlite3`)
- pandas / openpyxl / python-docx

## Быстрый старт
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 run.py
```

## Тесты
```bash
python3 -m unittest discover -s tests -v
```

## Санитайзер файлов
В проект добавлен скрипт санитизации текстовых файлов:

```bash
bash scripts/sanitize_files.sh
```

Что делает санитайзер:
- убирает UTF-8 BOM в начале файла;
- приводит окончания строк к `LF`;
- удаляет хвостовые пробелы/табы в строках;
- добавляет финальный перенос строки в непустых файлах.

Обрабатываются типичные текстовые файлы проекта (`.py`, `.md`, `.txt`, `.json`, `.ui`, `.yml/.yaml`, `.toml`, `.ini`, `.cfg`, `.spec`, `.gitignore`, `.gitattributes`).

## Сборка приложения
```bash
pyinstaller myapp.spec
```

## GitHub Release
В проекте настроен workflow `.github/workflows/release.yml`, который собирает релизные архивы для:
- Windows
- macOS arm64
- macOS x86_64

Пайплайн запускается автоматически при пуше тега формата `v*` (например, `v2.0.0`) или вручную через `workflow_dispatch`.

Перед релизом:
1. Обновите `assets/updates.txt` и `CHANGELOG.md`.
2. Проверьте тесты:
   ```bash
   python3 -m unittest discover -s tests -v
   ```
3. Закоммитьте изменения и запушьте ветку.

Публикация релиза:
```bash
git tag -a v2.0.0 -m "Release v2.0.0"
git push origin v2.0.0
```

После пуша тега GitHub Actions соберёт архивы и создаст релиз в разделе `Releases`.

## Структура проекта
- `run.py` - точка входа приложения.
- `main.py` - основное окно и бизнес-логика интерфейса.
- `database.py` - работа с SQLite и миграции таблиц.
- `tools.py` - утилиты (формулы, конфиг, логи, файловые операции).
- `create.py` / `createDocument.py` - экспорт документов и подготовка данных.
- `tests/` - автотесты.
- `ui/`, `templates/`, `assets/`, `utilities/` - ресурсы и шаблоны.

## Где хранятся пользовательские данные
При запуске приложение копирует рабочие файлы (конфиг, БД, шаблоны) в пользовательскую директорию `MyApp`:
- macOS: `~/Library/Application Support/MyApp`
- Windows: `%APPDATA%/MyApp`
- Linux: `~/.local/share/MyApp`

Если системная директория недоступна, используется fallback: `.appdata/MyApp` в текущем проекте.
