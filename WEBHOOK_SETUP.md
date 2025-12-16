# Настройка Webhook для Telegram бота

## Что такое Webhook?

Webhook - это способ получения обновлений от Telegram через HTTP запросы вместо постоянного polling. Это более эффективно для продакшн-серверов.

## Требования

1. **Публичный HTTPS URL** - Telegram требует HTTPS для webhook
2. **Сервер с публичным IP/доменом**
3. **SSL сертификат** (можно использовать Let's Encrypt)

## Установка зависимостей

```bash
pip install -r requirements.txt
```

## Настройка переменных окружения

Добавьте в `.env` файл:

```env
BOT_TOKEN=your_bot_token
WEBHOOK_HOST=https://yourdomain.com  # Ваш публичный домен
WEBAPP_HOST=0.0.0.0                  # Хост для веб-сервера (обычно 0.0.0.0)
WEBAPP_PORT=8443                      # Порт для веб-сервера (обычно 8443)
```

## Вариант 1: Использование готового веб-сервера (webhook_server.py)

### Запуск сервера:

```bash
python3 webhook_server.py
```

Или с указанием хоста и порта:

```bash
python3 webhook_server.py 0.0.0.0 8443
```

### Что делает скрипт:

1. Автоматически устанавливает webhook при запуске
2. Запускает веб-сервер на указанном порту
3. Обрабатывает входящие обновления от Telegram
4. Автоматически удаляет webhook при остановке

### Использование с Nginx (рекомендуется):

Если у вас есть Nginx, настройте reverse proxy:

```nginx
server {
    listen 443 ssl;
    server_name yourdomain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location /webhook {
        proxy_pass http://127.0.0.1:8443;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Вариант 2: Ручная настройка webhook

### 1. Установить webhook:

```bash
python3 set_webhook.py https://yourdomain.com/webhook
```

### 2. Проверить информацию о webhook:

```bash
python3 set_webhook.py info
```

### 3. Удалить webhook:

```bash
python3 set_webhook.py delete
```

## Вариант 3: Использование с существующим веб-сервером

Если у вас уже есть веб-сервер (Flask, FastAPI, Django), вы можете интегрировать обработку webhook:

### Пример для Flask:

```python
from flask import Flask, request
import asyncio
from aiogram import Bot, Dispatcher

app = Flask(__name__)
bot = Bot(token="YOUR_TOKEN")
dp = Dispatcher()

@app.route('/webhook', methods=['POST'])
def webhook():
    update = request.get_json()
    # Обработка обновления
    asyncio.create_task(dp.feed_update(bot, update))
    return 'OK', 200
```

## Проверка работы

1. Установите webhook: `python3 set_webhook.py https://yourdomain.com/webhook`
2. Проверьте информацию: `python3 set_webhook.py info`
3. Отправьте боту сообщение `/start`
4. Проверьте логи сервера

## Устранение проблем

### Ошибка "Conflict: terminated by other getUpdates request"

Это означает, что где-то еще запущен polling. Решение:
1. Остановите все процессы с `main.py`
2. Удалите webhook: `python3 set_webhook.py delete`
3. Подождите 5-10 минут
4. Установите webhook заново

### Webhook не работает

1. Проверьте, что URL доступен из интернета: `curl https://yourdomain.com/webhook`
2. Проверьте SSL сертификат: `curl -v https://yourdomain.com/webhook`
3. Проверьте логи сервера
4. Проверьте информацию о webhook: `python3 set_webhook.py info`

### Проблемы с SSL

Telegram требует валидный SSL сертификат. Используйте:
- Let's Encrypt (бесплатно)
- Cloudflare (бесплатно с автоматическим SSL)
- Коммерческий SSL сертификат

## Переключение между Polling и Webhook

### Для локальной разработки (Polling):

```bash
python3 main.py
```

### Для продакшн-сервера (Webhook):

```bash
python3 webhook_server.py
```

## Автозапуск на сервере

### Использование systemd:

Создайте файл `/etc/systemd/system/telegram-bot.service`:

```ini
[Unit]
Description=Telegram Bot Webhook Server
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/tgbot
Environment="PATH=/usr/bin:/usr/local/bin"
ExecStart=/usr/bin/python3 /path/to/tgbot/webhook_server.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Затем:

```bash
sudo systemctl enable telegram-bot
sudo systemctl start telegram-bot
sudo systemctl status telegram-bot
```

## Мониторинг

Проверяйте логи регулярно:

```bash
tail -f bot.log
```

Или если используете systemd:

```bash
sudo journalctl -u telegram-bot -f
```


