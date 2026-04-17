# Деплой FastAPI + Nuxt приложения на VPS

## Оглавление

1. [Подготовка VPS](#подготовка-vps)
2. [Настройка домена и DNS](#настройка-домена-и-dns)
3. [Настройка безопасности (UFW)](#настройка-безопасности-ufw)
4. [Установка Docker](#установка-docker)
5. [Клонирование проекта и настройка окружения](#клонирование-проекта-и-настройка-окружения)
6. [Первоначальный выпуск SSL-сертификата](#первоначальный-выпуск-ssl-сертификата)
7. [Запуск в production](#запуск-в-production)
8. [Миграции и база данных](#миграции-и-база-данных)
9. [CI/CD через GitHub Actions](#cicd-через-github-actions)
10. [Мониторинг и обслуживание](#мониторинг-и-обслуживание)
11. [Частые проблемы и решения](#частые-проблемы-и-решения)
12. [Чеклист](#чеклист)

---

## Подготовка VPS

### 1. Подключение к серверу

```bash
ssh root@ваш_сервер_ip
```

### 2. Обновление системы

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y curl wget git nano htop
```

---

## Настройка домена и DNS

### 1. Покупка домена

Купите домен у регистратора (Рег.ру, GoDaddy, Namecheap). Для примера: `ваш-домен.ru`

### 2. Настройка DNS-записей

В панели управления доменом создайте **A-записи**:

| Тип | Имя | Значение      | TTL  |
| --- | --- | ------------- | ---- |
| A   | @   | IP_вашего_VPS | 3600 |
| A   | www | IP_вашего_VPS | 3600 |

**Распространение DNS:** от 15 минут до 48 часов.

Подробная инструкция по настройке DNS на Рег.ру → [`dns_info.md`](dns_info.md)

### 3. Проверка DNS

```bash
nslookup ваш-домен.ru
# Ответ должен содержать IP вашего VPS
```

---

## Настройка безопасности (UFW)

```bash
sudo apt install -y ufw
sudo ufw allow 22/tcp    # SSH — открыть ДО включения!
sudo ufw allow 80/tcp    # HTTP (нужен для ACME-challenge и редиректа)
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
sudo ufw status
```

**Важно:** Порты 5432 (PostgreSQL), 6379 (Redis), 8000 (FastAPI), 3000 (Nuxt) **не открывать** — они доступны только внутри Docker-сети.

Подробное руководство по UFW → [`firewall_info.md`](firewall_info.md)

### Создание непривилегированного пользователя (рекомендуется)

```bash
adduser deploy
usermod -aG sudo deploy
usermod -aG docker deploy

# Скопировать SSH-ключ для нового пользователя
rsync --archive --chown=deploy:deploy ~/.ssh /home/deploy

# Переключиться на нового пользователя
su - deploy
```

---

## Установка Docker

```bash
# Официальный скрипт установки (устанавливает актуальную версию с Docker Compose v2)
curl -fsSL https://get.docker.com | sh

# Запустить Docker при загрузке системы
sudo systemctl enable docker
sudo systemctl start docker

# Добавить текущего пользователя в группу docker (чтобы не вводить sudo)
sudo usermod -aG docker $USER
# Переподключитесь к серверу, чтобы изменения вступили в силу

# Проверка
docker --version
docker compose version   # Должно быть v2+
```

---

## Клонирование проекта и настройка окружения

### 1. Клонирование репозитория

```bash
git clone <ваш-репозиторий> /opt/ваш-проект
cd /opt/ваш-проект
```

### 2. Удалить dev-override с сервера

```bash
# ОБЯЗАТЕЛЬНО: docker-compose.override.yml автоматически подхватывается
# Docker Compose и переводит стек в dev-режим (hot-reload, открытые порты)
rm docker-compose.override.yml
```

### 3. Создать и заполнить `.env`

```bash
cp .env.example .env
nano .env
```

Заполните все значения. Особое внимание:

```bash
# База данных — сгенерировать надёжный пароль
POSTGRES_PASSWORD=$(openssl rand -hex 32)
# Вставьте результат в .env

# DATABASE_URL — обновите пароль
DATABASE_URL=postgresql+asyncpg://app_user:<ваш_пароль>@db:5432/myapp

# Auth — сгенерировать секретный ключ
python3 -c "import secrets; print(secrets.token_hex(32))"
# Вставьте результат в SECRET_KEY

# Продакшен-режим
APP_ENV=production

# Домен
DOMAIN=ваш-домен.ru

# Публичный URL API для браузерного клиента Nuxt
NUXT_PUBLIC_API_BASE=https://ваш-домен.ru/api

# CORS — разрешить только ваш домен
CORS_ORIGINS=["https://ваш-домен.ru","https://www.ваш-домен.ru"]
```

### 4. Заменить `[DOMAIN]` в nginx.conf

```bash
sed -i 's/\[DOMAIN\]/ваш-домен.ru/g' nginx.conf

# Проверить результат
grep server_name nginx.conf
```

---

## Первоначальный выпуск SSL-сертификата

SSL-сертификат нужно получить **до** запуска полного prod-стека, иначе nginx не сможет стартовать (он ищет файлы сертификата при запуске).

Используем Certbot в Docker — ничего не нужно устанавливать на хост:

```bash
# Убедитесь, что DNS уже распространился (nslookup ваш-домен.ru → IP вашего VPS)
# Убедитесь, что порт 80 открыт (ufw allow 80/tcp)

docker run --rm \
  -p 80:80 \
  -v /etc/letsencrypt:/etc/letsencrypt \
  certbot/certbot certonly \
    --standalone \
    -d ваш-домен.ru \
    -d www.ваш-домен.ru \
    --email admin@ваш-домен.ru \
    --agree-tos \
    --no-eff-email
```

Certbot создаст сертификаты в `/etc/letsencrypt/live/ваш-домен.ru/`.

**Что происходит:** Certbot временно поднимает HTTP-сервер на порту 80, Let's Encrypt обращается к `http://ваш-домен.ru/.well-known/acme-challenge/...` для проверки владения доменом, затем выдаёт сертификат.

Подробное объяснение работы Certbot → [`cert_bot_lets_encrypt.md`](cert_bot_lets_encrypt.md)

---

## Запуск в production

```bash
cd /opt/ваш-проект

docker compose \
  -f docker-compose.yml \
  -f docker-compose.prod.yml \
  up -d --build
```

Первый запуск займёт несколько минут — Docker собирает образы backend и frontend.

### Проверка запуска

```bash
# Статус всех контейнеров
docker compose ps

# Ожидаемый результат (все сервисы healthy/running):
# NAME         STATUS          PORTS
# db           Up (healthy)
# redis        Up (healthy)
# backend      Up (healthy)
# frontend     Up
# nginx        Up              0.0.0.0:80->80/tcp, 0.0.0.0:443->443/tcp
# certbot      Up
```

### Проверка работы приложения

```bash
# Проверка редиректа HTTP → HTTPS
curl -I http://ваш-домен.ru
# Ожидается: 301 Moved Permanently → https://

# Проверка HTTPS
curl -I https://ваш-домен.ru
# Ожидается: 200 OK

# Проверка FastAPI
curl https://ваш-домен.ru/api/v1/health
# Ожидается: {"status": "ok"} или аналогичный JSON

# Убедиться, что внутренние порты НЕ торчат наружу
ss -tlnp | grep -E '5432|6379|8000|3000'
# Ожидается: пустой вывод
```

### Просмотр логов

```bash
docker compose logs -f backend    # Логи FastAPI (Alembic миграции + запросы)
docker compose logs -f frontend   # Логи Nuxt SSR
docker compose logs -f nginx      # Логи Nginx (доступ + ошибки)
docker compose logs -f db         # Логи PostgreSQL
```

---

## Миграции и база данных

### Автоматический запуск

Alembic-миграции запускаются **автоматически** при каждом старте backend-контейнера через `entrypoint.sh`. Специально запускать ничего не нужно.

### Ручное управление миграциями

```bash
# Применить все pending-миграции
docker compose exec backend uv run alembic upgrade head

# Проверить текущее состояние
docker compose exec backend uv run alembic current

# Показать историю миграций
docker compose exec backend uv run alembic history

# Откатить последнюю миграцию
docker compose exec backend uv run alembic downgrade -1
```

### Доступ к базе данных

```bash
# Подключиться к psql
docker compose exec db psql -U app_user -d myapp

# Посмотреть таблицы
\dt

# Выйти
\q
```

### Бэкап и восстановление

```bash
# Создать бэкап
docker compose exec -T db \
  pg_dump -U app_user myapp > backup_$(date +%Y%m%d_%H%M%S).sql

# Восстановить из бэкапа
cat backup.sql | docker compose exec -T db psql -U app_user -d myapp
```

---

## CI/CD через GitHub Actions

Файл `.github/workflows/deploy.yml` настраивает автоматический деплой: после успешного CI-пайплайна на ветке `main` — автоматически деплоит на VPS.

### Необходимые GitHub Secrets

Перейдите в репозиторий → **Settings → Secrets and variables → Actions → New repository secret**.

| Secret        | Значение |
| ------------- | -------- |
| `VPS_HOST`    | IP-адрес или hostname VPS |
| `VPS_USER`    | Пользователь SSH (например, `deploy` или `ubuntu`) |
| `VPS_SSH_KEY` | Приватный SSH-ключ (содержимое файла `~/.ssh/github_deploy`) |
| `PROJECT_DIR` | Путь к проекту на VPS (например, `/opt/ваш-проект`) |

### Генерация SSH-ключа для CI

Выполните на **сервере** (или локально, затем скопируйте публичный ключ на сервер):

```bash
# Генерация ключевой пары
ssh-keygen -t ed25519 -C "github-actions-deploy" -f ~/.ssh/github_deploy -N ""

# Добавить публичный ключ в authorized_keys на сервере
cat ~/.ssh/github_deploy.pub >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys

# Скопировать приватный ключ в GitHub Secret VPS_SSH_KEY
cat ~/.ssh/github_deploy
# Скопируйте ВЕСЬ вывод (включая строки -----BEGIN и -----END)
```

### Процесс деплоя

1. Разработчик делает `git push` в `main`
2. GitHub Actions запускает CI (lint + tests + docker build)
3. Если CI прошёл — запускается `deploy.yml`
4. SSH-подключение к VPS → `git pull` → `docker compose up --build`
5. Сервис доступен с новой версией кода

---

## Мониторинг и обслуживание

### Обновление вручную (без CI)

```bash
cd /opt/ваш-проект
git pull
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build --remove-orphans
```

### Перезапуск отдельного сервиса

```bash
docker compose restart backend
docker compose restart nginx
```

### Продление SSL-сертификата

Сервис `certbot` в `docker-compose.prod.yml` крутится в фоне и автоматически продлевает сертификат. Для надёжности добавьте cron-задачу на VPS:

```bash
crontab -e
# Добавить строку:
0 */12 * * * cd /opt/ваш-проект && docker compose -f docker-compose.yml -f docker-compose.prod.yml run --rm certbot renew --quiet && docker compose exec nginx nginx -s reload
```

Проверить сертификаты:
```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml \
  run --rm certbot certificates
```

### Мониторинг ресурсов

```bash
# Статистика контейнеров
docker stats

# Системные ресурсы
htop

# Дисковое пространство
df -h
du -sh /var/lib/docker/volumes/*
```

### Очистка Docker

```bash
# Удалить неиспользуемые образы, сети, контейнеры (НЕ удаляет volumes)
docker system prune -f

# Посмотреть размер Docker-данных
docker system df
```

### Полезные команды Docker

```bash
# Просмотр логов с фильтром по времени
docker compose logs --since="1h" backend

# Войти в контейнер backend (для отладки)
docker compose exec backend bash

# Войти в контейнер frontend
docker compose exec frontend sh

# Пересобрать только один сервис
docker compose -f docker-compose.yml -f docker-compose.prod.yml \
  up -d --build backend
```

---

## Частые проблемы и решения

### 1. nginx не стартует: `cannot load certificate`

**Причина:** SSL-сертификат ещё не выпущен, nginx не находит файлы `/etc/letsencrypt/live/...`

**Решение:** Выпустить сертификат через certbot standalone (см. раздел [Первоначальный выпуск SSL](#первоначальный-выпуск-ssl-сертификата)) и только потом запускать полный стек.

### 2. 502 Bad Gateway

**Причина:** backend или frontend не запустился или ещё стартует.

**Решение:**
```bash
docker compose logs -f backend
docker compose ps
# Подождать, пока healthcheck не станет healthy
```

### 3. CORS error в браузере

**Причина:** `CORS_ORIGINS` в `.env` не включает ваш домен.

**Решение:**
```bash
# В .env на сервере:
CORS_ORIGINS=["https://ваш-домен.ru","https://www.ваш-домен.ru"]

docker compose restart backend
```

### 4. Nuxt: API-запросы в браузере падают (Network Error)

**Причина:** `NUXT_PUBLIC_API_BASE` не задан или указывает на `localhost`.

**Решение:**
```bash
# В .env на сервере:
NUXT_PUBLIC_API_BASE=https://ваш-домен.ru/api

docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build frontend
```

### 5. Порты 5432 / 6379 / 8000 / 3000 доступны из интернета

**Причина:** Запустили без `docker-compose.prod.yml`, использовали только базовый `docker-compose.yml`.

**Решение:** Всегда запускать с двумя файлами:
```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

### 6. Alembic: `Can't connect to the database`

**Причина:** backend стартовал раньше, чем db стал healthy.

**Решение:** `depends_on` с `condition: service_healthy` должен предотвращать это. Если всё же происходит:
```bash
docker compose restart backend
# Или применить миграции вручную
docker compose exec backend uv run alembic upgrade head
```

### 7. DNS не разрешается

**Решение:** Подождать 1–48 часов после изменения DNS-записей. Проверить:
```bash
nslookup ваш-домен.ru
dig ваш-домен.ru
```

### 8. Потеряли доступ по SSH

**Решение:**
1. Используйте веб-консоль провайдера VPS
2. Обратитесь в поддержку хостинга

### 9. Certbot: `Could not bind to IPv4 or IPv6`

**Причина:** Порт 80 занят другим процессом (или nginx уже запущен).

**Решение:**
```bash
# Остановить nginx перед запуском certbot standalone
docker compose stop nginx
# Запустить certbot
docker run --rm -p 80:80 -v /etc/letsencrypt:/etc/letsencrypt \
  certbot/certbot certonly --standalone -d ваш-домен.ru ...
# Запустить nginx обратно
docker compose start nginx
```

---

## Чеклист

**Однократная настройка сервера:**

1. [ ] Купить домен, настроить A-записи в DNS
2. [ ] Подключиться к VPS: `ssh root@IP`
3. [ ] Обновить систему: `apt update && apt upgrade -y`
4. [ ] Установить Docker: `curl -fsSL https://get.docker.com | sh`
5. [ ] Настроить UFW: открыть порты 22, 80, 443
6. [ ] Клонировать проект: `git clone ... /opt/ваш-проект`
7. [ ] Удалить `docker-compose.override.yml` с сервера
8. [ ] Создать `.env` на основе `.env.example`, заполнить все значения
9. [ ] Заменить `[DOMAIN]` в `nginx.conf`: `sed -i 's/\[DOMAIN\]/ваш-домен.ru/g' nginx.conf`
10. [ ] Дождаться распространения DNS: `nslookup ваш-домен.ru` → IP сервера
11. [ ] Выпустить SSL: `docker run certbot/certbot certonly --standalone ...`
12. [ ] Запустить стек: `docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build`
13. [ ] Проверить: `curl -I https://ваш-домен.ru` → 200 OK

**CI/CD (однократно):**

14. [ ] Создать GitHub Secrets: `VPS_HOST`, `VPS_USER`, `VPS_SSH_KEY`, `PROJECT_DIR`
15. [ ] Сгенерировать SSH-ключ для CI, добавить публичный ключ в `authorized_keys`
16. [ ] Сделать тестовый push в `main`, убедиться что CI + deploy workflow прошли

**Регулярное обслуживание:**

17. [ ] Добавить cron для продления SSL (раз в 12 часов)
18. [ ] Настроить регулярный бэкап БД

---

_Руководство охватывает стандартный деплой FastAPI + Nuxt на VPS с Docker, Nginx и Let's Encrypt SSL._
