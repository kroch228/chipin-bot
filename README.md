# Chipin 💸

> Бот для разделения расходов в групповых чатах Telegram.

[![CI](https://github.com/kroch228/chipin-bot/actions/workflows/ci.yml/badge.svg)](https://github.com/kroch228/chipin-bot/actions)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![aiogram 3.x](https://img.shields.io/badge/aiogram-3.x-blue.svg)](https://docs.aiogram.dev/)

---

## Демо

```
Вы:     /add 1500 ужин @alice @bob
Chipin: ✅ ужин — 1500.00
        Оплатил: @you
        Участники: 3 чел. по 500.00 каждый

Вы:     /balance
Chipin: 📊 Балансы:
          @you: +1000.00
          @alice: -500.00
          @bob: -500.00

Вы:     /settle
Chipin: 💸 Оптимальные переводы:
          @alice → @you: 500.00
          @bob → @you: 500.00
```

---

## Возможности

- Добавление расходов с произвольным числом участников
- Автоматический расчёт долей (равное разделение)
- Просмотр текущих балансов группы
- Оптимальный алгоритм погашения долгов (минимум переводов)
- Закрытие периода расчётов
- Поддержка нескольких групп одновременно
- Асинхронная архитектура (aiogram 3 + SQLAlchemy async)
- Health-check endpoint для мониторинга
- Docker-ready с автоматическими миграциями

---

## Быстрый старт (Docker)

```bash
git clone https://github.com/kroch228/chipin-bot.git
cd chipin-bot
cp .env.example .env
# Вставьте BOT_TOKEN от @BotFather в .env
docker compose up -d
```

Бот запустится, применит миграции и начнёт polling.

## Быстрый старт (без Docker)

```bash
git clone https://github.com/kroch228/chipin-bot.git
cd chipin-bot
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]" aiohttp
cp .env.example .env
# Вставьте BOT_TOKEN в .env
alembic upgrade head
python -m bot.main
```

---

## Конфигурация

| Переменная | По умолчанию | Описание |
|---|---|---|
| `BOT_TOKEN` | — (обязательно) | Токен бота от @BotFather |
| `DATABASE_URL` | `sqlite+aiosqlite:///data/chipin.db` | URL базы данных (SQLAlchemy async) |
| `LOG_LEVEL` | `INFO` | Уровень логирования (DEBUG, INFO, WARNING, ERROR) |

---

## Команды бота

| Команда | Описание | Пример |
|---|---|---|
| `/start` | Приветствие и справка | `/start` |
| `/add` | Добавить расход | `/add 1500 ужин @alice @bob` |
| `/balance` | Показать балансы группы | `/balance` |
| `/settle` | Показать оптимальные переводы | `/settle` |
| `/close` | Закрыть период расчётов | `/close` |
| `/help` | Справка по командам | `/help` |

---

## Архитектура

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  Telegram   │────▶│  bot/        │────▶│  core/      │
│  (aiogram)  │◀────│  handlers    │◀────│  services   │
└─────────────┘     │  middlewares │     │  repos      │
                    └──────────────┘     │  models     │
                                         └──────┬──────┘
                                                │
                                         ┌──────▼──────┐
                                         │  SQLAlchemy │
                                         │  (async)    │
                                         │  SQLite/PG  │
                                         └─────────────┘
```

- **core/** — доменная логика, модели, репозитории, сервисы. Не зависит от aiogram.
- **bot/** — Telegram-хендлеры, FSM, клавиатуры. Тонкий слой над core.
- **migrations/** — Alembic-миграции (async).

---

## Разработка

```bash
# Тесты
pytest -x -q

# Линтинг
ruff check .
ruff format --check .

# Типы
mypy core bot --ignore-missing-imports
```

CI запускается автоматически на push/PR в `main`.

---

## Roadmap

- [ ] Неравное разделение расходов (кастомные доли)
- [ ] Inline-кнопки для подтверждения переводов
- [ ] История расходов с пагинацией (`/history`)
- [ ] Экспорт в CSV
- [ ] Поддержка нескольких валют
- [ ] Напоминания о долгах по расписанию

---

## Лицензия

MIT — см. [LICENSE](LICENSE).

## Contributing

Pull requests приветствуются. Для крупных изменений — откройте issue для обсуждения.

---

# Chipin 💸 (English)

> Split-the-bill Telegram bot for group chats.

## Quick Start

```bash
git clone https://github.com/kroch228/chipin-bot.git
cd chipin-bot
cp .env.example .env
# Set BOT_TOKEN from @BotFather
docker compose up -d
```

## Features

- Add expenses with multiple participants
- Automatic equal split calculation
- Group balance overview
- Optimal debt settlement (minimum transfers)
- Period close/reset
- Multi-group support
- Async architecture (aiogram 3 + SQLAlchemy async)
- Docker-ready with auto-migrations

## Commands

| Command | Description | Example |
|---|---|---|
| `/start` | Welcome message | `/start` |
| `/add` | Add expense | `/add 1500 dinner @alice @bob` |
| `/balance` | Show group balances | `/balance` |
| `/settle` | Show optimal transfers | `/settle` |
| `/close` | Close billing period | `/close` |
| `/help` | Help | `/help` |

## License

MIT
