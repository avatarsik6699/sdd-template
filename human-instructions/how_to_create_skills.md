## Как добавить свои skills в Claude Code

**Skills** — это кастомные slash-команды вида `/my-skill`. Каждый skill — файл `SKILL.md` в специальной папке.

---

### Где размещать

| Область              | Путь                              |
|----------------------|-----------------------------------|
| Личные (все проекты) | `~/.claude/skills/<имя>/SKILL.md` |
| Проект               | `.claude/skills/<имя>/SKILL.md`   |

---

### Минимальный пример

Создайте `~/.claude/skills/code-review/SKILL.md`:

```markdown
---
name: code-review
description: Проверить код на качество и безопасность. Используй при code review.
---

Проведи code review для $ARGUMENTS:
1. Проверь безопасность
2. Найди потенциальные баги
3. Оцени читаемость
4. Предложи улучшения
```

Использование: `/code-review src/auth.py`

---

### Ключевые поля frontmatter

| Поле | Описание |
|---|---|
| `name` | Имя для `/slash-команды` |
| `description` | Когда Claude должен сам предлагать skill |
| `disable-model-invocation: true` | Только ручной вызов (для `/commit`, `/deploy`) |
| `allowed-tools` | Инструменты без запроса разрешения (напр. `Bash Grep`) |
| `argument-hint` | Подсказка аргументов в UI |

---

### Динамический контент

Используйте `` !`команда` `` — выполнится до отправки Claude:

```markdown
---
name: pr-review
allowed-tools: Bash(gh *)
---

PR diff: !`gh pr diff`

Проанализируй эти изменения...
```

---

### Важные нюансы

- **`description`** определяет, когда Claude автоматически предложит skill — пишите конкретно
- Если skill срабатывает слишком часто — добавьте `disable-model-invocation: true`
- Skills обнаруживаются автоматически после сохранения файла, без перезапуска