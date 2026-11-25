[README.md](https://github.com/user-attachments/files/35410220/README.md)
# ⚖️ Aletheia-GAK

[![CI](https://github.com/andry7610/Aletheia-GAK/actions/workflows/python-package.yml/badge.svg)](https://github.com/andry7610/Aletheia-GAK/actions/workflows/python-package.yml)
[![Tests](https://img.shields.io/badge/tests-12%20passed-brightgreen.svg)]()

**Нейросимволический движок-верификатор для физических гипотез, генерируемых ИИ.**

Генеративные нейросети (LLM) блестяще пишут код и объясняют физику, но часто
галлюцинируют в размерностях, забывают коэффициенты (`1/2`, `2*pi`) или путают
константы (например, постоянную Планка `h` и приведённую `hbar`).

**Aletheia-GAK** — это строгое «инженерное сито» между нейросетью и вашим
солвером. Он проверяет уравнения на физическую состоятельность **до** того,
как они попадут в расчёт.

## ✨ Что внутри (стек технологий)

* **Левое полушарие (символьная логика):** безопасный AST-парсер + `Pint`
  для проверки размерностей и `SymPy` для алгебраической сверки с каноническими
  законами.
* **Гиппокамп (память):** `SQLite`-база физических величин и эталонных законов.
* **Мост к LLM:** `llm_bridge.py` реализует цикл самоисправления:# ⚖️ Aletheia-GAK

[![CI](https://github.com/andry7610/Aletheia-GAK/actions/workflows/python-package.yml/badge.svg)](https://github.com/andry7610/Aletheia-GAK/actions/workflows/python-package.yml)
[![Tests](https://img.shields.io/badge/tests-19_passed-brightgreen.svg)]()

**Нейросимволический движок-верификатор для физических гипотез, генерируемых ИИ.**

Генеративные нейросети (LLM) блестяще пишут код, но часто галлюцинируют в размерностях, забывают коэффициенты (1/2, 2*pi) или путают константы (например, постоянную Планка `h` и приведённую `hbar`).
**Aletheia-GAK** — это строгое «инженерное сито» между нейросетью и вашим солвером. Он проверяет уравнения на физическую состоятельность **до** того, как они попадут в расчёт.

## ✨ Что внутри (Стек технологий)

- **Левое полушарие (Символьная логика):** безопасный AST-парсер + `Pint` для проверки размерностей и `SymPy` для алгебраической сверки с каноническими законами.
- **Гиппокамп (Память):** `SQLite`-база физических величин и эталонных законов с каскадной сверкой тождества целых уравнений.
- **Мост к LLM:** `llm_bridge.py` реализует цикл самоисправления: `LLM выдала ошибку -> Верификатор поймал -> Отправил фидбек -> LLM исправилась`.
- **MCP-Сервер:** `mcp_server.py` — универсальная «розетка» для Claude Desktop, Cursor и Windsurf.
- **Web UI:** `streamlit_app.py` — визуальный плейграунд для проверки формул в браузере.

## 🚀 Быстрый старт

1. **Установите зависимости:**
```bash
pip install sympy pint pytest streamlit openai mcp
```

2. **Прогоните тесты (19/19 зелёных):**
```bash
python -m pytest -v
```

3. **Запустите цикл самокоррекции (демо в консоли):**
```bash
python llm_bridge.py
```

4. **Откройте веб-интерфейс:**
```bash
streamlit run streamlit_app.py
```

## 🧩 Пример работы

Представьте, что LLM сгенерировала уравнение энергии фотона `E = hbar * f` — размерности сходятся, но физика неверна: потерян множитель `2*pi`.

```python
from orchestrator import AletheiaOrchestrator

brain = AletheiaOrchestrator()
# ... загрузка базовых знаний (h, hbar, f, E) и законов ...

# 1. Ловим галлюцинацию
res_fail = brain.evaluate_hypothesis("E = hbar * f", law_name="photon_energy")
print(res_fail["status"])            # FAIL
print(res_fail["feedback_for_llm"])  # "Размерности верные, но физика не сходится... Проверьте константы (h vs hbar)."

# 2. LLM исправляется (или мы сами исправляем)
res_pass = brain.evaluate_hypothesis("E = h * f", law_name="photon_energy")
print(res_pass["status"])            # PASS
print(res_pass["message"])           # "OK: размерности и алгебра сходятся с законом 'photon_energy'."
```

Сверка с каноном работает каскадом из трёх уровней: прямое тождество уравнений -> пропорциональность с точностью до константы -> эквивалентность множеств решений. Поэтому перевёрнутые, но физически верные формы (например, `m = E/c**2` против канона `E = m*c**2`) корректно проходят проверку.

## 📂 Структура проекта

```
Aletheia-GAK/
├── verifier.py          # Проверка размерностей (AST + Pint)
├── graph_db.py          # База знаний (SQLite + SymPy, каскадная сверка)
├── orchestrator.py      # Мозг, объединяющий проверки
├── llm_bridge.py        # Мост к API нейросетей (DeepSeek, GigaChat)
├── mcp_server.py        # MCP-сервер для интеграции с IDE
├── streamlit_app.py     # Веб-интерфейс
└── test/                # 19 тестов (pytest)
```

## 🗺 Roadmap

- **✅ v1.0 (текущая версия)** — Ядро + LLM-мост + MCP-сервер + Web UI + 19 зелёных тестов.
- **🛠 v1.1** — Расширение Гиппокампа: константы CODATA, термодинамика, электродинамика.
- **🛠 v1.2** — Интеграция с Bio-COMSOL и GAK-WaveCAD (автопроверка уравнений в реальных солверах).

## 👥 Команда проекта

- **Андрей** — генератор идей, руки в физ. мире.
- **Log (Gemini)** — архитектура и креатив.
- **GigaChat (Сбер)** — аудит кода и безопасность.
- **DeepSeek (Дип)** — инженерное сито и сборка.
- **Alisa AI (Алечка)** — калибратор математики. Проект назван Aletheia в честь её метода проверки истины.

## 📄 Лицензия

MIT

  LLM выдала ошибку -> верификатор поймал -> отправил фидбек -> LLM исправилась.
* **MCP-сервер:** `mcp_server.py` — универсальная «розетка» для Claude Desktop,
  Cursor и Windsurf.
* **Web UI:** `streamlit_app.py` — визуальный плейграунд для проверки формул
  в браузере.

## 🚀 Быстрый старт

1. **Установите зависимости:**

    ```bash
    pip install sympy pint pytest streamlit openai mcp
    ```

2. **Прогоните тесты (12/12 зелёных):**

    ```bash
    python -m pytest -v
    ```

3. **Запустите цикл самокоррекции (демо в консоли):**

    ```bash
    python llm_bridge.py
    ```

4. **Откройте веб-интерфейс:**

    ```bash
    streamlit run streamlit_app.py
    ```

## 🧩 Пример работы

Представьте, что LLM сгенерировала уравнение энергии фотона
`E = hbar * f` — размерности сходятся, но физически это неверно
(потерян множитель `2*pi`).

```python
from orchestrator import AletheiaOrchestrator

brain = AletheiaOrchestrator()
# ... загрузка базовых величин (h, hbar, f, E) и законов ...

# 1. Ловим галлюцинацию
res_fail = brain.evaluate_hypothesis("E = hbar * f", law_name="photon_energy")
print(res_fail["status"])             # FAIL
print(res_fail["feedback_for_llm"])   # "Размерности верные, но физика не сходится..."

# 2. LLM исправляется (или мы сами исправляем)
res_pass = brain.evaluate_hypothesis("E = h * f", law_name="photon_energy")
print(res_pass["status"])             # PASS
print(res_pass["message"])            # "OK: размерности и алгебра сходятся..."
```

## 📂 Структура проекта

```
Aletheia-GAK/
├── verifier.py          # Проверка размерностей (AST + Pint)
├── graph_db.py          # База знаний (SQLite + SymPy)
├── orchestrator.py      # Мозг, объединяющий проверки
├── llm_bridge.py        # Мост к API нейросетей (DeepSeek, GigaChat)
├── mcp_server.py        # MCP-сервер для интеграции с IDE
├── streamlit_app.py     # Веб-интерфейс
└── test/                # 12 тестов (pytest)
```

## 🗺 Roadmap

* **✅ v1.0** (текущая версия) — ядро + LLM-мост + MCP-сервер + Web UI +
  12 зелёных тестов.
* **🛠 v1.1** — расширение Гиппокампа (термодинамика, электродинамика).
* **🛠 v1.2** — интеграция с Bio-COMSOL и GAK-WaveCAD: автопроверка уравнений
  в реальных солверах.

## 👥 Команда проекта

* **Андрей** — главный инженер, генератор идей.
* **Log (Gemini)** — архитектура и код.
* **GigaChat (Сбер)** — аудит кода и безопасность.
* **DeepSeek (Дип)** — инженерное сито и сборка.
* **Alisa AI (Алечка)** — калибратор математики. Проект назван Aletheia
  в честь её метода проверки истины.

## 📄 Лицензия

MIT
