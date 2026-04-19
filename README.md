
## 🚀 Запуск проекта

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Запуск краулера

```bash
python main.py
```

---

## 🧪 Запуск тестов

### Все тесты

```bash
pytest -v
```

### С покрытием

```bash
pytest -v --cov=. --cov-report=term-missing --cov-report=html
```

### HTML отчёт

```bash
open htmlcov/index.html
```

---


# Отчёт по тестированию проекта Habr Crawler

## 📊 Результаты запуска pytest

| Всего тестов | Покрытие |
|-------------|----------|
| 29          | 95%      |

---

## 1. Общая оценка результата

Общее покрытие кода составило **95%**. Проверены не только отдельные утилитарные функции, но и сценарии парсинга, сохранения данных, работы очереди frontier, robots.txt, fetcher и сквозной проход движка.

Вначале успешно прошли **27 из 29 тестов**, упавшие тесты указывали на реальные логические дефекты в коде. После внесения исправлений **все тесты были успешно пройдены**.

---

## 2. Что именно покрыто тестами

В текущем наборе тестов проверяются следующие ключевые блоки системы:

- нормализация URL, удаление UTM-параметров и базовая фильтрация ссылок;
- проверка принадлежности URL к внутренним доменам Habr;
- выделение текста, заголовка, метаинформации и ссылок из HTML-страниц;
- работа очереди frontier:
  - выбор следующего URL
  - пропуск задач из будущего
  - повторные попытки
- сохранение Page, Link и FetchAttempt в хранилище;
- работа с seed-URL и сбор статистики;
- учёт robots.txt, ограничение частоты запросов и обработка сетевых ошибок;
- сквозной сценарий `engine.run()` для HTML, non-HTML и ошибочных ответов.

---

## 📊 Покрытие по модулям

| Модуль | Строк кода | Не покрытые строки | Покрытие |
|--------|-----------|-------------------|----------|
| analysis/stats.py | 36 | 0 | 100% |
| config.py | 8 | 0 | 100% |
| crawler/init.py | 0 | 0 | 100% |
| crawler/dedup.py | 33 | 1 | 97% |
| crawler/engine.py | 39 | 3 | 92% |
| crawler/fetcher.py | 53 | 1 | 98% |
| crawler/parser.py | 34 | 0 | 100% |
| crawler/robots.py | 31 | 1 | 97% |
| crawler/scheduler.py | 13 | 0 | 100% |
| crawler/seed.py | 26 | 0 | 100% |
| crawler/storage.py | 70 | 1 | 99% |
| main.py | 28 | 28 | 0% |
| models/init.py | 7 | 0 | 100% |
| models/base.py | 3 | 0 | 100% |
| models/fetch_attempt.py | 15 | 0 | 100% |
| models/frontier.py | 17 | 0 | 100% |
| models/link.py | 14 | 0 | 100% |
| models/page.py | 22 | 0 | 100% |
| models/url.py | 15 | 0 | 100% |
| tests/conftest.py | 25 | 0 | 100% |
| tests/test_dedup.py | 17 | 1 | 94% |
| tests/test_dedup_regressions.py | 14 | 0 | 100% |
| tests/test_parser.py | 20 | 0 | 100% |
| tests/test_robots_fetcher_engine.py | 97 | 2 | 98% |
| tests/test_scheduler_seed_stats.py | 46 | 0 | 100% |
| tests/test_storage.py | 99 | 0 | 100% |
| tests/test_storage_protocol_regressions.py | 5 | 0 | 100% |

---

## 3. Анализ упавших тестов

### 3.1. test_should_not_crawl_foreign_domain_with_habr_like_article_path

**Симптом:**  
URL `https://www.mql5.com/ru/articles/123/` ошибочно проходит через `should_crawl()` как допустимый для обхода.

**Причина:**  
Функция проверяет только `path`, но не валидирует домен и схему.

**Что переработать:**
- `crawler/dedup.py`
- добавить проверку:
  - scheme ∈ {http, https}
  - host ∈ habr.com

**Итог:** баг исправлен.

---

### 3.2. test_get_or_create_url_rejects_xmpp_url_without_host

**Симптом:**  
При обработке URL:

```
xmpp:aveysov@gmail.com/
```

происходит попытка сохранить:

```
Url(
    url="xmpp:aveysov@gmail.com/",
    scheme="xmpp",
    host=None,
    path="aveysov@gmail.com/",
)
```

Ошибка БД:

```
NOT NULL constraint failed: urls.host
```

**Причина:**
- `urlparse()` → `host=None`
- БД требует NOT NULL
- отсутствует валидация URL

**Что переработать:**

- `crawler/dedup.py`
  - фильтрация схем (http/https)

- `crawler/storage.py`
  - проверка `host is None`
  - не делать INSERT
  - выбрасывать ValueError

**Итог:** баг исправлен.

---

## 4. Итог

- Найдены реальные баги
- Добавлены regression-тесты
- Все тесты успешно пройдены