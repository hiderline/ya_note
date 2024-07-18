from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

User = get_user_model()


class TestRoutes(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='User_author')
        cls.reader = User.objects.create(username='User_reader')

# Главная страница доступна анонимному пользователю.
    def test_home_page_availability_for_anonymous_user(self):
        url = reverse('notes:home')
        response = self.client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)

# Аутентифицированному пользователю доступны:
    # страница со списком заметок notes/,
    # страница успешного добавления заметки done/,
    # страница добавления новой заметки add/.

# Автору заметки доступны:
    # Страницы отдельной заметки,
    # удаления заметки
    # редактирования заметки
# Если на эти страницы попытается зайти другой пользователь —
	# вернётся ошибка 404.

# Анонимный пользователь перенаправляется на страницу логина
# при попытке перейти на:
    # страницу списка заметок,
    # отдельной заметки,
    # страницу успешного добавления записи,
    # страницу добавления заметки,
    # редактирования заметки,
    # удаления заметки

# Всем пользователям доступны:
    # страница регистрации пользователей,
    # страница входа в учётную запись,
    # страница выхода из учётной записи.