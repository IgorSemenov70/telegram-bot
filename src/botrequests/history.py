import sqlite3
import datetime
from typing import List


class SQLighter:
    def __init__(self, database: str) -> None:
        self.connection = sqlite3.connect(database)
        self.cursor = self.connection.cursor()
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS users(
            user_id INTEGER,
            command varchar,
            date current_date,
            hotels_name varchar,
            address varchar,
            distance_from_center varchar,
            price varchar);
            """)
        self.connection.commit()

    def close(self) -> None:
        self.connection.close()

    def safe_user_info(self, user_id: int, command: str, hotels_name: str, address: str, distance_from_center: str,
                       price: str) -> None:
        date_now = datetime.datetime.now()
        date = datetime.datetime.strftime(date_now, '%Y-%m-%d %H:%M:%S')
        with self.connection:
            q = """INSERT INTO `users` (user_id, command, date, hotels_name, address, distance_from_center, price) 
                        VALUES (?, ?, ?, ?, ?, ?, ?);
                """
            self.cursor.execute(q, (user_id, command, date, hotels_name, address, distance_from_center, price))

    def get_user_info(self, user_id: str) -> List:
        with self.connection:
            q = """SELECT command, date, hotels_name, address, distance_from_center, price
                        FROM `users` 
                        WHERE user_id = ?
                        LIMIT 5;
                        """
            self.cursor.execute(q, (user_id,))
            return self.cursor.fetchall()
