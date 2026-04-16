Как именно настроить vs code, чтобы он поддерживал работу в том случае, если я запускаю всё окружение в докер контейнерах?
---

## Подход 1: Локальные зависимости для IDE (проще)

VS Code остаётся локальным, но для IntelliSense нужны локальные копии зависимостей.

**Backend (Python):**
```bash
# В корне проекта
uv sync --dev
```
Затем в VS Code: `Ctrl+Shift+P` → `Python: Select Interpreter` → выбрать `.venv/bin/python`.

**Frontend (Node):**
```bash
cd frontend && pnpm install
```
VS Code подхватит `node_modules` автоматически через `tsconfig.json`.

Этот подход достаточен для 90% случаев — IntelliSense, go-to-definition, type-checking работают локально, а запуск — в Docker.

---

## Подход 2: Dev Containers (полное погружение)

VS Code подключается **внутрь контейнера** — весь инструментарий (терминал, расширения, отладчик) работает прямо там.

Нужно расширение [Dev Containers](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers) и файл `.devcontainer/devcontainer.json`.

---

## Минимальный набор расширений VS Code для твоего стека

| Расширение | Для чего |
|---|---|
| `ms-python.python` | Python IntelliSense, выбор интерпретатора |
| `ms-python.mypy-type-checker` | mypy прямо в редакторе |
| `charliermarsh.ruff` | ruff linting/formatting inline |
| `Vue.volar` | Nuxt/Vue 3 поддержка |
| `ms-vscode-remote.remote-containers` | если захочешь Подход 2 |

---

Для простого проекта достаточно запустить `uv sync --dev` и `pnpm install` локально — всё остальное VS Code найдёт сам.