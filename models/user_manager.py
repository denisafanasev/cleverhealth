import hashlib

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from itsdangerous import URLSafeTimedSerializer
import pandas as pd
from sqlalchemy import text, create_engine

from models.user import User
from data_adapters.data_store import DataStore

from error import UserManagerException
import config


class UserManager():
    """
    Класс модели управления пользователями, ведения списка пользователей
    Взаимодейтвует с модулем хранения данных, преобразую доменные структуры в объекты типа Dict
    Вовзращает в слой бизнес-логики приложения объекты в доменных структурах
    """

    def hash_password(self, _password):
        """
        Генерирует hash функцию от пароля

        Args:
            _password (String): пароль

        Returns:
            String: представление результата hash функции
        """

        return hashlib.md5(_password.encode()).hexdigest()

    def create_token(self, email):
        """создание токена по email адресу

        Args:
            email (string): email адрес

        Returns:
            string: токен
        """

        serializer = URLSafeTimedSerializer(config.SECRET_KEY)
        return serializer.dumps(email, salt=config.SECURITY_PASSWORD_SALT)

    def validate_password(self, _password):
        """
        Проверка пароля на корректное значение

        Args:
            _password (String): пароль

        Raises:
            UserManagerException: ошибка корректности значения пароля
        """

        if (len(_password) < 5) or (len(_password) > 20):
            raise UserManagerException("неверная длинная пароля, укажите минимум 5 и максимум 20 символов")

    def validate_role(self, _role):
        """
        Проверка корректности указания роли пользователя в системе

        Args:
            _role (String): роль пользователя user/superuser

        Raises:
            UserManagerException: ошибка корректности указанного значения роли
        """

        if _role != "superuser" and _role != "user":
            raise UserManagerException("Роль пользователя задана не верно")

    def validate_login(self, _login):
        """
        Проверка корректности значения логина пользователя

        Args:
            _login (String): логин пользователя

        Raises:
            UserManagerException: ошибка корректности указанного логина пользователя
        """

        if (len(_login) < 3) or (len(_login) > 10):
            raise UserManagerException("неверная длинная логина пользователя, укажите минимум 3 символа и максимум 10")

    def user_row_to_user(self, _data_row):
        """
        Преобразует структуру данных, в которой хранится информация о пользователи в структуру User

        Args:
            _data_row (Dict): структура данных, которую возвращает дата адаптер

        Returns:
            User: пользователь
        """

        # создадим пользователя с указанием обязательных атрибутов
        # note that doc_id from the table used as a user_id
        # if _data_row.get('doc_id') is not None:
        #     doc_id = _data_row['doc_id']
        # else:
        #     doc_id = _data_row.doc_id

        doc_id = _data_row['doc_id'] if _data_row.get('doc_id') is not None else _data_row.doc_id
        try:
            user = User(doc_id, _data_row['login'], _data_row['name'], _data_row['email'], _data_row['role'],
                        _data_row['active'])
        except KeyError as error:
            raise UserManagerException("DB structure error: no attribute " + error.args[0])

        # проверим наличие в структуре хранения необязательных атрибутов

        if _data_row.get('probationers_number') is not None:
            user.probationers_number = int(_data_row['probationers_number'])
        else:
            user.probationers_number = 5

        if _data_row.get('created_date') is not None:
            if isinstance(_data_row['created_date'], str):
                user.created_date = datetime.strptime(_data_row['created_date'], '%d/%m/%Y')
            else:
                user.created_date = _data_row['created_date']
        else:
            # user.created_date = datetime.strptime("01/01/1990", '%d/%m/%Y')
            user.created_date = datetime(1990, 1, 1, 0, 0)

        if _data_row.get('education_module_expiration_date') is not None:
            if isinstance(_data_row['education_module_expiration_date'], str):
                user.education_module_expiration_date = datetime.strptime(_data_row['education_module_expiration_date'],
                                                                          '%d/%m/%Y')
            else:
                user.education_module_expiration_date = _data_row['education_module_expiration_date']
        else:
            user.education_module_expiration_date = datetime.today()

        if _data_row.get('token') is not None:
            user.token = _data_row['token']
        else:
            user.token = ""

        if _data_row.get('email_confirmed') is not None:
            user.email_confirmed = _data_row['email_confirmed']
        else:
            user.email_confirmed = False

        date_today = datetime.today()

        if user.role == 'superuser':
            user.education_module_expiration_date += relativedelta(year=date_today.year + 10)

        if date_today.date() > user.education_module_expiration_date.date():
            user.active_education_module = "inactive"
        else:
            if user.education_module_expiration_date - date_today < timedelta(days=31):
                user.active_education_module = "ends"
            else:
                user.active_education_module = "active"

        return user

    def get_user_by_id(self, _user_id):
        """
        Возвращает объект User по id пользователя

        Args:
            _user_id   - Required  : id пользователя (Int)
        """

        user = None

        data_store = DataStore("users", force_adapter='PostgreSQLDataAdapter')
        if data_store.get_rows_count() == 0:
            data_store = DataStore("users")

        user_data = data_store.get_row_by_id(_user_id)

        if user_data is not None:
            user = self.user_row_to_user(user_data)

        return user

    def get_user(self, _login, _password):
        """
        Возвращает пользователя по логину и паролю

        Args:
            _login   - Required  : current iteration (String)
            _password   - Required  : current iteration (String)
        """

        user = None

        login = _login.lower().strip()
        password = self.hash_password(_password)

        data_store = DataStore("users", force_adapter='PostgreSQLDataAdapter')
        if data_store.get_rows_count() == 0:
            data_store = DataStore("users")
        # user_data = data_store.get_rows(f"users.login = '{login}' and users.password = '{password}'")
        if data_store.current_data_adapter == 'PostgreSQLDataAdapter':
            user_data = data_store.get_rows({'where': f"users.login = '{login}' and users.password = '{password}'"})
        else:
            user_data = data_store.get_rows({"login": login, "password": password})

        # проверим, что у нас данному набору логин и пароль соответсвует только одна запись пользователя
        if len(user_data) > 1:
            raise UserManagerException("Ошибка в базе данных пользователей")

        if len(user_data) == 0:
            raise UserManagerException("Указаны неверные данные для входа")

        # получаем объект Пользователь
        user = self.user_row_to_user(user_data[0])

        return user

    def get_user_by_login(self, _login):
        """
        Возвращает пользователя по логину

        Args:
            _login   - Required  : login пользователя (String)
        """

        user = None

        login = _login.lower().strip()
        data_store = DataStore("users", force_adapter='PostgreSQLDataAdapter')

        if data_store.current_data_adapter == 'PostgreSQLDataAdapter':
            user_data = data_store.get_rows({'where': f"users.login = '{login}'"})
        else:
            user_data = data_store.get_rows({"login": login})

        if len(user_data) > 1:
            raise UserManagerException("Ошибка в базе данных пользователей, login не уникальный")

        if len(user_data) == 1:
            user = self.user_row_to_user(user_data[0])

        return user

    def get_user_by_email(self, _email):
        """
        Возвращает пользователя по email

        Args:
            _email   - Required  : email пользователя (String)
        """

        user = None

        email = _email.lower().strip()
        data_store = DataStore("users", force_adapter='PostgreSQLDataAdapter')

        if data_store.current_data_adapter == 'PostgreSQLDataAdapter':
            user_data = data_store.get_rows({'where': f"users.email = '{email}'"})
        else:
            user_data = data_store.get_rows({"email": email})

        if len(user_data) > 1:
            raise UserManagerException("Ошибка в базе данных пользователей, email не уникальный")

        if len(user_data) == 1:
            user = self.user_row_to_user(user_data[0])

        return user

    def get_users(self, _user_id):
        """
        Возвращает список пользователей в системе, в соответствии с ролью пользователя, который запрашивает список

        Args:
            None

        Returns:
            List: список пользователей с типом User
        """

        # users = []

        # data_store = DataStore("users", force_adapter='PostgreSQLDataAdapter')
        # if _page is None:
        #     users_list_data = data_store.get_rows()
        # else:
        #     if data_store.current_data_adapter == 'PostgreSQLDataAdapter':
        #         users_list_data = data_store.get_rows({'limit': 20, 'offset': (_page - 1) * 20, 'order_by': 'doc_id asc'})
        #         users_list_data = pd.read_sql('select * from users', data_store.data_store)
        #     else:
        #         users_list_data = data_store.get_rows()

        # for user_data in users_list_data:

        #     user = self.user_row_to_user(user_data)

            # if self.get_user_role(_user_id) == "superuser":
            #     users.append(user)
            # else:
            #     if self.get_user_by_id(_user_id) == user.user_id:
            #         users.append(user)
        date_today = datetime.today()
        data_store = DataStore("users", force_adapter='PostgreSQLDataAdapter')
        if data_store.current_data_adapter == 'PostgreSQLDataAdapter':
            con = create_engine("postgresql:" + config.PostgreSQLDataAdapter_connection_string())
            if self.get_user_role(_user_id) == "superuser":
                # users.append(user)
                users = pd.read_sql('select * from users', con)
                users['education_module_expiration_date'] = users['education_module_expiration_date'].where(users['role'] == 'user', other=date_today + relativedelta(year=date_today.year + 10))
                users.loc[users['education_module_expiration_date'] < date_today, 'active_education_module'] = "inactive"
                users.loc[users['education_module_expiration_date'] - date_today < timedelta(days=31), 'active_education_module'] = "ends"
                users.loc[users['education_module_expiration_date'] - date_today >= timedelta(days=31), 'active_education_module'] = "active"
                            
                users.drop(columns=['password', 'token'], inplace=True)  
                
        else:
            users_data = data_store.get_rows()
            users = []
            for user_data in users_data:
                user = self.user_row_to_user(user_data)
                if self.get_user_role(_user_id) == "superuser":
                    users.append(user)
                else:
                    if self.get_user_by_id(_user_id) == user.user_id:
                        users.append(user)
                        
            # users_df_data['created_date'] = pd.to_datetime(users_df_data['created_date'], format='%d/%m/%Y')
            # users_df_data['education_module_expiration_date'] = pd.to_datetime(users_df_data['education_module_expiration_date'], format='%d/%m/%Y')
             
       
        return users

    def is_there_users(self):
        """
        Проверяем, есть ли в системе пользователи вообще

        Args:
            None
        """

        data_store = DataStore("users", force_adapter='PostgreSQLDataAdapter')

        data = data_store.get_rows_count()
        if data != 0:
            return True
        else:
            if data_store.current_data_adapter == 'PostgreSQLDataAdapter':
                data_store_tinydb = DataStore("users")

                data = data_store_tinydb.get_rows_count()
                if data != 0:
                    return True

        return False

    def create_user(self, _user):
        """
        Процедура создания нового пользователя в системе

        Args:
            _user (Dict): данные нового пользователя

        Raises:
            UserManagerException: ошибка создания нового пользователя

        Returns:
            _error (List): список ошибок при создании пользователя
        """
        self.validate_password(_user['password'])
        self.validate_login(_user['login'])

        if len(_user['email']) == 0:
            raise UserManagerException('Введите email')

        password = self.hash_password(_user['password'])
        password2 = self.hash_password(_user['password2'])
        login = _user['login'].lower().strip()
        email = _user['email'].lower().strip()
        role = _user['role']
        name = _user['name']
        email_confirmed = False

        # создаем токен для подтверждения регистрации
        token = self.create_token(email)

        # создаем новую запись
        data_store = DataStore("users", force_adapter='PostgreSQLDataAdapter')

        # проверим, что у пользователя с таким логином не существует

        if password != password2:
            raise UserManagerException("Пароли не совпадают")

        user = self.get_user_by_login(login)
        if user is not None:
            raise UserManagerException("Пользователь с таким логином уже существует")

        user = self.get_user_by_email(email)
        if user is not None:
            raise UserManagerException("Пользователь с таким email уже существует")

        # создаем новую запись
        user = User(_login=login, _name=name, _email=email, _role=role, _probationers_number=_user['probationers_number'],
                    _token=token, _email_confirmed=email_confirmed)

        if data_store.current_data_adapter == 'TinyDBDataAdapter':
            created_date = user.created_date.strftime('%d/%m/%Y')
            education_module_expiration_date = user.education_module_expiration_date.strftime('%d/%m/%Y')
        else:
            created_date = user.created_date
            education_module_expiration_date = user.education_module_expiration_date

        user_data = {"login": user.login, "password": password, "email": user.email,
                     "role": user.role, "name": user.name, "created_date": created_date,
                     "education_module_expiration_date": education_module_expiration_date,
                     "probationers_number": user.probationers_number,
                     "active": user.active, "email_confirmed": user.email_confirmed, "token": user.token}

        return data_store.insert_row(user_data)

    def get_user_role(self, _user_id):
        """
        Возвращает роль пользователя по id

        Args:
            _id (Int): id пользователя

        Returns:
            String: роль пользователя
        """
        user = self.get_user_by_id(_user_id)
        user_role = user.role

        return user_role

    def chenge_user(self, _user_id, _user_data, _education_module_expiration_date="", _token="", _email_confirmed=False,
                    _active=True):
        """
        Обновляет информацию о пользователе и возвращает ее

        Args:
            _user_id (Int): ID пользователя
            _user_data (Dict): данные пользователя
            _education_module_expiration_date (String): дата окончания подписки
            _token (Int): токен пользователя
            _email_confirmed (Boolean): подтверждена ли почта[True - да/False - нет]

        Returns:
            Dict: словарь с информацией о пользователе
        """
        if len(_user_data['email']) == 0:
            raise UserManagerException('Введите email')

        user = self.get_user_by_email(_user_data['email'])
        if user is not None:
            if user.login != _user_data['login']:
                raise UserManagerException("Пользователь с таким email уже существует")

        user = User(_user_id=_user_id, _login=_user_data['login'], _name=_user_data['name'], _email=_user_data['email'],
                    _role=_user_data['role'], _created_date=_user_data['created_date'],
                    _probationers_number=_user_data['probationers_number'], _token=_token,
                    _email_confirmed=_email_confirmed,
                    _education_module_expiration_date=_education_module_expiration_date, _active=_active)

        data_store = DataStore("users", force_adapter='PostgreSQLDataAdapter')
        if data_store.current_data_adapter == 'TinyDBDataAdapter':
            created_date = user.created_date.strftime('%d/%m/%Y')
            education_module_expiration_date = user.education_module_expiration_date.strftime('%d/%m/%Y')
        else:
            created_date = user.created_date
            education_module_expiration_date = user.education_module_expiration_date

        user_data = {"login": user.login, "email": user.email, "role": user.role, "name": user.name,
                     "probationers_number": user.probationers_number, "created_date": created_date,
                     "education_module_expiration_date": education_module_expiration_date, "active": user.active,
                     "token": user.token, "email_confirmed": user.email_confirmed}

        data_store.update_row_by_id(user_data, user.user_id)

        return user

    def chenge_password(self, _user_id, _password, _password2, _current_password=''):
        """
        Сброс пароля пользователя

        Args:
            _user_id (Integer): ID пользователя
            _password (String): пароль пользователя
            _password2 (String): контрольный ввод пароля пользователя
            _current_password(String): текущий пароль пользователя(нужен, если пароль меняет user, а не superuser).
                                        Defaults to ''
        """

        self.validate_password(_password)
        if _password != _password2:
            raise UserManagerException("введенные пароли не совпадают")

        password = self.hash_password(_password)
        data_store = DataStore("users", force_adapter='PostgreSQLDataAdapter')
        if _current_password != "":
            if _current_password is None:
                raise UserManagerException('Введите текущий пароль')
            current_password = self.hash_password(_current_password)
            user = data_store.get_row_by_id(_user_id)
            if current_password != user['password']:
                raise UserManagerException("Введенный текущий пароль неправильный")

        user_data = {"password": password}

        data_store.update_row_by_id(user_data, _user_id)

    def activation(self, _user_id):
        """
        Разблокировка пользователя

        Args:
            _user_id(Int): ID пользователя

        Returns:
            _active (bool): Активирован пользователь
        """

        data_store = DataStore('users', force_adapter='PostgreSQLDataAdapter')

        user = self.get_user_by_id(_user_id)
        if user is not None:
            data_store.update_row_by_id({'active': True}, _user_id)

    def deactivation(self, _user_id):
        """
        Блокировка пользователя

        Args:
            _user_id(Int): ID пользователя

        Returns:
            _active (bool): Заблокирован пользователь
        """

        data_store = DataStore('users', force_adapter='PostgreSQLDataAdapter')

        user = self.get_user_by_id(_user_id)
        if user is not None:
            data_store.update_row_by_id({'active': False}, _user_id)

    def access_extension(self, _period, _reference_point, _user_id):
        """
        Продление срока доступа пользователя к центру обучения

        Args:
            _period(Int): количество месяцев, на которое продлевают срок доступа пользователю
            _reference_point(String): начальное время отсчета
            _user_id(Int): ID пользователя, которому продлевают срок доступа
        """

        data_store = DataStore('users', force_adapter='PostgreSQLDataAdapter')

        user = self.get_user_by_id(_user_id)
        if user is not None:
            if _reference_point == "end":
                user.education_module_expiration_date = (
                        user.education_module_expiration_date + relativedelta(months=_period))
            elif _reference_point == "today":
                user.education_module_expiration_date = (datetime.now() + relativedelta(months=_period))

            data_store.update_row_by_id({'education_module_expiration_date': user.education_module_expiration_date}, _user_id)


    def get_users_by_ids_list(self, _user_id, _ids_list):
        """
        Возвращает список пользователей по ID из списка

        Args:
            _user_id(Int): ID текущего пользователя
            _ids_list(List): список ID пользователей

        Returns:
            List: список пользователей
        """
        data_store = DataStore('users', force_adapter='PostgreSQLDataAdapter')

        users_data_list = []
        # Если роль текущего пользователя superuser, то он получит список пользователей.
        # Иначе, получит пустой список
        if data_store.current_data_adapter == 'PostgreSQLDataAdapter':
            if self.get_user_role(_user_id) == 'superuser':
                con = create_engine("postgresql:" + config.PostgreSQLDataAdapter_connection_string())
                # users_data_list = data_store.get_rows({'where': f'users.doc_id in {tuple(_ids_list)}'})
                users_data_list = pd.read_sql(f'select * from users where doc_id in (SELECT unnest(ARRAY[{_ids_list}]))', con=con)
                # for user_data in users_data_list:
                #     users_list.append(self.user_row_to_user(user_data))

        return users_data_list

    def get_users_by_role(self, _id_user, _role):
        """
        Возвращает список пользователей по роли

        Args:
            _id_user(Int): ID текущего пользователя
            _role(Str): роль

        Returns:
            List: список пользователей
        """
        data_store = DataStore('users', force_adapter='PostgreSQLDataAdapter')

        users_list = []
        # Если роль текущего пользователя superuser, то он получит список пользователей.
        # Иначе, получит пустой список
        if self.get_user_role(_id_user) == 'superuser':
            if data_store.current_data_adapter == 'PostgreSQLDataAdapter':
                users_data_list = data_store.get_rows({'where': f"users.role = '{_role}'"})
            else:
                users_data_list = data_store.get_rows({'role': _role})
            for user_data in users_data_list:
                users_list.append(self.user_row_to_user(user_data))

        return users_list

    def get_current_data_adapter(self):
        """
        Возвращает название текущего адаптера

        Returns:
            Str: название текущего адаптера
        """
        data_store = DataStore('users', force_adapter='PostgreSQLDataAdapter')

        return data_store.current_data_adapter

    def get_numbers_users(self, _current_user_id):
        """
        Возвращает количество пользователей в базе данных, если текущий адаптер PostgreSQLDataAdapter

        Args:
            _current_user_id(Int): ID текущего пользователя

        Returns:
            Int: количество пользователей
        """
        data_store = DataStore('users', force_adapter='PostgreSQLDataAdapter')

        if self.get_user_role(_current_user_id) == 'superuser':
            if data_store.current_data_adapter == 'PostgreSQLDataAdapter':
                return data_store.get_rows_count()

    def get_users_by_search_text(self, _search_text, _current_user_id, _page=None):
        """
        Возвращает список пользователей, у которых логин, email, имя пользователя, дата создания или
        срок действия модуля образования совпадает с текстом

        Args:
            _search_text(Str): текст
            _current_user_id(Int): ID текущего пользователя

        Returns:
            users_list: список пользователей
        """

        data_store = DataStore('users', force_adapter='PostgreSQLDataAdapter')

        if self.get_user_role(_current_user_id) == 'superuser':
            date_format = '%d/%m/%Y'
            try:
                date = datetime.strptime(_search_text, date_format)
            except ValueError:
                date = None

            if date is not None:
                query = {
                    'where': f"users.created_date = '{date.date()}' or users.education_module_expiration_date = '{date.date()}'"
                }

            else:
                query = {
                    'where': f"users.login like '{_search_text}%' or users.email like '{_search_text}%' or users.name like '{_search_text}%'"
                }
            if _page is not None:
                query.update({'limit': 20, 'offset': (_page - 1) * 20})

            users_data_list = data_store.get_rows(query)
            users_list = []
            for user_data in users_data_list:
                users_list.append(self.user_row_to_user(user_data))

        return users_list
