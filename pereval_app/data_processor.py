import os
import psycopg2
from psycopg2 import sql
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)


class DatabaseConnector:
    """Класс для подключения к базе данных"""

    def __init__(self):
        self.conn = None
        self.cursor = None

    def connect(self):
        """Установка соединения с БД"""
        try:
            self.conn = psycopg2.connect(
                host=os.getenv('FSTR_DB_HOST', 'localhost'),
                port=os.getenv('FSTR_DB_PORT', '5432'),
                database=os.getenv('FSTR_DB_NAME', 'pereval'),
                user=os.getenv('FSTR_DB_LOGIN', 'postgres'),
                password=os.getenv('FSTR_DB_PASS', '')
            )
            self.cursor = self.conn.cursor()
            logger.info("Successfully connected to database")
            return True
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            return False

    def disconnect(self):
        """Закрытие соединения с БД"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()


class PerevalDataProcessor:
    """Класс для обработки данных перевалов с нормализованной структурой"""

    def __init__(self):
        self.db = DatabaseConnector()

    def _create_or_get_user(self, user_data):
        """Создает или получает существующего пользователя"""
        try:
            print(f"DEBUG _create_or_get_user: user_data = {user_data}")
            print(f"DEBUG _create_or_get_user: type(user_data) = {type(user_data)}")
            print(
                f"DEBUG _create_or_get_user: keys = {list(user_data.keys()) if isinstance(user_data, dict) else 'NOT DICT'}")

            # Проверяем наличие email
            if 'email' not in user_data:
                print(f"ERROR: email not in user_data!")
                raise KeyError("Email is required")

            email = user_data['email']
            print(f"DEBUG: email = {email}")

            # Проверяем, существует ли пользователь
            select_query = sql.SQL("""
                SELECT id FROM pereval_user WHERE email = %s
            """)
            self.db.cursor.execute(select_query, (email,))
            result = self.db.cursor.fetchone()

            if result:
                print(f"DEBUG: User exists with id {result[0]}")
                return result[0]  # Возвращаем существующий ID

            # Создаем нового пользователя
            print(f"DEBUG: Creating new user with email {email}")
            insert_query = sql.SQL("""
                INSERT INTO pereval_user (email, fam, name, otc, phone)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            """)

            # Проверяем наличие всех полей
            fam = user_data.get('fam', '')
            name = user_data.get('name', '')
            otc = user_data.get('otc', '')
            phone = user_data.get('phone', '')

            print(f"DEBUG: fam={fam}, name={name}, otc={otc}, phone={phone}")

            self.db.cursor.execute(insert_query, (
                email,
                fam,
                name,
                otc,
                phone
            ))
            user_id = self.db.cursor.fetchone()[0]
            print(f"DEBUG: New user created with id {user_id}")
            return user_id

        except Exception as e:
            logger.error(f"Error creating/getting user: {e}")
            print(f"ERROR in _create_or_get_user: {e}")
            raise

    def _create_coords(self, coords_data):
        """Создает запись координат"""
        try:
            insert_query = sql.SQL("""
                INSERT INTO pereval_coords (latitude, longitude, height)
                VALUES (%s, %s, %s)
                RETURNING id
            """)
            self.db.cursor.execute(insert_query, (
                float(coords_data['latitude']),
                float(coords_data['longitude']),
                int(coords_data['height'])
            ))
            return self.db.cursor.fetchone()[0]
        except Exception as e:
            logger.error(f"Error creating coords: {e}")
            raise

    def _create_level(self, level_data):
        """Создает запись уровня сложности"""
        try:
            insert_query = sql.SQL("""
                INSERT INTO pereval_level (winter, summer, autumn, spring)
                VALUES (%s, %s, %s, %s)
                RETURNING id
            """)
            self.db.cursor.execute(insert_query, (
                level_data.get('winter', ''),
                level_data.get('summer', ''),
                level_data.get('autumn', ''),
                level_data.get('spring', '')
            ))
            return self.db.cursor.fetchone()[0]
        except Exception as e:
            logger.error(f"Error creating level: {e}")
            raise

    def _create_images(self, pereval_id, images_data):
        """Создает записи изображений"""
        try:
            for img in images_data:
                insert_query = sql.SQL("""
                    INSERT INTO pereval_image (pereval_id, data, title, date_added)
                    VALUES (%s, %s, %s, %s)
                """)
                self.db.cursor.execute(insert_query, (
                    pereval_id,
                    img['data'],
                    img['title'],
                    datetime.now()
                ))
        except Exception as e:
            logger.error(f"Error creating images: {e}")
            raise

    def _delete_images(self, pereval_id):
        """Удаляет все изображения перевала"""
        try:
            delete_query = sql.SQL("""
                DELETE FROM pereval_image WHERE pereval_id = %s
            """)
            self.db.cursor.execute(delete_query, (pereval_id,))
        except Exception as e:
            logger.error(f"Error deleting images: {e}")
            raise

    def _update_coords(self, coords_id, coords_data):
        """Обновляет координаты"""
        try:
            update_query = sql.SQL("""
                UPDATE pereval_coords 
                SET latitude = %s, longitude = %s, height = %s
                WHERE id = %s
            """)
            self.db.cursor.execute(update_query, (
                float(coords_data['latitude']),
                float(coords_data['longitude']),
                int(coords_data['height']),
                coords_id
            ))
        except Exception as e:
            logger.error(f"Error updating coords: {e}")
            raise

    def _update_level(self, level_id, level_data):
        """Обновляет уровень сложности"""
        try:
            update_query = sql.SQL("""
                UPDATE pereval_level 
                SET winter = %s, summer = %s, autumn = %s, spring = %s
                WHERE id = %s
            """)
            self.db.cursor.execute(update_query, (
                level_data.get('winter', ''),
                level_data.get('summer', ''),
                level_data.get('autumn', ''),
                level_data.get('spring', ''),
                level_id
            ))
        except Exception as e:
            logger.error(f"Error updating level: {e}")
            raise

    def submit_data(self, data):
        """
        Основной метод для добавления данных о перевале
        """
        print(f"DEBUG submit_data: Получены данные")
        print(f"DEBUG submit_data: type(data) = {type(data)}")
        print(f"DEBUG submit_data: keys = {list(data.keys())}")

        try:
            # Подключение к БД
            if not self.db.connect():
                return {
                    "status": 500,
                    "message": "Ошибка подключения к базе данных",
                    "id": None
                }

            # Начинаем транзакцию
            self.db.cursor.execute("BEGIN")

            # 1. Создаем/получаем пользователя
            print(f"DEBUG submit_data: data['user'] = {data.get('user', {})}")
            print(f"DEBUG submit_data: type(data['user']) = {type(data.get('user', {}))}")

            user_data = data.get('user', {})
            if not user_data:
                print("ERROR: User data is empty!")
                return {
                    "status": 400,
                    "message": "Данные пользователя отсутствуют",
                    "id": None
                }

            # Проверяем наличие email
            if 'email' not in user_data:
                print(f"ERROR: Email not found in user_data. Keys: {list(user_data.keys())}")
                return {
                    "status": 400,
                    "message": "Email пользователя обязателен",
                    "id": None
                }

            user_id = self._create_or_get_user(user_data)

            # 2. Создаем координаты
            coords_id = self._create_coords(data['coords'])

            # 3. Создаем уровень сложности
            level_id = self._create_level(data['level'])

            # 4. Создаем перевал
            add_time = data.get("add_time")
            if isinstance(add_time, datetime):
                add_time_str = add_time.strftime('%Y-%m-%d %H:%M:%S')
            elif add_time:
                add_time_str = add_time
            else:
                add_time_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            insert_query = sql.SQL("""
                INSERT INTO pereval (
                    beauty_title, title, other_titles, connect, 
                    add_time, user_id, coords_id, level_id, status
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """)

            self.db.cursor.execute(insert_query, (
                data['beauty_title'],
                data['title'],
                data.get('other_titles', ''),
                data.get('connect', ''),
                add_time_str,
                user_id,
                coords_id,
                level_id,
                'new'  # Статус по умолчанию
            ))

            # Получаем ID вставленного перевала
            pereval_id = self.db.cursor.fetchone()[0]

            # 5. Создаем изображения
            images = data.get('images', [])
            if images:
                self._create_images(pereval_id, images)

            # Фиксируем транзакцию
            self.db.conn.commit()

            return {
                "status": 200,
                "message": "Отправлено успешно",
                "id": pereval_id
            }

        except Exception as e:
            if self.db.conn:
                self.db.conn.rollback()

            logger.error(f"Error submitting data: {e}")
            return {
                "status": 500,
                "message": f"Ошибка при выполнении операции: {str(e)}",
                "id": None
            }

        finally:
            self.db.disconnect()

    def get_pereval_by_id(self, pereval_id):
        """Получение данных о перевале по ID"""
        try:
            if not self.db.connect():
                return None

            query = sql.SQL("""
                SELECT 
                    p.id, p.beauty_title, p.title, p.other_titles, p.connect,
                    p.add_time, p.status,
                    u.email, u.fam, u.name, u.otc, u.phone,
                    c.latitude, c.longitude, c.height,
                    l.winter, l.summer, l.autumn, l.spring
                FROM pereval p
                JOIN pereval_user u ON p.user_id = u.id
                JOIN pereval_coords c ON p.coords_id = c.id
                JOIN pereval_level l ON p.level_id = l.id
                WHERE p.id = %s
            """)

            self.db.cursor.execute(query, (pereval_id,))
            result = self.db.cursor.fetchone()

            if result:
                # Получаем изображения
                img_query = sql.SQL("""
                    SELECT data, title FROM pereval_image 
                    WHERE pereval_id = %s
                """)
                self.db.cursor.execute(img_query, (pereval_id,))
                images = [{'data': row[0], 'title': row[1]} for row in self.db.cursor.fetchall()]

                return {
                    "id": result[0],
                    "beauty_title": result[1],
                    "title": result[2],
                    "other_titles": result[3],
                    "connect": result[4],
                    "add_time": result[5],
                    "status": result[6],
                    "user": {
                        "email": result[7],
                        "fam": result[8],
                        "name": result[9],
                        "otc": result[10],
                        "phone": result[11]
                    },
                    "coords": {
                        "latitude": float(result[12]),
                        "longitude": float(result[13]),
                        "height": result[14]
                    },
                    "level": {
                        "winter": result[15],
                        "summer": result[16],
                        "autumn": result[17],
                        "spring": result[18]
                    },
                    "images": images
                }
            return None

        except Exception as e:
            logger.error(f"Error getting pereval: {e}")
            return None
        finally:
            self.db.disconnect()

    def update_pereval(self, pereval_id, data):
        """Обновление данных перевала"""
        try:
            if not self.db.connect():
                return {
                    "state": 0,
                    "message": "Ошибка подключения к базе данных"
                }

            # Проверяем статус перевала
            status_query = sql.SQL("""
                SELECT status, user_id, coords_id, level_id 
                FROM pereval 
                WHERE id = %s
            """)
            self.db.cursor.execute(status_query, (pereval_id,))
            result = self.db.cursor.fetchone()

            if not result:
                return {
                    "state": 0,
                    "message": f"Перевал с ID {pereval_id} не найден"
                }

            status, user_id, coords_id, level_id = result

            # Проверяем, можно ли редактировать (только статус 'new')
            if status != 'new':
                return {
                    "state": 0,
                    "message": f"Редактирование запрещено. Текущий статус: {status}"
                }

            # Начинаем транзакцию
            self.db.cursor.execute("BEGIN")

            # Обновляем координаты
            if 'coords' in data:
                self._update_coords(coords_id, data['coords'])

            # Обновляем уровень сложности
            if 'level' in data:
                self._update_level(level_id, data['level'])

            # Обновляем основные данные перевала
            update_fields = []
            update_values = []

            if 'beauty_title' in data:
                update_fields.append("beauty_title = %s")
                update_values.append(data['beauty_title'])

            if 'title' in data:
                update_fields.append("title = %s")
                update_values.append(data['title'])

            if 'other_titles' in data:
                update_fields.append("other_titles = %s")
                update_values.append(data['other_titles'])

            if 'connect' in data:
                update_fields.append("connect = %s")
                update_values.append(data['connect'])

            if update_fields:
                update_query = sql.SQL(f"""
                    UPDATE pereval 
                    SET {', '.join(update_fields)}
                    WHERE id = %s
                """)
                update_values.append(pereval_id)
                self.db.cursor.execute(update_query, tuple(update_values))

            # Обновляем изображения (удаляем старые, добавляем новые)
            if 'images' in data:
                self._delete_images(pereval_id)
                self._create_images(pereval_id, data['images'])

            # Фиксируем транзакцию
            self.db.conn.commit()

            return {
                "state": 1,
                "message": "Запись успешно обновлена"
            }

        except Exception as e:
            if self.db.conn:
                self.db.conn.rollback()

            logger.error(f"Error updating pereval {pereval_id}: {e}")
            return {
                "state": 0,
                "message": f"Ошибка при обновлении: {str(e)}"
            }

        finally:
            self.db.disconnect()

    def get_perevals_by_email(self, email):
        """Получение всех перевалов по email пользователя"""
        try:
            if not self.db.connect():
                return []

            query = sql.SQL("""
                SELECT 
                    p.id, p.beauty_title, p.title, p.other_titles, p.connect,
                    p.add_time, p.status,
                    u.email, u.fam, u.name, u.otc, u.phone,
                    c.latitude, c.longitude, c.height,
                    l.winter, l.summer, l.autumn, l.spring
                FROM pereval p
                JOIN pereval_user u ON p.user_id = u.id
                JOIN pereval_coords c ON p.coords_id = c.id
                JOIN pereval_level l ON p.level_id = l.id
                WHERE u.email = %s
                ORDER BY p.add_time DESC
            """)

            self.db.cursor.execute(query, (email,))
            results = self.db.cursor.fetchall()

            perevals = []
            for result in results:
                # Получаем изображения для каждого перевала
                img_query = sql.SQL("""
                    SELECT data, title FROM pereval_image 
                    WHERE pereval_id = %s
                """)
                self.db.cursor.execute(img_query, (result[0],))
                images = [{'data': row[0], 'title': row[1]} for row in self.db.cursor.fetchall()]

                pereval = {
                    "id": result[0],
                    "beauty_title": result[1],
                    "title": result[2],
                    "other_titles": result[3],
                    "connect": result[4],
                    "add_time": result[5],
                    "status": result[6],
                    "user": {
                        "email": result[7],
                        "fam": result[8],
                        "name": result[9],
                        "otc": result[10],
                        "phone": result[11]
                    },
                    "coords": {
                        "latitude": float(result[12]),
                        "longitude": float(result[13]),
                        "height": result[14]
                    },
                    "level": {
                        "winter": result[15],
                        "summer": result[16],
                        "autumn": result[17],
                        "spring": result[18]
                    },
                    "images": images
                }
                perevals.append(pereval)

            return perevals

        except Exception as e:
            logger.error(f"Error getting perevals by email {email}: {e}")
            return []
        finally:
            self.db.disconnect()