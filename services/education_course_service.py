from flask import url_for
from werkzeug.utils import redirect

from models.homework_chat_manager import HomeworkChatManager
from models.message_manager import MessageManager
from models.user_manager import UserManager
from models.course_manager import EducationCourseManager
from models.module_manager import EducationModuleManager
from models.lesson_manager import EducationLessonManager
from models.education_stream_manager import EducationStreamManager
from models.homework_manager import HomeworkManager
from models.action_manager import ActionManager
from models.courses_access_manager import CoursesAccessManager

from datetime import datetime


class EducationCourseService():
    """
    EducationCourseService - класс бизнес-логики сервиса управления настройками приложения
    Возвращает в слой отображения объекты в доменной модели
    Взаимодейтвует с классами слоя моделей, передавая им данные и получая данные в объектах доменной модели
    """

    def get_course_modules_list(self, _id):
        """
        Возвращает список модулей курса по id

        Args:
            _id(Int): индентификатор курса

        Returns:
            modules_list(List): списко модулей курса
        """

        module_manager = EducationModuleManager()
        lesson_manager = EducationLessonManager()

        modules_list = module_manager.get_course_modules_list(_id)
        if modules_list is not None:
            for module in modules_list:
                module.lessons = lesson_manager.get_lessons_list_by_id_module(module.id)

            return modules_list

    def get_user_by_id_and_course_id(self, _user_id, _course_id):
        """
        Возвращает объект User по id пользователя

        Args:
            _user_id   - Required  : id пользователя (Int)
            _id_course - Required  : id курса (Int)

        Returns:
            User: пользователь
        """

        user_manager = UserManager()
        education_stream_manager = EducationStreamManager()

        user = user_manager.get_user_by_id(_user_id)

        education_streams = education_stream_manager.get_education_streams_list_by_id_user(user.user_id, user.role)

        for education_stream in education_streams:
            if education_stream.course == _course_id:
                if education_stream.status != "закончен":
                    user.education_module_expiration_date = education_stream.date_end

        return user
    
    def get_user_by_id(self, _user_id):
        """
        Возвращает объект User по id пользователя

        Args:
            _user_id   - Required  : id пользователя (Int)

        Returns:
            User: пользователь
        """

        user_manager = UserManager()
        user = user_manager.get_user_by_id(_user_id)
        
        return user

    def get_course_by_id(self, _id):
        """
        Возвращает курс по id

        Args:
            _id(Int): индентификатор курса

        Returns:
            course(Course): курс
        """

        course_manager = EducationCourseManager()

        return course_manager.get_course_by_id(_id)
    
    def is_course_module_avalable_for_user(self, _course_id, _module_id, _user_id):
        """
        Функция проверки доступности модуля для пользователя

        Args:
            _course_id (Integer): ID курса
            _module_id (Integer): ID модуля
            _user_id (Integer): ID пользователя

        Returns:
            Boolean: доступен модуль для пользователя или нет
        """        
        
        access_manager = CoursesAccessManager()
        education_stream_manager = EducationStreamManager()
        is_access, start_access_date = access_manager.is_course_module_avalable_for_user(_course_id, _module_id, _user_id)
        end_access_date = None
        if is_access:
            if start_access_date is not None:
                education_stream = education_stream_manager.get_education_stream_by_id_user_and_id_course(_user_id, _course_id)
                end_access_date = education_stream.date_end

        return is_access, start_access_date, end_access_date

    def get_last_homework(self, _id_lesson, _id_user):
        """
        Возвращает последнее сданное домашнюю работу по уроку

        Args:
            _id_lesson(Int): ID урока
            _id_user(Int): ID пользователя

        Return:
            Homework: домашняя работа
        """

        homework_manager = HomeworkManager()

        homework_list = homework_manager.get_homeworks_list_by_id_lesson(_id_lesson, _id_user)
        date = datetime.strptime("01/01/2000", "%d/%m/%Y")
        date_first_homework = datetime.now()
        last_homework = None
        if homework_list is not None:
            # ищем домашнюю работу, которая была сдана позже всех по данному уроку
            for homework in homework_list:
                if homework.date_delivery >= date:
                    date = homework.date_delivery
                    last_homework = homework

            # находим дату сдачи первой домашней работы, сданной пользователем, по уроку
            for homework in homework_list:
                if homework.date_delivery <= date_first_homework:
                    date_first_homework = homework.date_delivery

            last_homework.date_delivery = date_first_homework

            return last_homework

    def get_homework_chat(self, _id_lesson, _id_user):
        """
        Возвращает данные чата по ID урока и пользователя

        Args:
            _id_lesson(Int): ID урока
            _id_user(Int): ID текущего пользователя

        Returns:
            HomeworkChat: комната чата
        """
        homework_chat_manager = HomeworkChatManager()
        message_manager = MessageManager()

        homework_chat = homework_chat_manager.get_homework_chat(_id_user, _id_lesson)
        if homework_chat is not None:
            homework_chat.unread_message_amount = message_manager.get_unread_messages_amount_for_user(homework_chat.id, _id_user)

            return homework_chat

    def redirect_to_lesson(self, _id_lesson, _id_user):
        """
        Создает событие "Просмотр урока пользователем" и перенаправляет пользователя на страницу заданного урока

        Args:
            _id_lesson(Integer): ID урока
            _id_user(Integer): ID текущего пользователя
        """
        lesson_manager = EducationLessonManager()
        module_manager = EducationModuleManager()
        user_manager = UserManager()
        action_manager = ActionManager()

        lesson = lesson_manager.get_lesson_by_id(_id_lesson)
        module = module_manager.get_module_by_id(lesson.id_module)
        module.lessons = lesson
        user = user_manager.get_user_by_id(_id_user)

        if lesson is not None:
            if user.role != "superuser":
                action_manager.add_notifications(module, "посмотрел", '', "course_manager", user)

            return redirect(url_for("multilingual.education_course_lesson", id_lesson=lesson.id, id_video=1))