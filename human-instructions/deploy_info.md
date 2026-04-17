## **📋 Общий обзор**

Вы развертываете веб-приложение (FastAPI + Nuxt) на чистом VPS с использованием:
1. **Docker Compose** — для управления контейнерами
2. **Nginx** — как обратный прокси и SSL-терминатор
3. **PostgreSQL** — база данных
4. **Redis** — кэш и очереди
5. **Let's Encrypt** — бесплатные SSL-сертификаты

Стек из 5 сервисов:
```
db (PostgreSQL 18) ──┐
redis (Redis 8)    ──┤
                     ├── backend (FastAPI, port 8000) ──┐
                     └── frontend (Nuxt 3, port 3000) ──┤
                                                        nginx (80/443) ── Интернет
```

---

## **🔍 Детальный разбор каждого шага**

### **Фаза 1: Подготовка VPS**

#### Шаг 1: Обновление системы
```bash
sudo apt update && sudo apt upgrade -y
```
- **`apt update`** — обновляет список доступных пакетов (не устанавливает их)
- **`apt upgrade -y`** — обновляет уже установленные пакеты. `-y` автоматически отвечает "yes"
- **Зачем?** Безопасность и стабильность. Новый сервер часто имеет устаревшие пакеты.

#### Шаг 2: Установка Docker и Docker Compose
```bash
curl -fsSL https://get.docker.com | sh
sudo systemctl enable docker
sudo systemctl start docker

# Проверка — должно быть Docker Compose v2
docker compose version
```
- **Docker** — платформа для контейнеризации приложений
- **Docker Compose** — инструмент для управления несколькими контейнерами через YAML-файл
- **Важно:** используйте `docker compose` (v2, встроен в Docker), не `docker-compose` (устаревший v1)
- **`systemctl enable docker`** — запускать Docker при загрузке системы

#### Шаг 3: Настройка фаервола
```bash
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP (нужен для ACME-challenge и редиректа)
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
```
- **Порты 5432, 6379, 8000, 3000 НЕ открываются** — они не должны быть доступны из интернета
- При использовании `docker-compose.prod.yml` эти порты убираются из публичного биндинга

---

### **Фаза 2: Настройка домена и SSL**

#### Шаг 1: Настройка DNS
```bash
# Это не команда, а инструкция что сделать:
# ваш-домен.ru  → IP_VPS
# www.ваш-домен.ru → IP_VPS
```
- **DNS (Domain Name System)** — преобразует доменное имя в IP-адрес сервера
- **A-запись** — связывает домен с IP-адресом
- **Где настраивать?** У вашего регистратора домена (Рег.ру, GoDaddy, Namecheap)
- **Зачем?** Чтобы пользователи могли заходить по домену, а не по IP-адресу

#### Шаг 2: Получение SSL сертификата
```bash
# Выпуск сертификата через Docker (не нужно ставить certbot на хост)
docker run --rm -p 80:80 \
  -v /etc/letsencrypt:/etc/letsencrypt \
  certbot/certbot certonly --standalone \
  -d ваш-домен.ru -d www.ваш-домен.ru \
  --email admin@ваш-домен.ru --agree-tos --no-eff-email
```
- **certbot** — запрашивает SSL сертификат у Let's Encrypt
- **`--standalone`** — certbot сам поднимает временный HTTP-сервер на порту 80
- **Что происходит?** Certbot подтверждает, что вы владеете доменом, и выдает сертификат на 90 дней

#### Шаг 3: Автопродление сертификата
Сервис `certbot` в `docker-compose.prod.yml` крутится в фоне и продлевает сертификат каждые 12 часов (продление произойдёт только если до истечения осталось ≤30 дней). Дополнительно добавьте в cron на VPS перезагрузку nginx после продления:
```bash
# crontab -e
0 */12 * * * cd /opt/ваш-проект && \
  docker compose -f docker-compose.yml -f docker-compose.prod.yml \
  run --rm certbot renew --quiet && \
  docker compose exec nginx nginx -s reload
```

