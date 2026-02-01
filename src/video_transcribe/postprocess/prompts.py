"""Built-in prompt presets for post-processing."""

from pathlib import Path
from dataclasses import dataclass
from enum import Enum

from video_transcribe.postprocess.exceptions import PromptTemplateError


class PromptPreset(str, Enum):
    """Available prompt presets."""
    MEETING = "meeting"
    SCREENCAST = "screencast"


@dataclass
class PromptTemplate:
    """Prompt template with system and user parts.

    Attributes:
        system: System prompt for LLM.
        user: User prompt template with placeholders.
    """
    system: str
    user: str


PRESETS: dict[PromptPreset, PromptTemplate] = {
    PromptPreset.MEETING: PromptTemplate(
        system="""Ты - профессиональный ассистент для создания сводок IT встреч.

Твоя задача:
- Определить участников по упоминаниям в диалоге
- Выделить ключевые темы (не более 5)
- Извлечь конкретные решения
- Найти action items с ответственными и сроками
- Очистить текст от мусора (слова-паразиты, повторения)

ВАЖНО: Различай участников и упомянутых лиц:
- Участники — только те, кто ГОВОРИЛ на встрече (есть в секции информации о спикерах)
- Упомянутые — те, о ком говорили, но не присутствовали

В секцию "Участники" включай только тех, кто реально говорил.
Участников НЕ может быть больше, чем обнаружено спикеров.

Пиши на русском языке. Используй markdown форматирование.""",

        user="""Создай структурированную сводку IT встречи на основе следующего транскрипта.

**Информация о транскрипте:**
- Модель: {model}
- Длительность: {duration} секунд ({duration_minutes:.1f} минут)

**Информация о спикерах:**
{speakers_info}

**Транскрипт:**
```
{transcript}
```

**Формат вывода (строго следуй структуре):**

```markdown
## Сводка встречи

**Модель:** {model}
**Длительность:** {duration_formatted}
**Дата:** {date}

---

### Участники
(список участников, определи по контексту)

### Обсуждаемые темы
- Тема 1 — краткое описание
- Тема 2 — краткое описание
- ...

### Ключевые решения
- Решение 1
- Решение 2

### Action Items
| Кто | Что | Срок |
|-----|-----|------|
| ... | ... | ... |

### Следующие шаги
- Шаг 1
- Шаг 2

### Открытые вопросы
- Вопрос 1
- Вопрос 2
```

Определи участников на основе транскрипта.
ВАЖНО: Количество участников НЕ должно превышать количество обнаруженных спикеров.

Извлеки максимум пользы из текста. Не выдумывай информацию, которой нет в транскрипте."""
    ),

    PromptPreset.SCREENCAST: PromptTemplate(
        system="""Ты - ассистент для преобразования скринкастов в структурированные текстовые туториалы.

Твоя задача:
- Убрать слова-паразиты, повторы, всякие "эээ", "ммм", "короче"
- Структурировать свободную речь в логические блоки
- Сформировать понятные заголовки для каждого этапа
- Составить вступление, объясняющее суть видео
- Добавить резюме с ключевыми выводами

Текст должен быть читабельным и полезным для самостоятельного изучения.""",

        user="""Преобразуй транскрипт скринкаста в структурированный туториал.

**Информация о транскрипте:**
- Модель: {model}
- Длительность: {duration} секунд ({duration_minutes:.1f} минут)

**Транскрипт:**
```
{transcript}
```

**Формат вывода (строго следуй структуре):**

```markdown
# [Придумай понятное название на основе содержания]

> Скринкаст, длительность: {duration_formatted}

## О чем это видео
{{Вступительный блок 2-4 предложения, объясняющие суть видео и для кого оно}}

---

## Содержание

### Шаг 1: [Ясный заголовок первого этапа]
{{Описание первого блока контента без слов-паразитов, в повествовательном стиле}}

### Шаг 2: [Ясный заголовок второго этапа]
{{Описание второго блока контента}}

... (продолжай для всех логических блоков)

## Резюме
{{2-3 предложения с ключевыми выводами — что зритель должен был вынести из видео}}
```

Текст должен быть чистым, структурированным и готовым к чтению."""
    ),
}


def get_preset(preset: PromptPreset) -> PromptTemplate:
    """Get prompt template by preset name.

    Args:
        preset: Preset identifier.

    Returns:
        PromptTemplate with system and user prompts.

    Raises:
        KeyError: If preset not found.
    """
    return PRESETS[preset]


def list_presets() -> list[str]:
    """Return list of available preset names.

    Returns:
        List of preset name strings.
    """
    return [p.value for p in PromptPreset]


def load_prompt_file(path: str) -> PromptTemplate:
    """Load custom prompt from markdown file with YAML frontmatter.

    Args:
        path: Path to custom prompt file.

    Returns:
        PromptTemplate with system and user prompts.

    Raises:
        PromptTemplateError: If file format is invalid or {transcript} is missing.

    File format:
        ---
        system: |
          System prompt here
        ---

        User prompt with {transcript} placeholder
    """
    content = Path(path).read_text(encoding="utf-8")

    # Parse frontmatter
    if not content.startswith("---"):
        raise PromptTemplateError(
            "❌ Prompt file must start with --- frontmatter\n"
            "   Format:\n"
            "   ---\n"
            "   system: |\n"
            "     Your system prompt\n"
            "   ---\n"
            "   Your user prompt with {transcript}"
        )

    parts = content.split("---", 2)
    if len(parts) < 3:
        raise PromptTemplateError(
            "❌ Invalid frontmatter format\n"
            "   File must contain exactly two --- delimiters"
        )

    import yaml
    frontmatter = yaml.safe_load(parts[1]) or {}
    user = parts[2].strip()

    system = frontmatter.get("system", "")

    # Validate required placeholders
    if "{transcript}" not in user:
        raise PromptTemplateError(
            "❌ Missing required placeholder: {transcript}\n"
            "   Add {transcript} to your prompt file."
        )

    return PromptTemplate(system=system, user=user)
