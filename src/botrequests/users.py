from typing import Optional


class User:
    """Класс для сбора информации по пользователям"""
    users = dict()

    def __init__(self, user_id: int) -> None:
        self.id = user_id
        self.command: str = ''
        self.sortorder: str = ''
        self.city: str = ''
        self.quantity_hotels: str = ''
        self.show_photo: str = ''
        self.quantity_photo: str = ''
        self.price_range: str = ''
        self.distance: str = ''
        self.check_in_date: str = ''
        self.check_out_date: str = ''
        User.add_user(user_id, self)

    @classmethod
    def add_user(cls, user_id: int, user: Optional['User']) -> None:
        cls.users[user_id] = user

    @classmethod
    def get_user(cls, user_id) -> Optional['User']:
        if user_id in cls.users:
            return cls.users[user_id]
        else:
            return User(user_id)

    def clear_user_info(self) -> None:
        """ Очищает накопленную информацию по пользователю"""
        self.command: str = ''
        self.sortorder: str = ''
        self.city: str = ''
        self.quantity_hotels: str = ''
        self.show_photo: str = ''
        self.quantity_photo: str = ''
        self.price_range: str = ''
        self.distance: str = ''
        self.check_in_date: str = ''
        self.check_out_date: str = ''
