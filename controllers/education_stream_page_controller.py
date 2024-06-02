from datetime import datetime, timedelta
import pandas as pd

from services.education_stream_card_service import EducationStreamCardService

class EducationStreamPageController():
    """
    Класс страницы карточки обучающего потока
    """    

    def get_students_list(self, _user_id, _id_education_stream=None):
        """
        Возвращает список студентов обучающего потока

        Args:
            _user_id(Int): ID текущего пользователя
            _id_education_stream(Int): ID обучающего потока

        Returns:
            students_list(List): список пользователей
        """

        education_stream_service = EducationStreamCardService()

        students = education_stream_service.get_students_list(_user_id, _id_education_stream)
        students_list = []
        if not isinstance(students, pd.DataFrame):
            
            for i_student in students:
                student = {
                    'id': i_student.user_id,
                    'login': i_student.login,
                    'name': i_student.name,
                    'email': i_student.email
                }

                students_list.append(student)
        
        else:
            
            students_df = students[['doc_id', 'login', 'name', 'email']]
            students_df = students_df.rename(columns={'doc_id': 'id'})
            
            students_list = students_df.to_dict('records')

        return students_list

    def get_curators_list(self, _user_id, _id_education_stream=None):
        """
        Возвращает список кураторов обучающего потока

        Args:
            _user_id(Int): ID текущего пользователя
            _id_education_stream(Int): ID обучающего потока

        Returns:
            curators_list(List): список пользователей
        """

        education_stream_service = EducationStreamCardService()

        curators = education_stream_service.get_curators_list(_user_id, _id_education_stream)
        curators_list = []
        if not isinstance(curators, pd.DataFrame):
             
            for i_curator in curators:
                curator = {
                    'id': i_curator.user_id,
                    'login': i_curator.login,
                    'name': i_curator.name,
                    'email': i_curator.email
                }

                curators_list.append(curator)
        
        else:
            curators_df = curators[['doc_id', 'login', 'name', 'email']]
            curators_df = curators_df.rename(columns={'doc_id': 'id'})
            curators_list = curators_df.to_dict('records')

        return curators_list

    def get_courses_list(self, _id_education_stream):
        """
        Возвращает список курсов

        Args:
            _timetables_list(List): список расписаний открытий модулей обучающего потока

        Returns:
            (List): список курсов
        """

        education_stream_service = EducationStreamCardService()

        courses = education_stream_service.get_courses_list()
        courses_list = []
        for course in courses:
            course_view = {
                'id': course.id,
                "name": course.name,
                'modules': []
            }

            for module in course.modules:
                timetable = education_stream_service.get_timetable_by_id_module_and_id_education_stream(module.id, _id_education_stream)
                module_view = {
                    "id": module.id,
                    'name': module.name,
                    'id_course': module.id_course
                }
                # Если есть расписание в потоке для данного модуля, то добавляем дату открытия этого модуля
                if timetable is not None:
                    module_view['date_start'] = timetable.date_start.strftime('%d/%m/%Y')

                course_view['modules'].append(module_view)

            courses_list.append(course_view)

        return courses_list

    def get_education_stream(self, _id):
        """
        Возвращает представление обучающего потока по id

        Args:
            _id(Int): идентификатор обучающего потока
        """

        education_stream_service = EducationStreamCardService()

        if _id is not None:
            education_stream = education_stream_service.get_education_stream(_id)
        else:
            education_stream = None

        if education_stream is not None:

            education_stream_view = {
                "id": education_stream.id,
                "name": education_stream.name,
                "course": {
                    "id": education_stream.course.id,
                    "name": education_stream.course.name,
                },
                "date_start": education_stream.date_start.strftime("%d/%m/%Y"),
                "date_end": education_stream.date_end.strftime("%d/%m/%Y"),
                "curators_list": education_stream.curators_list,
                "students_list": education_stream.students_list,
                "teacher": {
                    'id': education_stream.teacher.user_id,
                    'login': education_stream.teacher.login,
                    'email': education_stream.teacher.email
                },
                "status": education_stream.status
            }
            # for student in education_stream.students_list:
            #     education_stream_view['students_list'].append({
            #         'id': student.user_id,
            #         'login': student.login,
            #         'name': student.name
            #     })
            #
            # for curator in education_stream.curators_list:
            #     education_stream_view['curators_list'].append({
            #         'id': curator.user_id,
            #         'login': curator.login,
            #         'name': curator.name
            #     })

        else:
            education_stream_view = {
                "id": 0,
                "name": "Введите название потока..",
                "course": "Выберить курс обучающего потока..",
                "date_start": datetime.today().strftime("%d/%m/%Y"),
                "date_end": (datetime.today() + timedelta(days=60)).strftime("%d/%m/%Y"),
                "curators_list": "Выберите кураторов обучающего потока..",
                "students_list": "Выберите учащихся обучающего потока..",
                "teacher": "Выберите преподавателя обучающего потока..",
            }

        return education_stream_view
    
    def create_education_stream(self, _education_stream, _timetables_list, _current_user_id):
        """
        Создает обучающий поток

        Args:
            _education_stream(Dict): обучающий поток
            _timetables_list(List): расписание открытия модулей для обучающего потока
            _current_user_id(Int): ID текущего пользователя

        Returns:
            id(Int): идентификатор обучающего потока
        """
        education_stream_manager = EducationStreamCardService()

        id_education_stream = education_stream_manager.create_education_stream(_education_stream, _timetables_list,
                                                                               _current_user_id)

        return id_education_stream, 'Обучающий поток успешно создан.', 'Successful'

    def save_education_stream(self, _education_stream, _timetables_list, _current_user_id):
        """
        Изменяет данные обучающего потока

        Args:
            _education_stream(Dict): обновленные атрибуты обучающего потока
            _timetables_list(List): список расписаний открытия модулей для потока
            _current_user_id(Int): ID текущего пользователя

        Returns:
            None
        """

        education_stream_service = EducationStreamCardService()

        for timetable in _timetables_list:
            timetable['date_start'] = datetime.strptime(timetable['date_start'], '%d/%m/%Y')

        education_stream_service.save_education_stream(_education_stream, _timetables_list, _current_user_id)

        return 'Редактирование обучающего потока успешно завершено.', 'Successful'

    def get_timetables_list(self, _id):
        """
        Возвращает список расписаний

        Args:
            _id(Int): ID обучающего потока

        Returns
            List(Dict): список расписаний
        """
        education_stream_service = EducationStreamCardService()

        if _id is not None:
            timetables_list = education_stream_service.get_timetables_list(_id)
            timetables_list_view = []
            for timetable in timetables_list:
                module = education_stream_service.get_module_by_id(timetable.id_module)
                timetables_list_view.append({
                    'module': {
                        'id': module.id,
                        'name': module.name
                    },
                    'id_education_stream': timetable.id_education_stream,
                    'date_start': timetable.date_start.strftime("%d/%m/%Y")
                })

            return timetables_list_view
