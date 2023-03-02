import os

from werkzeug.utils import redirect

from models.homework_chat_manager import HomeworkChatManager
from models.message_manager import MessageManager
from models.timetable_manager import TimetableManager
from models.user_manager import UserManager
from models.course_manager import EducationCourseManager
from models.module_manager import EducationModuleManager
from models.lesson_manager import EducationLessonManager
from models.education_stream_manager import EducationStreamManager
from models.homework_manager import HomeworkManager
from models.action_manager import ActionManager

from datetime import datetime
import config


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

        #education_streams = education_stream_manager.get_education_streams_list_by_login_user(user.login, user.role)

        #if _course_id is not None:
        #    for education_stream in education_streams:
        #        if education_stream.course == _course_id and education_stream.status == "идет":
        #            user.education_stream_list = education_stream

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
        course_manager = EducationCourseManager()
        module_manager = EducationModuleManager()
        timetable_manager = TimetableManager()
        education_stream_manager = EducationStreamManager()
        user_manager = UserManager()

        user = user_manager.get_user_by_id(_user_id)
        
        # если пользователь суперпользователь, то сразу возвращаем True и больше ничего не проверяем
        if user.role == 'superuser':
            return True

        # если это обычный пользователь, посмотрим что за курс и модуль
        course = course_manager.get_course_by_id(_course_id)

        if course.type == 'additional':
            # если дополнительный курс, то проверяем доступность модуля для пользователя по налицию у него общей подписки
            if user.education_module_expiration_date >= datetime.now():
                return True
            else:
                return False
        else:
            # если это основной курс, то проверяем доступность модуля по наличию подписки на обучающий курс

            # TODO: это надо перенести в целевую модель проверки вхождения пользователя в обущающий поток   

            course_modules = module_manager.get_course_modules_list(_course_id)
            # education_stream = education_stream_manager.get_education_stream_by_id_user_and_id_course(_user_id,
            #                                                                                           _course_id)
            # timetable = timetable_manager.get_timetable_by_id_module_and_id_education_stream(_module_id,
            #                                                                                  education_stream.id)
            # date_today = datetime.today()
            # if date_today >= timetable.date_start:
            #     return True

            # проверяем, есть ли пользователь в списках участников пятого потока
            for i in range(1, min(len(course_modules) + 1, 9)):
                if course_modules[i - 1].id == _module_id:
                    with open(config.DATA_FOLDER + 'course_1/s6_users.txt') as f:
                        course_users_list = f.read().splitlines()

                    for course_user in course_users_list:
                        if course_user.lower() == user.login:
                            return True
            
            for i in range(1, min(len(course_modules) + 1, 9)):
                if course_modules[i - 1].id == _module_id:
                    with open(config.DATA_FOLDER + 'course_1/s7_users.txt') as f:
                        course_users_list = f.read().splitlines()

                    for course_user in course_users_list:
                        if course_user.lower() == user.login:
                            return True
                        
            for i in range(1, min(len(course_modules) + 1, 9)):
                if course_modules[i - 1].id == _module_id:
                    with open(config.DATA_FOLDER + 'course_1/s1_users.txt') as f:
                        course_users_list = f.read().splitlines()

                    for course_user in course_users_list:
                        if course_user.lower() == user.login:
                            return True

            # проверяем, есть ли пользователь в списках участников четвертого потока
            for i in range(1, min(len(course_modules) + 1, 9)):
                if course_modules[i - 1].id == _module_id:
                    with open(config.DATA_FOLDER + 'course_1/s61_users.txt') as f:
                        course_users_list = f.read().splitlines()

                    for course_user in course_users_list:
                        if course_user.lower() == user.login:
                            return True

            '''
            # проверяем, есть ли пользователь в списках участников третьего потока
            for i in range(1, min(len(course_modules) + 1, 9)):
                if course_modules[i - 1].id == _module_id:
                    with open(config.DATA_FOLDER + 'course_1/s3_users.txt') as f:
                        course_users_list = f.read().splitlines()

                    for course_user in course_users_list:
                        if course_user.lower() == user.login:
                            return True
            '''

            return False

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
            homework_chat.unread_message_amount = message_manager.get_unread_messages_amount(homework_chat.id, _id_user)

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
                action_manager.add_notifications(module, "посмотрел", '', "course_manager", user.login)

            return redirect(f"/education_course/lesson?id_lesson={lesson.id}&id_video=1")