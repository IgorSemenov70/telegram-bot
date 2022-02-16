# <p align="center">Telegram-бот для анализа сайта Hotels.com и поиска подходящих пользователю отелей </p>

## Особенности
- /help — помощь по командам бота
- /lowprice — вывод самых дешёвых отелей в городе
- /highprice — вывод самых дорогих отелей в городе
- /bestdeal — вывод отелей, наиболее подходящих по цене и расположению от центра
- /history — вывод истории поиска отелей

## Инструкция по установке:
1 Установить зависимости:
```
pip install -r requirements.txt
```
2) В Telegram написать @BotFather, /start, или /newbot, получить сообщение с токеном бота.
3) Настроить переменные среды, по шаблону .env.template
`BOT_TOKEN=Ваш_токен`
`API_TOKEN, URL_SEARCH, URL_PROPERTIES, URL_PHOTO` - взять с сайта <a href="https://rapidapi.com/ru/apidojo/api/hotels4/">rapidapi.com</a>
## Запустить локально
```
git clone https://github.com/IgorSemenov70/telegram-bot
cd telegram-bot
pip install -r requirements.txt
python main.py
```
## Author
- [GitHub](https://github.com/IgorSemenov70)

## Контакты:
- [Telegram](https://t.me/igor_Semenov70/)
- [Instagram](https://www.instagram.com/igor_semenov70/)

## Обратная связь
Если у вас есть какие-либо отзывы, пожалуйста, свяжитесь с мной по вышеуказанным контактам.