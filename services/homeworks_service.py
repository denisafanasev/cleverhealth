import config
from models.homework_manager import HomeworkManager
from models.course_manager import EducationCourseManager
from models.module_manager import EducationModuleManager
from models.lesson_manager import EducationLessonManager
from models.education_stream_manager import EducationStreamManager
from models.user_manager import UserManager
from models.homework_chat_manager import HomeworkChatManager
from models.message_manager import MessageManager


class HomeworksService():
    """
    HomeworksService - класс бизнес-логики сервиса управления настройками приложения.
    Возвращает в слой отображения объекты в доменной модели
    Взаимодейтвует с классами слоя моделей, передавая им данные и получая данные в объектах доменной модели
    """

    def get_lesson(self, _id_lesson):
        """
        Возвращает данные урока

        Args:
            _id_lesson(Int): id урока

        Returns:
            Lesson: урок
        """

        lesson_manager = EducationLessonManager()
        module_manager = EducationModuleManager()

        lesson = lesson_manager.get_lesson_by_id(_id_lesson)
        module = module_manager.get_module_by_id(lesson.id_module)
        module.lessons = lesson

        return module

    def get_education_stream(self, _id_education_stream, _current_user_id):
        """
        Возвращает данные обучающего потока по его ID

        Args:
            _id_education_stream(Int): ID

        Returns:
            EducationStream: обучающий поток
        """

        education_stream_manager = EducationStreamManager()
        course_manager = EducationCourseManager()

        education_stream = education_stream_manager.get_education_stream(_id_education_stream)
        education_stream.course = course_manager.get_course_by_id(education_stream.course)

        return education_stream

    def get_users_by_education_streams(self, _users_id_list, _current_user_id):
        """

        """
        user_manager = UserManager()

        users_list = user_manager.get_users_by_ids_list(_current_user_id, _users_id_list)
        if len(users_list) == 0:
            for user_id in _users_id_list:
                user = user_manager.get_user_by_id(user_id)
                if user is not None:
                    users_list.append(user)

        return users_list

    def get_user_by_id(self, _id_user):
        """
        Возвращает данные пользователя по ID

        Args:
            _id_user(Int): ID пользователя

        Returns:
            User: пользователь
        """

        user_manager = UserManager()

        return user_manager.get_user_by_id(_id_user)

    def get_homework_chat(self, _id_lesson, _id_user, _id_current_user):
        """
        Возвращает данные чата

        Args:
            _id_lesson(Integer): ID урока
            _id_user(Integer): ID пользователя
            _id_current_user(Integer): ID текущего пользователя

        Returns:
            RoomChat: комната чата
        """

        homework_chat_manager = HomeworkChatManager()
        message_manager = MessageManager()

        homework_chat = homework_chat_manager.get_homework_chat(_id_user, _id_lesson)
        if homework_chat is not None:
            homework_chat.unread_message_amount = message_manager.get_unread_messages_amount_for_superuser(homework_chat.id, _id_user)

        return homework_chat

    def get_users_list_in_education_streams_file(self, _id_education_stream):
        """
        Возвращает список пользователей, которые находятся в обучающем потоке

        Returns:
            List: список пользователей
        """
        user_manager = UserManager()

        users_login_list = []
        with open(config.DATA_FOLDER + f'course_1/s{_id_education_stream}_users.txt') as f:
            users_login_list.extend(f.read().splitlines())

        users_list = []
        for user_login in users_login_list:
            user = user_manager.get_user_by_login(user_login)
            if user is not None:
                users_list.append(user)

        return users_list

    def get_homeworks_list_by_id_user(self, _id_lesson, _id_user):
        """
        Возвращает список проверенных домашних работ по ID пользователя и урока

        Args:
            _id_lesson(Integer): ID урока
            _id_user(Integer): ID пользователя

        Returns:
            List: список домашних работ
        """
        homework_manager = HomeworkManager()

        homework_list = homework_manager.get_homeworks_list_by_id_lesson(_id_lesson, _id_user)
        if homework_list:
            return homework_list

    def get_homeworks_list_by_id_user_verified(self, _id_lesson, _id_user):
        """
        Возвращает список проверенных домашних работ по ID пользователя и урока

        Args:
            _id_lesson(Integer): ID урока
            _id_user(Integer): ID пользователя

        Returns:
            List: список домашних работ
        """
        homework_manager = HomeworkManager()

        homework_list = homework_manager.get_homeworks_list_by_id_lesson(_id_lesson, _id_user)
        if homework_list:
            homeworks = [homework for homework in homework_list if homework.status is not None]
            return homeworks

    def get_homeworks_list_by_id_user_no_verified(self, _id_lesson, _id_user):
        """
        Возвращает список не проверенных домашних работ по ID пользователя и урока

        Args:
            _id_lesson(Integer): ID урока
            _id_user(Integer): ID пользователя

        Returns:
            List: список домашних работ
        """
        homework_manager = HomeworkManager()

        homework_list = homework_manager.get_homeworks_list_by_id_lesson_no_verified(_id_lesson, _id_user)
        if homework_list:
            return homework_list

    def get_lessons_by_id_course(self, _id_course):
        """
        Возвращает все уроки курса, у которых есть задание

        Return:
            List(Lesson): список уроков
        """
        lesson_manager = EducationLessonManager()
        module_manager = EducationModuleManager()

        modules_list = module_manager.get_course_modules_list(_id_course)
        lessons_list = []
        for module in modules_list:
            lessons_list_data = lesson_manager.get_lessons_list_by_id_module(module.id)
            lessons_list_with_task = [lesson for lesson in lessons_list_data if lesson.task is not None]
            lessons_list.extend(lessons_list_with_task)

        return lessons_list

    def get_module_by_id(self, _id):
        """
        Возвращает данные модуля по ID

        Args:
            _id(Int): ID модуля

        Return:
            Module: модуль
        """

        module_manager = EducationModuleManager()

        return module_manager.get_module_by_id(_id)

    def get_course_by_id(self, _id):
        """
        Возвращает данные курса по ID

        Args:
            _id(Int): ID курса

        Return:
            Course: курс
        """

        course_manager = EducationCourseManager()

        return course_manager.get_course_by_id(_id)

    def get_educations_stream(self):
        """
        Возвращает список всех обучающих потоков

        Returns:
            List(EducationStream): список образовательных потоков
        """

        education_stream = EducationStreamManager()

        return education_stream.get_education_streams()

    def is_unread_messages(self, _id_lessons_list, _user_id):
        """
        Проверяет на наличие непрочитанных суперпользователями сообщений.
        Args:
            _id_lessons_list(Int): список ID уроков курса
            _user_id(Int): ID пользователя

        Return:
            True - если есть хотя одно непрочитанное сообщение
            False - если нет непрочитанных сообщений
        """
        homework_chat_manager = HomeworkChatManager()
        message_manager = MessageManager()

        unread_messages_list = message_manager.get_unread_messages_by_id_user(_user_id)
        for unread_message in unread_messages_list:
            homework_chat = homework_chat_manager.homework_chat_entry(unread_message.id_homework_chat)
            if homework_chat.id_lesson in _id_lessons_list:
                return True

        return False

    def get_amount_accepted_homework(self, _user_id, _id_lessons_list):
        """
        Возвращает количества принятых/не принятых домашних работ у пользователя

        Args:
            _user_id(Int): ID пользователя
            _id_lessons_list(List): список ID уроков курса

        Returns:
            count_accepted_homework(Int): количество принятых домашних работ
            count_no_accepted_homework(Int): количество не принятых домашних работ
        """

        homework_manager = HomeworkManager()

        id_lessons_set = homework_manager.get_id_lessons_list_with_completed_homework(_user_id)

        count_accepted_homework = len(id_lessons_set.intersection(_id_lessons_list))
        # count_no_accepted_homework = len(_id_lessons_list) - count_accepted_homework

        return count_accepted_homework
    
    def get_amount_no_accepted_homework(self, _user_id, _id_lessons_list):
        """
        Возвращает количества принятых/не принятых домашних работ у пользователя

        Args:
            _user_id(Int): ID пользователя
            _id_lessons_list(List): список ID уроков курса

        Returns:
            count_accepted_homework(Int): количество принятых домашних работ
            count_no_accepted_homework(Int): количество не принятых домашних работ
        """

        homework_manager = HomeworkManager()

        id_lessons_set = homework_manager.get_id_lessons_list_with_no_completed_homework(_user_id)

        count_no_accepted_homework = len(id_lessons_set.intersection(_id_lessons_list))

        return count_no_accepted_homework
