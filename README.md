<div align="center">

<img src="https://raw.githubusercontent.com/Tarikul-Islam-Anik/Animated-Fluent-Emojis/master/Emojis/Objects/Locked%20with%20Key.png" alt="VPN Bot Logo" width="100" />

# Unbroken VPN Bot

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/aiogram-3.x-0088CC?style=for-the-badge&logo=telegram&logoColor=white" alt="aiogram" />
  <img src="https://img.shields.io/badge/PostgreSQL-16-336791?style=for-the-badge&logo=postgresql&logoColor=white" alt="PostgreSQL" />
  <img src="https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker" />
</p>

<p align="center">
  <img src="https://readme-typing-svg.herokuapp.com?font=Fira+Code&weight=500&size=20&pause=1000&color=6366F1&center=true&vCenter=true&width=500&lines=Telegram+%D0%B1%D0%BE%D1%82+%D0%B4%D0%BB%D1%8F+%D0%BF%D1%80%D0%BE%D0%B4%D0%B0%D0%B6%D0%B8+VPN;Outline+VPN+%2B+Telegram+Payments;%D0%90%D0%B2%D1%82%D0%BE%D0%BC%D0%B0%D1%82%D0%B8%D1%87%D0%B5%D1%81%D0%BA%D0%BE%D0%B5+%D1%83%D0%BF%D1%80%D0%B0%D0%B2%D0%BB%D0%B5%D0%BD%D0%B8%D0%B5+%D0%BF%D0%BE%D0%B4%D0%BF%D0%B8%D1%81%D0%BA%D0%B0%D0%BC%D0%B8" alt="Typing SVG" />
</p>

**Telegram-бот для автоматизированной продажи VPN-ключей Outline**

</div>

---

## Функционал

### 🔑 VPN-ключи
- Автоматическая генерация ключей через Outline API
- Мгновенная выдача после оплаты
- Деактивация ключа по истечении подписки

### 💳 Платежи
- Приём оплаты через Telegram Payments
- Гибкие тарифы (настраиваемая длительность и цена)
- Автоматическое создание и продление подписок

### 🎁 Пробный период
- 7 дней бесплатного доступа для новых пользователей
- Одноразовая активация на аккаунт

### 🤝 Реферальная программа
- Уникальная реферальная ссылка для каждого пользователя
- +7 дней приглашённому при регистрации
- +7 дней пригласившему при первой оплате реферала

### ⏰ Планировщик
- Автоматические уведомления за 3 дня до окончания
- Деактивация подписки по расписанию
- Перепланирование задач при продлении

### 🛡️ Надёжность
- Retry-логика с exponential backoff
- Асинхронные транзакции
- Иерархия исключений (17+ классов)
- Детальное логирование

---

## Архитектура

Проект построен по принципам **Domain-Driven Design** с разделением на слои:

**Presentation Layer**
- `bot/handlers/` — обработчики команд и callback'ов
- `bot/middlewares.py` — DB Session middleware, управление клавиатурами

**Business Logic Layer**
- `core/user/` — управление пользователями
- `core/subscription/` — подписки, планировщик, фоновые задачи
- `core/payment/` — создание инвойсов, обработка платежей
- `core/referral/` — реферальная программа
- `core/tariff/` — тарифы

**Data Layer**
- Repositories для каждого домена
- Async SQLAlchemy с asyncpg
- Redis для кэширования

**External Integrations**
- Outline API — управление VPN-ключами
- Telegraph API — политика конфиденциальности

### Структура проекта

```
.github/
└── workflows/
    └── cicd.yml

src/
├── bot/
│   ├── __init__.py
│   ├── handlers/
│   │   ├── __init__.py
│   │   ├── commands.py
│   │   ├── help.py
│   │   ├── main_menu.py
│   │   ├── payment.py
│   │   ├── privacy_policy.py
│   │   ├── referral_info.py
│   │   ├── subscription_info.py
│   │   └── trial_period.py
│   ├── utils/
│   │   └── datetime_formatter.py
│   ├── keyboards.py
│   ├── middlewares.py
│   ├── states.py
│   ├── texts.py
│   ├── privacy_policy.html
│   └── telegraph_page.json
│
├── core/
│   ├── models.py
│   ├── user/
│   │   ├── models.py
│   │   ├── repository.py
│   │   └── service.py
│   ├── subscription/
│   │   ├── models.py
│   │   ├── repository.py
│   │   ├── service.py
│   │   ├── scheduler.py
│   │   └── jobs.py
│   ├── payment/
│   │   ├── models.py
│   │   ├── repository.py
│   │   └── service.py
│   ├── referral/
│   │   ├── models.py
│   │   ├── repository.py
│   │   └── service.py
│   └── tariff/
│       ├── models.py
│       └── repository.py
│
├── outline/
│   └── service.py
│
├── migrations/
│   └── versions/
│
├── config.py
├── database.py
├── exceptions.py
└── main.py

tests/
├── conftest.py
├── samples.py
└── unit/
```

---

## Технологии

| Категория | Стек |
|-----------|------|
| Backend | Python 3.10+, aiogram 3.x |
| Database | PostgreSQL 16, SQLAlchemy 2.0, Alembic |
| Cache | Redis 6.2 |
| VPN | Outline API (pyoutlineapi) |
| Validation | Pydantic 2.x |
| Scheduler | APScheduler |
| DevOps | Docker, GitHub Actions |
| Testing | pytest, pre-commit |

---

## Установка

### Требования
- Python 3.10+
- PostgreSQL 14+
- Redis 6+
- Outline VPN Server
- Telegram Bot Token

### Конфигурация

`.env` файл:

```env
MODE=DEV

BOT_TOKEN=your_telegram_bot_token

DB_HOST=db
DB_PORT=5432
DB_USER=your_user
DB_PASS=your_password
DB_NAME=vpn_db

TEST_DB_HOST=test_db
TEST_DB_PORT=5432
TEST_DB_USER=your_user
TEST_DB_PASS=your_password
TEST_DB_NAME=test_vpn_db

REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=your_password

TEST_REDIS_HOST=test_redis
TEST_REDIS_PORT=6379
TEST_REDIS_DB=3
TEST_REDIS_PASSWORD=your_password

OUTLINE_API_URL=https://your-outline-server:port/api-secret
OUTLINE_CERT_SHA256=your_certificate_sha256

PAYMASTER_MERCHANT_ID=your_paymaster_token
```

### Docker

```bash
docker-compose up -d
```

### Локальная разработка

```bash
git clone https://github.com/yourusername/unbroken-vpn-bot.git
cd unbroken-vpn-bot

python -m venv .venv
.venv\Scripts\activate

pip install -r requirements.txt
pip install -r requirements-dev.txt

alembic upgrade head
python -m src.main
```

---

## Тестирование

```bash
pytest                    # Все тесты
pytest --cov=src          # С покрытием
pytest tests/unit -v      # Unit-тесты
```



