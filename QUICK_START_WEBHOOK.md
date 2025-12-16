# Быстрый старт: Настройка Webhook

## Шаг 1: Установите зависимости

```bash
pip install -r requirements.txt
```

## Шаг 2: Настройте .env файл

Добавьте в `.env`:

```env
WEBHOOK_HOST=https://yourdomain.com  # Замените на ваш домен
```

## Шаг 3: Убедитесь, что у вас есть HTTPS

Telegram требует HTTPS для webhook. Варианты:
- Используйте Cloudflare (бесплатно, автоматический SSL)
- Используйте Let's Encrypt
- Используйте коммерческий SSL

## Шаг 4: Запустите веб-сервер

```bash
python3 webhook_server.py
```

Сервер автоматически:
- Установит webhook при запуске
- Будет обрабатывать обновления от Telegram
- Удалит webhook при остановке

## Шаг 5: Проверьте работу

В другом терминале:

```bash
# Проверьте информацию о webhook
python3 set_webhook.py info

# Отправьте боту /start и проверьте логи
tail -f bot.log
```

## Альтернатива: Ручная настройка

Если у вас уже есть веб-сервер:

```bash
# Установите webhook
python3 set_webhook.py https://yourdomain.com/webhook

# Проверьте информацию
python3 set_webhook.py info

# Удалите webhook (если нужно)
python3 set_webhook.py delete
```

## Важно!

⚠️ **Не запускайте одновременно `main.py` (polling) и `webhook_server.py` (webhook)** - это вызовет конфликт!

- Для локальной разработки: используйте `python3 main.py`
- Для продакшн-сервера: используйте `python3 webhook_server.py`

## Проблемы?

См. подробную инструкцию в `WEBHOOK_SETUP.md`


