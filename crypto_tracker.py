# Импорт необходимых библиотек
import logging
import json
from telegram.ext import Updater, CommandHandler
from requests import Request, Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects

# Логирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG
)

logger = logging.getLogger(__name__)

# Токен от BotFarther
TOKEN = '5377290425:AAELQjxgw1hPhlJeHLpUWLEXU9pigfHQreA'

dict1 = {}
file_txt = 'users.json'


# Вызов /start
def start(update, context):
    update.message.reply_text("Актуальные курсы криптовалюты!")


# Функция, которая выводит пользователю актуальный курс криптовалюты
def price(update, context):
    try:
        # Название криптовалюты
        method = str(context.args[0]).lower()
        currency = str(context.args[1]).lower()
        if method != 'slug' and method != 'symbol':
            update.message.reply_text("Первое значение - slug или method")
            return
    except IndexError:
        update.message.reply_text("Передайте метод и название")
        return

    # API CoinMarketCap
    url = 'https://pro-api.coinmarketcap.com/v2/cryptocurrency/quotes/latest'

    # Информация, нужная для парсинга
    parameters = {
        method: currency,
        'convert': 'USD'
    }

    # Token CoinMarketCap и формат файла
    headers = {
        'Accepts': 'application/json',
        'X-CMC_PRO_API_KEY': 'c50f0aff-2673-4c2f-82f4-0725ecf14659'
    }

    session = Session()
    session.headers.update(headers)

    try:
        # Получение json файла
        response = session.get(url, params=parameters)
        #  Преобразование json, чтобы с ним мог работать python
        data = json.loads(response.text)
        # Получение id для будущей работы с json
        try:
            for entry in data['data']:
                coin_id = entry
            # Название - разные запросы для разных методов
            if method == 'slug':
                coin = data['data'][coin_id]['name']
            elif method == 'symbol':
                coin = data['data'][coin_id][0]['name']
            if method == 'slug':
                # Цена
                actual_price = data['data'][coin_id]['quote']['USD']['price']
                # Изменение цены за час, 24 часа и неделю
                change1h = data['data'][coin_id]['quote']['USD']['percent_change_1h']
                change24h = data['data'][coin_id]['quote']['USD']['percent_change_24h']
                change7d = data['data'][coin_id]['quote']['USD']['percent_change_7d']
            elif method == 'symbol':
                # Цена
                actual_price = data['data'][coin_id][0]['quote']['USD']['price']
                # Изменение цены за час, 24 часа и неделю
                change1h = data['data'][coin_id][0]['quote']['USD']['percent_change_1h']
                change24h = data['data'][coin_id][0]['quote']['USD']['percent_change_24h']
                change7d = data['data'][coin_id][0]['quote']['USD']['percent_change_7d']
            # Округление значений
            actual_price, change1h, change24h = round(actual_price, 2), round(change1h, 1), round(change24h, 1)
            change7d = round(change7d, 1)
            # Рост или падение в зависимости от изменения цены
            change1h_text = 'Падение' if change1h < 0.0 else 'Рост'
            change24h_text = 'Падение' if change24h < 0.0 else 'Рост'
            change7d_text = 'Падение' if change7d < 0.0 else 'Рост'
            # Вывод текста пользователю бота
            update.message.reply_text(f'Цена {coin} на данный момент: {actual_price}$\n'
                                      f'{change1h_text} цены за час: {change1h}%\n'
                                      f'{change24h_text} цены за сутки: {change24h}%\n'
                                      f'{change7d_text} цены за неделю: {change7d}%')
        # Пользователь ввел неверное название криптовалюты
        except KeyError:
            update.message.reply_text('Неверное название криптовалюты')
    # На случай, если у CoinMarketCap проблемы
    except (ConnectionError, Timeout, TooManyRedirects):
        update.message.reply_text('Попробуйте позже')


# Функция, которая возвращает цену
def get_price(coin):
    global file_txt
    url = 'https://pro-api.coinmarketcap.com/v2/cryptocurrency/quotes/latest'

    parameters = {
        'slug': coin,
        'convert': 'USD'
    }

    headers = {
        'Accepts': 'application/json',
        'X-CMC_PRO_API_KEY': 'c50f0aff-2673-4c2f-82f4-0725ecf14659'
    }

    session = Session()
    session.headers.update(headers)

    try:
        response = session.get(url, params=parameters)
        data = json.loads(response.text)
        for entry in data['data']:
            coin_id = entry
        # Получение цены
        actual_price = data['data'][coin_id]['quote']['USD']['price']
        actual_price = round(actual_price, 2)
        # Возвращение цены
        return round(actual_price, 1)
    # Если CoinMarketCap не отвечает
    except (ConnectionError, Timeout, TooManyRedirects):
        logging.warning('CoinMarketCap не отвечает')


# /portfolio - информация о командах для управления своим крипто портфелем
def portfolio(update, context):
    global file_txt
    update.message.reply_text('Вы можете отслеживать свой крипто портфель через телеграм\n'
                              'Используйте команды /add coin amount, /delete coin\n'
                              '/change_amount coin amount /view для управления портфелем')


