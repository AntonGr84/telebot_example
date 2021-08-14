from typing import Optional
from telebot import TeleBot
from telebot.types import Message
from hotels import HotelsRequest


class HotelsBot(TeleBot):
    """Класс-потомок класса телеграм бота для
        инкапсуляции дополнительных методов в класс

    Args:
        TeleBot: класс-родитель
    """

    # Текст описания
    _about_text = \
        'Я помогу тебе найти подходящие отели в разных городах мира'
    # Текст заголовка команд
    _commands_title = \
        'Ты можешь использовать следующие команды:'

    # Текст помощи по командам
    _commands_help = \
        '/help - вывести справку по командам\r\n' + \
        '/lowprice - самые дешевые отели \r\n' + \
        '/highprice - самые дорогие отели\r\n' + \
        '/bestdeal - самые дешевые отели, но ближе всего к центру'

    # Словарь для хранения запросов пользователя
    _users_cookies: dict[int, HotelsRequest] = dict()

    # Шаги по получению информации от пользователя для формирования запроса
    def _get_city_name(self, message: Message) -> None:
        """Функция получения имени города из сообщения к боту

        Args:
            message (Message): объект-сообщение к боту
        """
        # Проверка имени города на реальность
        isCityExists: Optional[bool] = \
            self._users_cookies[message.chat.id].is_city_exists(message.text)
        if isCityExists is None:
            self.send_message(
                message.chat.id,
                'Упс. Что-то пошло не так, попробуйте снова'
            )
            return
        if not isCityExists:
            self.send_message(
                message.chat.id,
                'Города с таким именем не существует'
            )
            return
        # Определяем следущих шаг бота
        if self._users_cookies[message.chat.id].request_type == 'bestdeal':
            self.send_message(
                message.chat.id,
                'Какая минимальная цена (целое число)?'
            )
            self.register_next_step_handler(message, self._get_min_price)
        else:
            self.send_message(
                message.chat.id,
                'Сколько отелей ты хочешь найти?'
            )
            self.register_next_step_handler(message, self._get_hotels_count)

    def _get_min_price(self, message: Message) -> None:
        """Получение значения минимальной стоимости для фильтрации из сообщения к боту

        Args:
            message (Message): объект-сообщение к боту
        """
        try:
            self._users_cookies[message.chat.id].min_price = int(message.text)
        except ValueError:
            self.send_message(
                message.chat.id,
                'Неправильно указана минимальная цена'
            )
            return
        self.send_message(
            message.chat.id,
            'Какая максимальная цена (целое число)?'
        )
        # Следующий шаг
        self.register_next_step_handler(message, self._get_max_price)

    def _get_max_price(self, message: Message) -> None:
        """Получение значения максимальной стоимости для фильтрации из сообщения к боту

        Args:
            message (Message): объект-сообщение к боту
        """
        try:
            self._users_cookies[message.chat.id].max_price = int(message.text)
        except ValueError:
            self.send_message(
                message.chat.id,
                'Неправильно указана максимальная цена'
            )
            return
        self.send_message(
            message.chat.id,
            'Какое минимальное расстояние до центра в километрах ' +
            '(можно с запятой)?'
        )
        # Следующий шаг
        self.register_next_step_handler(message, self._get_min_distance)

    def _get_min_distance(self, message: Message) -> None:
        """Получение значения минимальной дистанции до центра
        для фильтрации из сообщения к боту

        Args:
            message (Message): объект-сообщение к боту
        """
        try:
            distance_str = message.text.replace(',', '.')
            self._users_cookies[message.chat.id].min_distance = \
                float(distance_str)
        except ValueError:
            self.send_message(
                message.chat.id,
                'Неправильно указана минимальная дистанция'
            )
            return
        self.send_message(
            message.chat.id,
            'Какое максимальное расстояние до центра в километрах ' +
            '(можно с запятой)?'
        )
        # Следующий шаг
        self.register_next_step_handler(message, self._get_max_distance)

    def _get_max_distance(self, message: Message) -> None:
        """Получение значения максимальной дистанции до центра
        для фильтрации из сообщения к боту

        Args:
            message (Message): объект-сообщение к боту
        """
        try:
            distance_str = message.text.replace(',', '.')
            self._users_cookies[message.chat.id].max_distance = \
                float(distance_str)
        except ValueError:
            self.send_message(
                message.chat.id,
                'Неправильно указана максимальная дистанция'
            )
            return
        self.send_message(
            message.chat.id,
            'Сколько отелей ты хочешь найти?'
        )
        # Следующий шаг
        self.register_next_step_handler(message, self._get_hotels_count)

    def _get_hotels_count(self, message: Message) -> None:
        """Получение количества отелей для поиска для фильтрации из сообщения к боту

        Args:
            message (Message): объект-сообщение к боту
        """
        try:
            # Проверяем на соответствие максимальному значению отелей в поиске
            if int(message.text) > HotelsRequest.MAX_CITIES:
                self._users_cookies[message.chat.id].hotels_count = \
                    HotelsRequest.MAX_CITIES
                self.send_message(
                    message.chat.id,
                    'Ты указал слишком много отелей, найду 10, больше не могу'
                )
            else:
                self._users_cookies[message.chat.id].hotels_count =\
                    int(message.text)
        except ValueError:
            self.send_message(
                message.chat.id,
                'Неверное количество отелей, найду максимально, 10 штук'
            )
            self._users_cookies[message.chat.id].hotels_count = \
                HotelsRequest.MAX_CITIES
        # Выполняем поис отелей и выводим результат в бота
        responce_text = self._users_cookies[message.chat.id].get_responce()
        if responce_text is None:
            self.send_message(
                message.chat.id,
                'Упс. Что-то пошло не так, попробуйте снова'
            )
            return
        if responce_text == '':
            self.send_message(
                message.chat.id,
                'Ничего не найдено, сделай запрос помягче'
            )
            return
        self.send_message(
            message.chat.id,
            responce_text,
            parse_mode='Markdown'
        )

    def _hello(self, chat_id: int) -> None:
        """Ответ на запрос "Привет"

        Args:
            chat_id (int): идентификатор чата для ответа
        """
        responce_text = 'Привет!\r\n{0}\r\n\r\n{1}\r\n{2}'.format(
            self._about_text,
            self._commands_title,
            self._commands_help
        )
        self.send_message(chat_id, responce_text)

    def _start(self, chat_id: int) -> None:
        """Ответ на команду /start

        Args:
            chat_id (int): идентификатор чата для ответа
        """
        responce_text = '{0}\r\n\r\n{1}\r\n{2}'.format(
            self._about_text,
            self._commands_title,
            self._commands_help
        )
        self.send_message(chat_id, responce_text)

    def _help(self, chat_id: int) -> None:
        """Ответ на команду /help

        Args:
            chat_id (int): идентификатор чата для ответа
        """
        responce_text = '{0}\r\n{1}'.format(
            self._commands_title,
            self._commands_help
        )
        self.send_message(chat_id, responce_text)

    def _unknown(self, chat_id: int) -> None:
        """Ответ на неизвестную команду

        Args:
            chat_id (int): идентификатор чата для ответа
        """
        responce_text = \
            'Не могу понять команду\r\n\r\n{0}\r\n{1}'.format(
                self._commands_title,
                self._commands_help
            )
        self.send_message(chat_id, responce_text)

    def parse_command(self, message: Message) -> None:
        """Разбор полученнго сообщение, поиск команды

        Args:
            message (Message): объект-сообщение к боту
        """
        if message.text == 'Привет':
            self._hello(message.chat.id)
        elif message.text == '/start':
            self._start(message.chat.id)
        elif message.text == '/help':
            self._help(message.chat.id)
        elif (
            message.text == '/lowprice' or
            message.text == '/highprice' or
            message.text == '/bestdeal'
        ):
            # Удаляем историю предыдущего поиска
            if message.chat.id in self._users_cookies:
                del self._users_cookies[message.chat.id]
            # Создаем новую историю поиска
            self._users_cookies[message.chat.id] = HotelsRequest()
            self._users_cookies[message.chat.id].request_type = \
                message.text[1:]
            self.send_message(message.chat.id, 'В каком городе ищешь?')
            self.register_next_step_handler(message, self._get_city_name)
        else:
            self._unknown(message.chat.id)
