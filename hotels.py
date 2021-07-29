
from typing import Optional
from typing import Union
from requests import request
from json import loads
from datetime import date
from datetime import timedelta


class Hotel:
    """Класс-структура для хранения параметров отелей
    """

    def __init__(
        self, name: str, address: str, distance: float, price: int
    ) -> None:
        self.name = name
        self.address = address
        self.distance = distance
        self.price = price


class HotelsRequest:
    # Заголовки для подключения к API сайта hotels.com
    headers = {
        'x-rapidapi-key': "d8aa339558msh40a8e99abf36cc1p191ffbjsnb76f5d39f02f",
        'x-rapidapi-host': "hotels4.p.rapidapi.com"
    }
    # Максимальное количество отелей в результате поиска
    MAX_CITIES = 10

    def __init__(self) -> None:
        """Инициализация экземпляра класса
        """
        # Поля для промежуточного хранения параметров запроса
        self.request_type: Optional[str] = None
        self.city_id: Optional[int] = None
        self.city_name: Optional[str] = None
        self.min_price: Optional[int] = None
        self.max_price: Optional[int] = None
        self.min_distance: Optional[float] = None
        self.max_distance: Optional[float] = None
        self.hotels_count: Optional[int] = None

    def is_city_exists(self, city_name: str) -> Optional[bool]:
        """Проверка имени города на реальность

        Args:
            city_name (str): Проверяемое имя

        Returns:
            Optional[bool]: None - если в процессе запроса к сайту произошла
                            ошибка (результат не определен)
                            True - реальное имя города
                            False - несуществующее имя города
        """
        # Сылка запроса к сайту
        url = "https://hotels4.p.rapidapi.com/locations/search"
        # Параметры запроса (имя города, язык ответа)
        query_string = {"query": city_name.lower(), "locale": "ru_RU"}
        try:
            response = request(
                "GET",
                url,
                headers=self.headers,
                params=query_string
            )
            # Если запрос не вернул успешный результат
            if response.status_code != 200:
                return None
            response_dict: dict = loads(response.text)
            # Если ответ содержит результаты поиска
            if response_dict.get('moresuggestions', 0) == 0:
                return False
            # Проверяем среди группы города полное совпадение названия
            for item in response_dict['suggestions']:
                if item['group'] == 'CITY_GROUP':
                    for city in item['entities']:
                        if city['name'].lower() == city_name.lower():
                            self.city_id = city['destinationId']
                            self.city_name = city['name'].lower()
                            return True
        except ConnectionError:
            return None
        return False

    def get_responce(self) -> Optional[str]:
        """Получение и разбор результата поиска

        Returns:
            Optional[str]:  форматированная строка с результатами поиска
                            None - если в процессе формирования запроса
                            произошли какие-то ошибки
        """
        # Ссылка запроса к API сайта
        url = "https://hotels4.p.rapidapi.com/properties/list"

        # Параметры запроса
        page_number: int = 1
        query_string: dict[str, Union[int, str]] = {
            "adults1": "1",
            "pageNumber": str(page_number),
            "destinationId": str(self.city_id),
            "checkOut": str(date.today() + timedelta(days=3)),
            "checkIn": str(date.today() + timedelta(days=2)),
            "locale": "ru_RU",
            "pageSize": "25",
            "currency": "RUB"
        }
        if self.request_type == 'lowprice':
            query_string['sortOrder'] = "PRICE"
        elif self.request_type == 'highprice':
            query_string['sortOrder'] = "PRICE_HIGHEST_FIRST"
        elif self.request_type == 'bestdeal':
            query_string["priceMin"] = str(self.min_price)
            query_string["priceMax"] = str(self.max_price)
            query_string['sortOrder'] = "DISTANCE_FROM_LANDMARK"
        else:
            return None
        results_list: list[Hotel] = list()
        finish_loop: bool = False
        try:
            while not finish_loop:
                response = request(
                    "GET",
                    url,
                    headers=self.headers,
                    params=query_string
                )
                # Если запрос вернул не успешный результат
                if response.status_code != 200:
                    return None
                responce_to_dict: dict = \
                    (loads(response.text))['data']['body']['searchResults']
                for hotel in responce_to_dict['results']:
                    distance: Optional[float] = None
                    for landmark in hotel['landmarks']:
                        if landmark['label'] == 'Центр города':
                            distance = float(
                                str(landmark['distance'])
                                .split(sep=' ')[0]
                                .replace(',', '.')
                            )
                        break
                    if self.request_type == 'bestdeal':
                        if distance < self.min_distance:
                            continue
                        if distance > self.max_distance:
                            finish_loop = True
                            break
                    results_list.append(
                        Hotel(
                            name=hotel['name'],
                            address=hotel['address']['streetAddress'],
                            distance=distance,
                            price=int(
                                str(hotel['ratePlan']['price']['current'])
                                .split(sep=' ')[0]
                                .replace(',', '')
                            )
                        )
                    )
                    if len(results_list) == self.hotels_count:
                        finish_loop = True
                        break
                page_number += 1
                query_string["pageNumber"] = str(page_number)
        except ConnectionError:
            return None
        result_str: str = ''
        for hotel in results_list:
            result_str += '*{}*\r\n{}\r\n'.format(
                hotel.name,
                hotel.address
            )
            result_str += '{} км до центра\r\n{} руб.\r\n\r\n'.format(
                hotel.distance,
                hotel.price
            )
        return result_str