# Добавление криптовалюты в портфель
def add(update, context):
    global dict1, file_txt
    # Словарь и имя файла json
    with open(file_txt) as file:
        # Получение предыдущих данных из json на случай перезапуска программы
        json_str = file.read()
        json_data = json.loads(json_str)
    # И запись этих данных в словарь для работы в python
    dict1 = json_data
    try:
        # Получение аргументов имени криптовалюты и количества монет
        coin = str(context.args[0])
        amount = float(context.args[1])
        if amount < 0:
            # Нельзя добавить отрицательное количество монет
            update.message.reply_text('Количество не может быть отрицательным')
            return
        try:
            # Проверка, существует ли такая криптовалюта
            get_price(coin)
        except KeyError:
            # Введено неверное название
            update.message.reply_text('Введите верное название криптовалюты')
            return
    except IndexError:
        # Введено меньше двух значений
        update.message.reply_text('Первое значение - название, второе число')
        return
    except ValueError:
        # Второй аргумент функции - не число
        update.message.reply_text('Второе значение - число')
        return
    # Username пользователя Telegram
    username = update.message.chat.username
    # Пользователь еще не создал свой список активов
    if str(username) not in dict1:
        # Добавление значений в словарь
        dict1[str(username)] = {coin: amount}
        update.message.reply_text('Токен успешно добавлен в ваш портфель')
    else:
        # Пользователь ранее уже добавлял активы
        d = dict1[username]
        # Получение списка активов пользователя
        if coin in d:
            # Эта монета уже добавлена в портфель
            update.message.reply_text('В вашем портфолио уже есть этот токен,\n'
                                      'для изменения количества используйте /change_amount')
        else:
            # Добавление монеты и ее количества в словарь
            d[coin] = amount
            update.message.reply_text('Токен успешно добавлен в ваш портфель')
        dict1[username] = d
    # Запись словаря в json файл
    with open(file_txt, 'w') as file:
        json.dump(dict1, file, ensure_ascii=False, indent=2)


# Функция, которая удаляет криптовалюту из списка активов
def delete(update, context):
    global dict1, file_txt
    with open(file_txt) as file:
        json_str = file.read()
        json_data = json.loads(json_str)
    dict1 = json_data
    try:
        # На вход только название монеты
        # Дальше все похоже на функцию add
        coin = str(context.args[0])
        try:
            get_price(coin)
        except KeyError:
            update.message.reply_text('Введите верное название криптовалюты')
            return
    except IndexError:
        update.message.reply_text('Передайте единственное значение - название криптовалюты')
        return
    username = update.message.chat.username
    if username not in dict1:
        # Сначала нужно добавить активы
        update.message.reply_text('Чтобы что-то удалить, сначала нужно что-то добавить')
    else:
        d = dict1[username]
        if coin in d:
            # Если монета есть в крипто портфеле пользователя, то она удаляется
            del d[coin]
            update.message.reply_text('Этот токен успешно удален из вашего портфеля')
        else:
            # Если монеты нет, пользователь получает соответсвующее сообщение
            update.message.reply_text('Этого токена нет в вашем портфеле')
        dict1[username] = d
    with open('users.json', 'w') as file:
        json.dump(dict1, file, ensure_ascii=False, indent=2)


# Изменение количества монет
def change_amount(update, context):
    global dict1, file_txt
    flag = True
    with open(file_txt) as file:
        # На вход получает название монеты и ее количество
        json_str = file.read()
        json_data = json.loads(json_str)
    dict1 = json_data
    # Дальше все похоже на функцию add
    try:
        coin = str(context.args[0])
        amount = float(context.args[1])
        try:
            get_price(coin)
        except KeyError:
            update.message.reply_text('Введите верное название криптовалюты')
    except IndexError:
        update.message.reply_text('Первое значение - название, второе число')
    except ValueError:
        update.message.reply_text('Второе значение - число')
    username = update.message.chat.username
    d = dict1[username]
    # Количество монет не может быть отрицательным
    if d[coin] + amount < 0:
        del d[coin]
        flag = False
        update.message.reply_text('В вашем портфеле больше нет этой монеты')
    if str(username) not in dict1:
        # Для изменения количества монет нужно сначала добавить их
        update.message.reply_text('Сначала добавьте токены в портфель')
    else:
        if coin in d:
            # Изменение количества монет
            d[coin] = d[coin] + amount
            dict1[username] = d
            update.message.reply_text(f'Количество монет {coin} изменено')
        else:
            # Если пользователь не получил сообщение об удалении монеты
            if flag:
                update.message.reply_text('Этой криптовалюты нету в вашем портфеле,\n'
                                          'используйте функцию /add coin amount')
        dict1[username] = d
    with open(file_txt, 'w') as file:
        json.dump(dict1, file, ensure_ascii=False, indent=2)


# Получение данных об активах
def view(update, context):
    global dict1
    with open(file_txt) as file:
        json_str = file.read()
        json_data = json.loads(json_str)
    dict1 = json_data
    username = update.message.chat.username
    d = dict1[username]
    # Сумма всех активов
    sum_ = 0
    for i in d:
        # i - название криптовалюты
        sum_ += get_price(i) * d[i]
        # Увеличение суммы и вывод сообщения на экран пользователю
        update.message.reply_text(f'Монет {i} на сумму: {get_price(i) * d[i]}$')
    # общая сумма
    update.message.reply_text(f'Общая сумма ваших активов составляет: {sum_}$')


# Запуск скрипта
def main():
    updater = Updater(TOKEN)
    dp = updater.dispatcher
    # Регистрация в диспетчере
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("price", price))
    dp.add_handler(CommandHandler("portfolio", portfolio))
    dp.add_handler(CommandHandler("add", add))
    dp.add_handler(CommandHandler("delete", delete))
    dp.add_handler(CommandHandler("change_amount", change_amount))
    dp.add_handler(CommandHandler("view", view))
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
