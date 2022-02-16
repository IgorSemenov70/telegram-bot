import datetime
import json
from typing import Tuple, List, Dict, Any
from requests.exceptions import ReadTimeout
import requests
from decouple import config
from telebot.types import InputMediaPhoto

from src.config import URL_PHOTO, URL_SEARCH, HOST, URL_PROPERTIES

API = config('API_TOKEN')
HEADERS = {
    'x-rapidapi-host': HOST,
    'x-rapidapi-key': API
}


def get_location(city: str) -> str:
    """Возвращает id искомого города"""
    html = requests.get(
        url=URL_SEARCH,
        headers=HEADERS,
        params={"query": city, 'locale': 'ru_RU'},
        timeout=15
    )
    data = json.loads(html.text)
    try:
        destination_id = data['suggestions'][0]['entities'][0]['destinationId']
    except KeyError:
        raise KeyError
    return str(destination_id)


def get_photo(hotels_id: int, count_photo: str) -> List | str:
    """Возвращает список фотографий отеля"""
    response = requests.get(
        url=URL_PHOTO,
        headers=HEADERS,
        params={"id": str(hotels_id)},
        timeout=15
    )
    data = json.loads(response.text)
    image_list = []
    try:
        for count, info in enumerate(data['hotelImages']):
            image = info['baseUrl'].replace('{size}', 'b')
            image_list.append(InputMediaPhoto(image))
            if count == int(count_photo) - 1:
                break
    except KeyError:
        return []
    return image_list


def time_for_the_week_ahead(check_in_date: str, check_out_date: str) -> str:
    """Возвращает количество дней проживания в отеле"""
    quantity_days = (datetime.datetime.strptime(check_out_date, '%Y-%m-%d') -
                     datetime.datetime.strptime(check_in_date, '%Y-%m-%d')).days
    if quantity_days == 1:
        result_str = f'{quantity_days} ночь'
    elif quantity_days in [2, 3, 4]:
        result_str = f'{quantity_days} ночи'
    else:
        result_str = f'{quantity_days} ночей'
    return result_str


def get_queryset_for_lowerprice_and_highprice(destination_id: str, check_in_date: str, check_out_date: str,
                                              sortorder: str
                                              ) -> Dict[str, str]:
    """Возвращает словарь с параметрами для поиска через команды /lowprice и /highprice"""
    querystring = {"destinationId": destination_id, "pageNumber": "1", "pageSize": "25", "checkIn": check_in_date,
                   "checkOut": check_out_date, "adults1": "1", "sortOrder": sortorder, "locale": "ru_RU",
                   "currency": "RUB"}
    return querystring


def get_queryset_for_bestdeal(destination_id: str, check_in_date: str, check_out_date: str, price_range: str
                              ) -> Dict[str, str]:
    """Возвращает словарь с параметрами для поиска через команду /bestdeal"""
    price_min, price_max = _convert_price(price_range=price_range)
    querystring = {"destinationId": destination_id, "pageNumber": "1", "pageSize": "25", "checkIn": check_in_date,
                   "checkOut": check_out_date, "adults1": "1", "priceMin": price_min, "priceMax": price_max,
                   "locale": "ru_RU", "currency": "RUB"}
    return querystring


def _convert_price(price_range: str) -> Tuple[str, str]:
    """Возвращает диапазон цен в формате для поиска"""
    price_min = price_range.split('/')[0]
    price_max = price_range.split('/')[1]
    return price_min, price_max


def get_properties_list(querystring: Dict[str, str]):
    """Возвращает словарь с информацией о найденных отелей"""
    try:
        html = requests.get(url=URL_PROPERTIES, headers=HEADERS, params=querystring, timeout=15)
        return json.loads(html.text)
    except ReadTimeout:
        return


