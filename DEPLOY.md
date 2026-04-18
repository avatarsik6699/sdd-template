# Деплой на VPS

Полный линейный флоу: от чистого сервера до работающего HTTPS-приложения и последующих обновлений через GitHub Actions.

**Стек:** FastAPI (`:8000`) + Nuxt 3 SSR (`:3000`) + PostgreSQL + Redis + Nginx (`:80`/`:443`) + Let's Encrypt

---

## Содержание

1. [Что понадобится заранее](#1-что-понадобится-заранее)
2. [Подготовка VPS](#2-подготовка-vps)
3. [Настройка домена](#3-настройка-домена)
4. [Установка Docker](#4-установка-docker)
5. [Клонирование и настройка проекта](#5-клонирование-и-настройка-проекта)
6. [Выпуск SSL-сертификата](#6-выпуск-ssl-сертификата)
7. [Первый запуск](#7-первый-запуск)
8. [Настройка CI/CD (GitHub Actions)](#8-настройка-cicd-github-actions)
9. [Обновление приложения](#9-обновление-приложения)
10. [Мониторинг и обслуживание](#10-мониторинг-и-обслуживание)
11. [Частые проблемы](#11-частые-проблемы)

---

## 1. Что понадобится заранее

- **VPS** с Ubuntu 22.04/24.04 (минимум 1 CPU, 1 GB RAM)
- **Домен** (купить у Рег.ру, Namecheap, GoDaddy и т.п.)
- **Доступ по SSH** к серверу (обычно выдаётся хостингом при создании сервера)
- **GitHub-репозиторий** с кодом проекта

---

## 2. Подготовка VPS

Подключитесь к серверу:

```bash
ssh root@ВАШ_IP
```

Обновите систему и установите базовые утилиты:

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y curl wget git nano htop ufw
```

### Настройка файрвола (UFW)

```bash
sudo ufw allow 22/tcp    # SSH — открыть ПЕРВЫМ, до включения UFW
sudo ufw allow 80/tcp    # HTTP (нужен для ACME-challenge и редиректа на HTTPS)
sudo ufw allow 443/tcp   # HTTPS

sudo ufw enable          # включить файрвол
sudo ufw status          # проверить
```

> **Важно:** Порты 5432 (PostgreSQL), 6379 (Redis), 8000 (FastAPI), 3000 (Nuxt) **не открывать** — они видны только внутри Docker-сети. В production-конфиге они не пробрасываются на хост.

> **Подводный камень:** Если не открыть порт 22 до `ufw enable` — потеряете SSH-доступ. Провайдер VPS предоставляет аварийную веб-консоль для восстановления.

### Создание непривилегированного пользователя (рекомендуется)

Работать от `root` небезопасно. Создайте отдельного пользователя:

```bash
adduser deploy
usermod -aG sudo deploy
usermod -aG docker deploy   # добавить в группу docker (после установки Docker)

# Скопировать SSH-ключ от root
rsync --archive --chown=deploy:deploy ~/.ssh /home/deploy

# Переключиться
su - deploy
```

---

## 3. Настройка домена

В панели управления доменом (у вашего регистратора) создайте **A-записи**:

| Тип | Имя  | Значение    | TTL  |
|-----|------|-------------|------|
| A   | `@`  | IP_вашего_VPS | 3600 |
| A   | `www`| IP_вашего_VPS | 3600 |

Распространение DNS занимает от 15 минут до 48 часов. Проверить готовность:

```bash
nslookup ваш-домен.ru
# В ответе должен быть IP вашего VPS
```

> **Подводный камень:** Не запускайте Certbot (шаг 6), пока DNS не разрешится — Let's Encrypt не сможет проверить владение доменом и выдаст ошибку. Дождитесь, пока `nslookup` не вернёт IP вашего сервера.

---

## 4. Установка Docker

```bash
# Официальный скрипт — устанавливает актуальную версию с Docker Compose v2
curl -fsSL https://get.docker.com | sh

sudo systemctl enable docker   # запускать при загрузке
sudo systemctl start docker

# Добавить текущего пользователя в группу docker (не нужен sudo для docker-команд)
sudo usermod -aG docker $USER
```

**Переподключитесь к серверу** (или выполните `newgrp docker`), чтобы членство в группе вступило в силу.

```bash
# Проверка
docker --version
docker compose version   # должно быть v2+
```

> **Подводный камень:** Используйте `docker compose` (v2, встроен в Docker), а не `docker-compose` (устаревший v1). Они различаются поведением при слиянии override-файлов.

---

## 5. Клонирование и настройка проекта

### Клонирование

```bash
git clone <ВАШ_РЕПОЗИТОРИЙ> /opt/ваш-проект
cd /opt/ваш-проект
```

### Удаление dev-override

```bash
rm docker-compose.override.yml
```

> **Важно:** `docker-compose.override.yml` автоматически подхватывается Docker Compose и переводит стек в dev-режим: открывает порты 5432, 6379, 8000, 3000 наружу и включает hot-reload. На сервере этот файл обязательно удалить.

### Создание `.env`

**Рекомендуется:** используйте скрипт, который сам сгенерирует все секреты и заполнит production-значения:

```bash
./scripts/setup-prod.sh ваш-домен.ru admin@ваш-домен.ru
```

Скрипт автоматически:
- генерирует `SECRET_KEY`, `POSTGRES_PASSWORD`, `REDIS_PASSWORD`
- выставляет `APP_ENV=production`, `NUXT_PUBLIC_API_BASE`, `CORS_ORIGINS`
- заменяет `[DOMAIN]` в `nginx.conf`
- удаляет `docker-compose.override.yml`

**Вручную** (если нужен полный контроль):

```bash
cp .env.example .env
nano .env
```

Ключевые значения для production:

```bash
# База данных
POSTGRES_PASSWORD=<вывод openssl rand -hex 32>
DATABASE_URL=postgresql+asyncpg://app_user:<пароль>@db:5432/myapp

# Redis
REDIS_PASSWORD=<вывод openssl rand -hex 16>

# Auth
SECRET_KEY=<вывод python3 -c "import secrets; print(secrets.token_hex(32))">

# Production-режим
APP_ENV=production

# Домен
DOMAIN=ваш-домен.ru

# URL API для браузерного клиента Nuxt (без /api — иначе дублирование в запросах)
# Nuxt автоматически маппит NUXT_PUBLIC_* → runtimeConfig.public.*
NUXT_PUBLIC_API_BASE=https://ваш-домен.ru

# CORS — разрешить только ваш домен
CORS_ORIGINS=["https://ваш-домен.ru","https://www.ваш-домен.ru"]
```

Команды для генерации секретов:

```bash
openssl rand -hex 32
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### Замена `[DOMAIN]` в nginx.conf

В шаблоне `nginx.conf` стоит плейсхолдер `[DOMAIN]` — заменить на реальный домен:

```bash
sed -i 's/\[DOMAIN\]/ваш-домен.ru/g' nginx/nginx.conf

# Проверить
grep server_name nginx/nginx.conf
# Должно быть: server_name ваш-домен.ru www.ваш-домен.ru;
```

---

## 6. Выпуск SSL-сертификата

> **Порядок важен:** SSL-сертификат нужно получить **до** запуска полного стека. Nginx при старте проверяет наличие файлов сертификата — если их нет, контейнер упадёт с ошибкой `cannot load certificate`.

Certbot запускается как одноразовый Docker-контейнер — ничего не нужно устанавливать на хост:

```bash
# Убедитесь:
# 1. DNS уже разрешается: nslookup ваш-домен.ru → IP вашего VPS
# 2. Порт 80 открыт: ufw status | grep 80
# 3. На порту 80 ничего не запущено (полный стек ещё не стартовал)

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

Certbot временно поднимает HTTP-сервер на порту 80, Let's Encrypt обращается к `http://ваш-домен.ru/.well-known/acme-challenge/...` для подтверждения владения доменом и выдаёт сертификат на 90 дней. Файлы сохраняются в `/etc/letsencrypt/live/ваш-домен.ru/`.

> **Подводный камень:** Ошибка `Could not bind to IPv4 or IPv6 ... [Errno 98] Address already in use` — порт 80 занят. Остановите nginx или другой процесс, затем повторите.

> **Подводный камень:** Ошибка `DNS problem: NXDOMAIN looking up A for ваш-домен.ru` — DNS ещё не распространился. Ждите и повторяйте `nslookup`.

> **Лимиты Let's Encrypt:** 5 выпусков одного домена в неделю. Если исчерпали лимит во время тестирования, добавьте `--staging` в команду (тестовый сертификат, не доверенный браузером, но без лимитов).

---

## 7. Первый запуск

```bash
cd /opt/ваш-проект

docker compose \
  -f docker-compose.yml \
  -f docker-compose.prod.yml \
  up -d --build
```

Первый запуск занимает несколько минут — Docker собирает образы backend и frontend.

### Проверка статуса

```bash
docker compose ps
```

Ожидаемый результат (все сервисы `healthy` или `running`):

```
NAME       STATUS           PORTS
db         Up (healthy)
redis      Up (healthy)
backend    Up (healthy)
frontend   Up
nginx      Up               0.0.0.0:80->80/tcp, 0.0.0.0:443->443/tcp
certbot    Up
```

> **Подводный камень:** Если `backend` в статусе `unhealthy` — Alembic не смог подключиться к БД или упал при миграции. Смотрите логи: `docker compose logs backend`.

### Проверка работы приложения

```bash
# HTTP → HTTPS редирект
curl -I http://ваш-домен.ru
# Ожидается: 301 Moved Permanently

# HTTPS
curl -I https://ваш-домен.ru
# Ожидается: 200 OK

# FastAPI health
curl https://ваш-домен.ru/api/v1/health
# Ожидается: {"status":"ok"} или аналогичный JSON

# Убедиться, что внутренние порты НЕ торчат наружу
ss -tlnp | grep -E '5432|6379|8000|3000'
# Ожидается: пустой вывод — всё закрыто
```

### Просмотр логов

```bash
docker compose logs -f backend    # FastAPI + Alembic миграции
docker compose logs -f frontend   # Nuxt SSR
docker compose logs -f nginx      # доступ и ошибки
docker compose logs -f db         # PostgreSQL
```

---

## 8. Настройка CI/CD (GitHub Actions)

Файл `.github/workflows/deploy.yml` описывает деплой на VPS, который запускается **вручную** (не автоматически).

### Шаг 1: Сгенерировать SSH-ключ для CI

На сервере (или локально, затем скопировать публичный ключ на сервер):

```bash
# Отдельная пара ключей для GitHub Actions — не путать с личным ключом
ssh-keygen -t ed25519 -C "github-actions-deploy" -f ~/.ssh/github_deploy -N ""

# Добавить публичный ключ в authorized_keys на сервере
cat ~/.ssh/github_deploy.pub >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys

# Вывести приватный ключ — скопируете в GitHub Secret
cat ~/.ssh/github_deploy
# Скопируйте ВЕСЬ вывод: от -----BEGIN до -----END включительно
```

### Шаг 2: Добавить секреты в GitHub

Перейдите в репозиторий → **Settings → Secrets and variables → Actions → New repository secret**

| Secret        | Значение |
|---------------|----------|
| `VPS_HOST`    | IP-адрес или домен сервера |
| `VPS_USER`    | SSH-пользователь (`deploy` или `root`) |
| `VPS_SSH_KEY` | Приватный ключ из `cat ~/.ssh/github_deploy` |
| `PROJECT_DIR` | Путь к проекту на сервере, напр. `/opt/ваш-проект` |

### Шаг 3: Тестовый деплой

1. Убедитесь, что CI (тесты) зелёный
2. Перейдите в **Actions → Deploy → Run workflow**
3. Выберите ветку `main` → **Run workflow**

Workflow подключится к серверу по SSH и выполнит:
```bash
git pull origin main
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build --remove-orphans
docker system prune -f
```

> **Подводный камень:** Ошибка `Host key verification failed` — GitHub Actions не знает fingerprint вашего сервера. Решение: добавьте сервер в `known_hosts` через `ssh-keyscan -H ВАШ_IP >> ~/.ssh/known_hosts` и пропишите его в workflow, или добавьте опцию `StrictHostKeyChecking: no` в `appleboy/ssh-action`.

---

## 9. Обновление приложения

### Через GitHub Actions (рекомендуется)

1. Запушьте изменения в `main`
2. Дождитесь зелёного CI
3. **Actions → Deploy → Run workflow → main → Run workflow**

### Вручную с сервера

```bash
cd /opt/ваш-проект
git pull
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build --remove-orphans
```

> **О миграциях:** Alembic запускается автоматически при каждом старте backend-контейнера через `entrypoint.sh`. При обновлении пересобирается только изменившийся сервис — миграции применяются автоматически в процессе перезапуска backend.

### Перезапуск отдельного сервиса

```bash
docker compose restart backend
docker compose restart nginx
```

---

## 10. Мониторинг и обслуживание

### Ресурсы

```bash
docker stats           # CPU/RAM по контейнерам в реальном времени
htop                   # системные ресурсы
df -h                  # дисковое пространство
docker system df       # место под Docker-данные
```

### Бэкап базы данных

```bash
# Создать бэкап
docker compose exec -T db \
  pg_dump -U app_user myapp > backup_$(date +%Y%m%d_%H%M%S).sql

# Восстановить
cat backup.sql | docker compose exec -T db psql -U app_user -d myapp
```

### SSL-сертификат

Сервис `certbot` в `docker-compose.prod.yml` крутится в фоне и проверяет продление каждые 12 часов (само продление происходит только если до истечения ≤ 30 дней).

Для надёжности добавьте cron-задачу, которая после продления перезагружает nginx:

```bash
crontab -e
# Добавить:
0 3 * * * cd /opt/ваш-проект && \
  docker compose -f docker-compose.yml -f docker-compose.prod.yml \
  run --rm certbot renew --quiet && \
  docker compose exec nginx nginx -s reload
```

Проверить статус сертификата:

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml \
  run --rm certbot certificates
```

### Ручное управление миграциями

```bash
docker compose exec backend uv run alembic upgrade head    # применить pending
docker compose exec backend uv run alembic current         # текущее состояние
docker compose exec backend uv run alembic history         # история
docker compose exec backend uv run alembic downgrade -1    # откатить последнюю
```

### Доступ к БД напрямую

```bash
docker compose exec db psql -U app_user -d myapp
```

### Очистка Docker

```bash
docker system prune -f        # образы, контейнеры, сети (volumes НЕ трогает)
docker system prune -f --volumes  # + volumes — ОСТОРОЖНО, удалит данные БД
```

---

## 11. Частые проблемы

### nginx не стартует: `cannot load certificate`

**Причина:** SSL-сертификат ещё не выпущен, nginx не находит файлы в `/etc/letsencrypt/live/`.

**Решение:** Шаг 6 нужно выполнить до запуска стека. Если стек уже запущен:
```bash
docker compose stop nginx
# Выпустить сертификат (шаг 6)
docker compose start nginx
```

---

### 502 Bad Gateway

**Причина:** backend или frontend не запустился или ещё стартует (идут healthcheck-проверки).

**Решение:**
```bash
docker compose ps             # проверить статусы
docker compose logs -f backend
# Подождать — backend делает healthcheck каждые 10 секунд, start_period 20 секунд
```

---

### CORS error в браузере

**Причина:** `CORS_ORIGINS` в `.env` не включает ваш домен.

**Решение:**
```bash
# В .env на сервере:
CORS_ORIGINS=["https://ваш-домен.ru","https://www.ваш-домен.ru"]

docker compose restart backend
```

---

### Nuxt: API-запросы в браузере падают (Network Error / 404)

**Причина:** `NUXT_PUBLIC_API_BASE` указывает на `localhost` (dev-значение из `.env.example`).

**Решение:**
```bash
# В .env на сервере (без /api — иначе запросы уходят на /api/api/...):
NUXT_PUBLIC_API_BASE=https://ваш-домен.ru

docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build frontend
```

---

### Порты 5432 / 6379 / 8000 / 3000 открыты снаружи

**Причина:** Запустили без `-f docker-compose.prod.yml`, либо `docker-compose.override.yml` не был удалён.

**Решение:**
```bash
# Убедиться, что override удалён
ls docker-compose.override.yml   # файла не должно быть

# Перезапустить с prod-конфигом
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

---

### Certbot: `Could not bind to IPv4 or IPv6` (порт 80 занят)

**Причина:** nginx или другой процесс занял порт 80.

**Решение:**
```bash
docker compose stop nginx
# Запустить certbot (шаг 6)
docker compose start nginx
```

---

### Alembic: `Can't connect to the database`

**Причина:** backend стартовал быстрее, чем db прошёл healthcheck (редко, `depends_on: condition: service_healthy` должен это предотвращать).

**Решение:**
```bash
docker compose restart backend
# Или применить вручную:
docker compose exec backend uv run alembic upgrade head
```

---

### DNS не разрешается

**Решение:** Ждите 1–48 часов. Проверяйте:
```bash
nslookup ваш-домен.ru
dig ваш-домен.ru +short
```

---

### GitHub Actions: `Host key verification failed`

**Причина:** Actions не доверяет fingerprint сервера.

**Решение:** добавьте в `deploy.yml` параметр `appleboy/ssh-action`:
```yaml
fingerprint: ${{ secrets.VPS_FINGERPRINT }}
# или отключить проверку (менее безопасно):
# Добавить secrets.VPS_HOST в known_hosts при помощи ssh-keyscan
```

Получить fingerprint: `ssh-keyscan -t ed25519 ВАШ_IP`

---

## Чеклист первого деплоя

**Сервер и сеть:**
- [ ] VPS создан, есть SSH-доступ
- [ ] A-записи домена указывают на IP VPS
- [ ] DNS разрешается: `nslookup ваш-домен.ru` → IP VPS
- [ ] UFW включён, открыты порты 22/80/443
- [ ] Docker установлен: `docker compose version` → v2+

**Проект:**
- [ ] Репозиторий склонирован в `/opt/ваш-проект`
- [ ] `docker-compose.override.yml` удалён с сервера
- [ ] `.env` создан (`./scripts/setup-prod.sh ваш-домен.ru`), все значения заполнены
- [ ] `[DOMAIN]` заменён в `nginx.conf` (скрипт делает это автоматически)

**SSL и запуск:**
- [ ] SSL-сертификат выпущен через certbot standalone
- [ ] `docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build` выполнен
- [ ] `docker compose ps` — все сервисы running/healthy
- [ ] `curl -I https://ваш-домен.ru` → 200 OK
- [ ] `curl https://ваш-домен.ru/api/v1/health` → JSON

**CI/CD (однократно):**
- [ ] SSH-ключ для CI сгенерирован, публичный — добавлен в `authorized_keys`
- [ ] GitHub Secrets настроены: `VPS_HOST`, `VPS_USER`, `VPS_SSH_KEY`, `PROJECT_DIR`
- [ ] Тестовый деплой через Actions → Deploy → Run workflow — прошёл успешно

**Обслуживание:**
- [ ] Cron для продления SSL настроен
- [ ] Бэкап БД настроен (опционально)
