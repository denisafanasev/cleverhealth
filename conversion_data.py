import os
from datetime import datetime

import sys
 # setting path
sys.path.append('../')

from data_adapters.data_store import DataStore
from models.course import Course
from models.module import Module
from models.lesson import Lesson
from models.homework import Homework
from models.homework_chat import HomeworkChat
from models.message import Message
import config


def conversion_module_data():
    """
    Конвертация формата данных модулей курсов и перенос в новый файл
    """
    data_store = DataStore('courses_list')
    data_store_module_new = DataStore("modules")

    courses_list = data_store.get_rows()
    for i_course in courses_list:
        course = Course(_id=i_course['id'])
        data_store_module = DataStore(f"course_{course.id}/modules")
        data_store.delete_key_in_row("id", "id", course.id)

        modules_list = data_store_module.get_rows()
        for i_module in modules_list:
            module = Module(_id=i_module['id'], _name=i_module['name'])
            if i_module.get("id_course") is None:
                module.id_course = course.id

            id_modules_edit = data_store_module_new.insert_row({"id_course": module.id_course, "name": module.name})

            conversion_lessons_data(module, id_modules_edit)

        # Так как мы перенесли в новый файл данные модулей и уроков всех курсов, то удаляем старый файл
        # На всякий случай закомментировал

        # if os.path.isfile(config.DATA_FOLDER + f"course_{course.id}/modules.json"):
        #     os.remove(config.DATA_FOLDER + f"course_{course.id}/modules.json")
        #
        # if os.path.isfile(config.DATA_FOLDER + f"course_{course.id}/lessons.json"):
        #     os.remove(config.DATA_FOLDER + f"course_{course.id}/lessons.json")


def conversion_lessons_data(_module, _id_module_edit):
    """
    Конвертация формата данных уроков курсов и перенос в новый файл

    Args:
        _module(Module): модуль
        _id_module_edit(Int): doc ID модуля
    """
    data_store_lesson_new = DataStore("lessons")
    data_store_lesson = DataStore(f"course_{_module.id_course}/lessons")

    lessons_list = data_store_lesson.get_rows({"id_module": _module.id})
    for i_lesson in lessons_list:
        lesson = Lesson(_id=i_lesson['id'], _id_module=_id_module_edit, _name=i_lesson["name"],
                        _materials=i_lesson['materials'], _link=i_lesson['link'])
        if i_lesson.get("text") is not None:
            lesson.text = i_lesson['text']

        if i_lesson.get("task") is not None:
            lesson.task = i_lesson['task']

        id_lesson_edit = data_store_lesson_new.insert_row({"id_module": lesson.id_module, "name": lesson.name,
                                       "materials": lesson.materials, "link": lesson.link,
                                       "text": lesson.text, "task": lesson.task, "id": lesson.id})

        # Так как у нас меняется ID у урока, то нужно найти все домашние задания, которые
        # прикреплены к данному уроку(пока не продумал до конца, как лучше сделать)
        conversion_homework_data(lesson.id, id_lesson_edit, _module.id_course)


def conversion_homework_data(_id_lesson, _id_lesson_edit, _id_course):
    """
    Конвертация формата данных домашних работ

    Args:
        _id_lesson(Int): ID урока
        _id_lesson_edit(Int): doc ID урока
        _id_course(Int): ID курса, в котором находится урок
    """
    data_store = DataStore("homeworks")
    data_store_answers = DataStore("homework_answers")

    homework_list = data_store.get_rows({"id_course": _id_course, "id_lesson": _id_lesson})
    for homework_data in homework_list:
        homework = Homework(_id=homework_data['id'], _id_lesson=homework_data['id_lesson'], _id_user=homework_data['id_user'])
        if homework_data.get("status") is None:
            homework_answer = data_store_answers.get_rows({"id_homework": homework.id})[0]
            homework.status = homework_answer['answer']

            data_store.update_row({"status": homework.status, "id": homework.id}, "id")

        if homework_data.get("id_course") is not None:
            data_store.delete_key_in_row("id_course", "id", homework.id)

        if homework_data.get('id_room_chat') is not None:
            data_store.delete_key_in_row("id_room_chat", "id", homework.id)

        if homework_data.get("id_learning_stream") is not None:
            data_store.delete_key_in_row("id_learning_stream", "id", homework.id)

        if homework_data.get("text") is None:
            data_store.update_row({"text": "", "id": homework.id}, "id")

        data_store.delete_key_in_row("id", "id", homework.id)