def unpacking_hotels_lowprice_and_highprice(
        data: Dict, show_photo: str, quantity_photo: str, quantity_hotels: str, quantity_days: str
) -> Dict[str, Any] | bool:
    """Возвращает итоговую информацию по отелям пользователю для команды /lowprice и /highprice"""
    info_hotels: Dict = {}
    try:
        hotels_list = data['data']['body']['searchResults']['results']
        if show_photo == 'да':
            for count, item in enumerate(hotels_list):
                if 'streetAddress' in item['address']:
                    info_hotels[count + 1] = {
                        'id': item['id'],
                        'name': item['name'],
                        'address': item['address']['streetAddress'],
                        'distance': item['landmarks'][0]['distance'],
                        'price': f"{str(float(item['ratePlan']['price']['exactCurrent']))} рублей за {quantity_days}",
                        'photo': get_photo(hotels_id=item['id'], count_photo=quantity_photo)}
                else:
                    info_hotels[count + 1] = {
                        'id': item['id'],
                        'name': item['name'],
                        'address': item['address']['locality'],
                        'distance': item['landmarks'][0]['distance'],
                        'price': f"{str(float(item['ratePlan']['price']['exactCurrent']))} рублей за {quantity_days}",
                        'photo': get_photo(hotels_id=item['id'], count_photo=quantity_photo)}
                if count == int(quantity_hotels) - 1:
                    break
        else:
            for count, item in enumerate(hotels_list):
                if 'streetAddress' in item['address']:
                    info_hotels[count + 1] = {
                        'id': item['id'],
                        'name': item['name'],
                        'address': item['address']['streetAddress'],
                        'distance': item['landmarks'][0]['distance'],
                        'price': f"{str(float(item['ratePlan']['price']['exactCurrent']))} рублей за {quantity_days}"}
                else:
                    info_hotels[count + 1] = {
                        'id': item['id'],
                        'name': item['name'],
                        'address': item['address']['locality'],
                        'distance': item['landmarks'][0]['distance'],
                        'price': f"{str(float(item['ratePlan']['price']['exactCurrent']))} рублей за {quantity_days}"}
                if count == int(quantity_hotels) - 1:
                    break
        return info_hotels
    except KeyError:
        return False


def unpacking_hotels_bestdeal(
        data: Dict, show_photo: str, quantity_photo: str, quantity_hotels: str, quantity_days: str, distance: str
) -> Dict[str, Any] | bool:
    """Возвращает итоговую информацию по отелям пользователю для команды /bestdeal"""
    info_hotels: Dict = {}
    try:
        hotels_list = data['data']['body']['searchResults']['results']
        if show_photo == 'да':
            for count, item in enumerate(hotels_list):
                if ('streetAddress' in item['address'] and float(distance) >= float(
                        item['landmarks'][0]['distance'].strip(' км').replace(',', '.'))):
                    info_hotels[count + 1] = {
                        'id': item['id'],
                        'name': item['name'],
                        'address': item['address']['streetAddress'],
                        'distance': item['landmarks'][0]['distance'],
                        'price': f"{str(float(item['ratePlan']['price']['exactCurrent']))} рублей за {quantity_days}",
                        'photo': get_photo(hotels_id=item['id'], count_photo=quantity_photo)}
                elif float(distance) >= float(
                        item['landmarks'][0]['distance'].strip(' км').replace(',', '.')):
                    info_hotels[count + 1] = {
                        'id': item['id'],
                        'name': item['name'],
                        'address': item['address']['locality'],
                        'distance': item['landmarks'][0]['distance'],
                        'price': f"{str(float(item['ratePlan']['price']['exactCurrent']))} рублей за {quantity_days}",
                        'photo': get_photo(hotels_id=item['id'], count_photo=quantity_photo)}
                if count == int(quantity_hotels) - 1:
                    break
        else:
            for count, item in enumerate(hotels_list):
                if ('streetAddress' in item['address'] and float(distance) >= float(
                        item['landmarks'][0]['distance'].strip(' км').replace(',', '.'))):
                    info_hotels[count + 1] = {
                        'id': item['id'],
                        'name': item['name'],
                        'address': item['address']['streetAddress'],
                        'distance': item['landmarks'][0]['distance'],
                        'price': f"{str(float(item['ratePlan']['price']['exactCurrent']))} рублей за {quantity_days}"}
                elif float(distance) >= float(
                        item['landmarks'][0]['distance'].strip(' км').replace(',', '.')):
                    info_hotels[count + 1] = {
                        'id': item['id'],
                        'name': item['name'],
                        'address': item['address']['locality'],
                        'distance': item['landmarks'][0]['distance'],
                        'price': f"{str(float(item['ratePlan']['price']['exactCurrent']))} рублей за {quantity_days}"}
                if count == int(quantity_hotels) - 1:
                    break
        return info_hotels
    except KeyError:
        return False