---

### **Фаза 3: Настройка Nginx**

#### Что такое Nginx?
- **Веб-сервер** и **обратный прокси**
- Принимает запросы от пользователей и перенаправляет их нужному сервису
- Работает как "привратник": снаружи виден только nginx, внутренние сервисы скрыты

#### Архитектура маршрутизации:
```
Браузер
  │
  ├─ /api/* ──► nginx (443) ──► backend:8000 (FastAPI)
  │
  └─ /*     ──► nginx (443) ──► frontend:3000 (Nuxt SSR)
```

#### Конфигурационный файл `nginx.conf`:
```nginx
# Часть 1: Редирект с HTTP на HTTPS + ACME challenge
server {
    listen 80;
    server_name ваш-домен.ru www.ваш-домен.ru;
    location /.well-known/acme-challenge/ { root /var/www/certbot; }
    location / { return 301 https://$host$request_uri; }
}

# Часть 2: Основная конфигурация HTTPS
server {
    listen 443 ssl http2;
    server_name ваш-домен.ru www.ваш-домен.ru;

    ssl_certificate     /etc/letsencrypt/live/ваш-домен.ru/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/ваш-домен.ru/privkey.pem;
    ssl_protocols       TLSv1.2 TLSv1.3;

    # Заголовки безопасности
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;

    # Сжатие данных
    gzip on;

    # FastAPI backend
    location /api/ {
        proxy_pass http://backend;  # → backend:8000
        proxy_set_header X-Forwarded-Proto $scheme;
        # ... заголовки
    }

    # Nuxt статика — кэш на год
    location /_nuxt/ {
        proxy_pass http://frontend;
        expires 365d;
        add_header Cache-Control "public, immutable";
    }

    # Nuxt SSR — всё остальное
    location / {
        proxy_pass http://frontend;  # → frontend:3000
        # ... заголовки
    }
}
```

#### Nginx работает в Docker-контейнере:
Конфиг монтируется через volume — никаких `sites-available`/`sites-enabled` не нужно:
```yaml
# docker-compose.prod.yml
nginx:
  volumes:
    - ./nginx.conf:/etc/nginx/nginx.conf:ro      # конфиг
    - /etc/letsencrypt:/etc/letsencrypt:ro        # SSL сертификаты
    - certbot-www:/var/www/certbot:ro             # ACME challenge
```

---

### **Фаза 4: Развертывание приложения**

#### Шаг 1: Создание production .env файла
```bash
cp .env.example .env
nano .env
```

В `.env` на сервере укажите реальные значения:
```bash
# База данных
POSTGRES_PASSWORD=<сгенерированный_пароль>  # openssl rand -hex 32
DATABASE_URL=postgresql+asyncpg://app_user:<пароль>@db:5432/myapp

# Auth
SECRET_KEY=<сгенерированный_ключ>   # python3 -c "import secrets; print(secrets.token_hex(32))"

# Продакшен
APP_ENV=production
DOMAIN=ваш-домен.ru
NUXT_PUBLIC_API_BASE=https://ваш-домен.ru/api
CORS_ORIGINS=["https://ваш-домен.ru","https://www.ваш-домен.ru"]
```

**О `NUXT_PUBLIC_API_BASE`:** Nuxt 3 автоматически маппит переменные с префиксом `NUXT_PUBLIC_` в `runtimeConfig.public`. Переменная `NUXT_PUBLIC_API_BASE` становится `runtimeConfig.public.apiBase` — используется браузерным клиентом для публичных API-запросов.

#### Шаг 2: Docker Compose конфигурация

Используются два файла compose:
- **`docker-compose.yml`** — базовый (5 сервисов: db, redis, backend, frontend, nginx)
- **`docker-compose.prod.yml`** — override для продакшена (убирает лишние порты, добавляет SSL volumes)

