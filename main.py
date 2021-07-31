from bot import HotelsBot
from telebot.types import Message
from env import BOT_TOKEN


# Создание объекта класса телеграм бота
bot = HotelsBot(BOT_TOKEN)


# Перехват всех текстовых сообщений к боту и направление их на фукцию парсинга
@bot.message_handler(func=lambda message: True, content_types=['text'])
def get_command(message: Message) -> None:
    """Функция перехвата входящих к телеграм боту сообщений

    Args:
        message (Message): объект-сообщение API телеграма
    """
    bot.parse_command(message)


# Бесконечный постоянный опрос телеграма о новых сообщениях
bot.polling(none_stop=True, interval=0)
