from datetime import datetime, timedelta

from models.timetable import Timetable
from data_adapters.data_store import DataStore


class TimetableManager():

    def timetable_row_to_timetable(self, _data_row):
        """
        Преобразует структуру данных, в которой хранится информация о пользователи в структуру Timetable

        Args:
            _data_row (Dict): структура данных, которую возвращает дата адаптер

        Returns:
            Timetable: расписание открытия модуля
        """

        timetable = Timetable(_data_row.doc_id, _data_row['id_education_stream'], _data_row['id_module'],
                              _data_row['date_start'])

        return timetable

    def create_timetable(self, _data, _id_education_stream):
        """
        Сохраняет расписание потока

        Args:
            _data(List): список с расписаниями модулей обучающего потока
            _id_education_stream(Int): ID обучающего потока

        Returns:
            None
        """
        data_store = DataStore('timetables')

        for timetable_data in _data:
            timetable = Timetable(_id_education_stream=_id_education_stream,
                                  _id_module=timetable_data['id_module'], _date_start=timetable_data['date_start'])

            data_store.insert_row({'id_education_stream': timetable.id_education_stream, "id_module": timetable.id_module,
                                   'date_start': timetable.date_start.strftime("%d/%m/%Y")})

    def get_timetables_list_by_id_education_stream(self, _id_education_stream):
        """
        Возвращает список расписаний модулей для обучающего потока по _id_education_stream

        Args:
            _id_education_stream(Int): ID обучающего потока
        """

        data_store = DataStore('timetables')

        timetables_data_list = data_store.get_rows({'id_education_stream': _id_education_stream})
        timetables_list = []
        for timetable in timetables_data_list:
            timetables_list.append(self.timetable_row_to_timetable(timetable))

        return timetables_list

    def get_timetable_by_id_module_and_id_education_stream(self, _id_module, _id_education_stream):
        """
        Возвращает расписание по id модуля и id обучающего потока

        Args:
            _id_module(Int): ID модуля
            _id_education_stream(Int): ID обучающего потока

        Returns:
            TimeTable: расписание
        """
        data_store = DataStore('timetables')

        timetables_data_list = data_store.get_rows({'id_education_stream': _id_education_stream, 'id_module': _id_module})

        if len(timetables_data_list) == 1:
            return self.timetable_row_to_timetable(timetables_data_list[0])

    def save_timetable(self, _data, _id_education_stream):
        """
        Обновляем расписание

        Args:
            _data(List): список с расписаниями модулей обучающего потока
            _id_education_stream(Int): ID обучающего потока

        Returns:
            None
        """

        data_store = DataStore('timetables')

        timetables_list = self.get_timetables_list_by_id_education_stream(_id_education_stream)
        data_store.delete_row([timetable.id for timetable in timetables_list])

        self.create_timetable(_data, _id_education_stream)