def conversion_room_chat_data():
    """
    Конвертация формата данных комнат чатов
    """
    data_store = DataStore("homework_chat")
    data_store_user = DataStore("users")
    data_store_lessons = DataStore("lessons")

    room_chat_list = data_store.get_rows()
    for room_chat_data in room_chat_list:
        # если есть у комнаты чата имя, то достаем из него нужную информацию, записываем ее отдельно и удаляем имя
        if room_chat_data.get("name"):
            ids_list = room_chat_data['name'].split("_")
            id_lesson = ids_list[2]
            login_user = ids_list[3]
            if len(ids_list) > 4:
                for index in range(4, len(ids_list)):
                    login_user = "_".join([login_user, ids_list[index]])

            lessons = data_store_lessons.get_rows({"id": int(id_lesson)})
            if len(lessons) == 1:
                id_lesson = lessons[0].doc_id
            elif len(lessons) > 1:
                for lesson in lessons:
                    if lesson['id_module'] == 1:
                        id_lesson = lesson.doc_id

            user = data_store_user.get_rows({"login": login_user})
            if user != []:
                room_chat = HomeworkChat(_id=room_chat_data['id'], _id_user=user[0].doc_id, _id_lesson=int(id_lesson))

                data_store.update_row({"id": room_chat.id, "id_lesson": room_chat.id_lesson, "id_user": room_chat.id_user}, "id")
                if room_chat_data.get('message') is not None:
                    for message in room_chat_data['message']:
                        conversion_message_data(message, room_chat_data.doc_id)

                    data_store.delete_key_in_row("message", "id", room_chat.id)

                if room_chat_data.get("id_education_stream") is not None:
                    data_store.delete_key_in_row("id_education_stream", "id", room_chat.id)

                data_store.delete_key_in_row("name", "id", room_chat.id)
                data_store.delete_key_in_row("id", "id", room_chat.id)


def conversion_message_data(_id_message, _id_homework_chat):
    """
    Конвертация формата данных сообщений

    Args:
        _id_message(Int): ID сообщения
        _id_homework_chat(Int): ID комнаты чата, в котором находится данное сообщение
    """

    data_store = DataStore("message")
    data_store_user = DataStore("users")

    message_data = data_store.get_rows({"id": _id_message})
    if message_data != []:
        message = Message(_id=message_data[0]['id'], _id_homework_chat=_id_homework_chat)
        if message_data[0].get("id_homework_chat") is None:
            data_store.update_row({"id_homework_chat": message.id_homework_chat, "id": message.id, "read": False}, "id")
            # data_store.delete_key_in_row('id_room_chat', 'id', message.id)

        # заменяет name_sender на id_user, если есть такой атрибут
        if message_data[0].get("name_sender") is not None:
            user = data_store_user.get_rows({"login": message_data[0]['name_sender']})
            if user != []:
                message.id_user = user[0].doc_id

                data_store.update_row({"id_user": message.id_user, "id": message.id}, "id")
                data_store.delete_key_in_row("name_sender", "id", message.id)

        # если нет даты отправки сообщения, то записываем сегодняшнюю дату
        if message_data[0].get("date_send") is None:
            message.date_send = datetime.now().strftime("%d/%m/%Y")

            data_store.update_row({"id": message.id, "date_send": message.date_send}, "id")

        try:
            data_store.delete_key_in_row("files", "id", message.id)
        except:
            pass

        data_store.update_row({"id": message.id, "read": message.read}, "id")
        data_store.delete_key_in_row("id", "id", _id_message)


def delete_id_key_in_lesson():
    """
    Удаляет ключ ID у уроков, так как больше не нужен(дальнейшие поиски будут по doc_id)
    """
    data_store = DataStore("lessons")

    lessons_list = data_store.get_rows()
    for lesson_data in lessons_list:
        if lesson_data.get("id") is not None:
            data_store.delete_key_in_row("id", "id", lesson_data['id'])


def create_copy_data():
    """
    Создает новые json файлы, в которые копирует текущие данные домашних работ, сообщения и чаты
    """
    data_store_homework = DataStore("homeworks")
    data_store_room_chat = DataStore("homework_chat")
    data_store_message = DataStore("message")
    data_store_homework_copy = DataStore("homeworks_copy")
    data_store_room_chat_copy = DataStore("room_chat_copy")
    data_store_message_copy = DataStore("message_copy")

    homework_list = data_store_homework.get_rows()
    for homework in homework_list:
        data_store_homework_copy.insert_row(homework)

    room_chat_list = data_store_room_chat.get_rows()
    for room_chat in room_chat_list:
        data_store_room_chat_copy.insert_row(room_chat)

    message_list = data_store_message.get_rows()
    for message in message_list:
        data_store_message_copy.insert_row(message)


# переименовываем файл room_chat.json на homework_chat.json
print("Переименовываем файл room_chat.json на homework_chat.json: ", end='')
os.rename(os.path.join(config.DATA_FOLDER, 'room_chat.json'), os.path.join(config.DATA_FOLDER, 'homework_chat.json'))
print("Файл переименован")

# Запуск функций для конвертации форматов данных
print("Запуск функций для конвертации форматов данных: ", end='')
create_copy_data()
print("done")

print("Запуск функции для конвертации формата данных уроков: ", end='')
conversion_module_data()
print("done")

print("Запуск функции для конвертации формата данных домашних работ: ", end='')
conversion_room_chat_data()
print("done")

print("Запуск функции для конвертации формата данных сообщений: ", end='')
delete_id_key_in_lesson()
print("done")

# и еще надо удалить файлы settings.json в каждой из папок с курсами