Структура базового файла:
```yaml
services:
  db:        # PostgreSQL 18, volume pgdata, healthcheck
  redis:     # Redis 8, healthcheck
  backend:   # FastAPI, depends_on db+redis, healthcheck /api/v1/health
  frontend:  # Nuxt 3, depends_on backend, healthcheck /
  nginx:     # Nginx, depends_on backend+frontend
```

#### Шаг 3: Запуск в production
```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```
- `-f docker-compose.yml -f docker-compose.prod.yml` — применить оба файла (override)
- `-d` — в фоновом режиме
- `--build` — пересобрать образы

#### Шаг 4: Просмотр логов
```bash
docker compose logs -f backend   # Логи FastAPI
docker compose logs -f frontend  # Логи Nuxt
docker compose logs -f nginx     # Логи Nginx
```

---

### **Фаза 5: Работа с базой данных**

#### Миграции Alembic:
Миграции **запускаются автоматически** при старте backend-контейнера через `entrypoint.sh`.

Для ручного управления:
```bash
# Применить все pending-миграции
docker compose exec backend uv run alembic upgrade head

# Проверить текущее состояние
docker compose exec backend uv run alembic current

# Откатить последнюю миграцию
docker compose exec backend uv run alembic downgrade -1
```

#### Доступ к базе данных:
```bash
docker compose exec db psql -U app_user -d myapp
```

---

## **🎯 Ключевые концепции для понимания**

### **Что такое Docker Compose?**
Представьте, что у вас есть 5 взаимосвязанных сервисов. Вместо ручной настройки каждого вы описываете их в YAML-файле, и Docker Compose:
- Скачивает образы
- Настраивает сеть между контейнерами
- Управляет переменными окружения
- Создаёт тома для данных
- Следит за зависимостями (healthcheck + depends_on)

### **Что делает Nginx как reverse proxy?**
```
Интернет → Nginx (443) → /api/*   → backend (FastAPI, :8000)
                       → /_nuxt/* → frontend (Nuxt, :3000) [кэш]
                       → /*       → frontend (Nuxt, :3000) [SSR]
```
Преимущества:
- SSL-терминация — только nginx работает с сертификатами
- Кэширование статики Nuxt (JS/CSS)
- Сжатие (gzip)
- Заголовки безопасности
- Внутренние сервисы не видны напрямую из интернета

### **Почему такая архитектура?**
1. **Изоляция** — каждое приложение в своём контейнере
2. **Переносимость** — одинаково работает на любом сервере
3. **Безопасность** — фаервол, SSL, security headers, закрытые внутренние порты
4. **Удобство обновлений** — `git pull && docker compose up --build` без простоя

---

## **⚠️ На что обратить внимание**

1. **Удалить `docker-compose.override.yml` с сервера** — он автоматически подхватывается Docker Compose и переводит стек в dev-режим (hot-reload, открытые порты)
2. **Замена `[DOMAIN]` в nginx.conf** — в шаблоне стоит плейсхолдер; заменить на реальный домен перед запуском
3. **Бэкап приватных ключей** (SSL-сертификаты, пароли БД)
4. **Регулярные обновления** системы и Docker-образов

## **🛠️ Порядок действий для новичка:**

1. **Подготовка** (15 мин):
   - Купить VPS (Hetzner, DigitalOcean, Selectel)
   - Купить домен
   - Настроить DNS-записи

2. **Выполнение команд** (30 мин):
   - Фаза 1 полностью
   - Дождаться распространения DNS (до 24 часов)
   - Фазы 2–5

3. **Тестирование** (15 мин):
   - Проверить `http://ваш-домен.ru` → должен редиректить на `https://`
   - Проверить `https://ваш-домен.ru` → должно работать приложение
   - Проверить `https://ваш-домен.ru/api/v1/health` → JSON от FastAPI
   - Проверить SSL: https://www.ssllabs.com/ssltest/
