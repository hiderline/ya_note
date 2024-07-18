from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from notes.models import Note

User = get_user_model()


class TestRoutes(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='User_author')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)

        cls.reader = User.objects.create(username='User_reader')
        cls.reader_client = Client()
        cls.reader_client.force_login(cls.reader)

        cls.note = Note.objects.create(
            title='Заголовок',
            text='Текст заметки',
            author=cls.author,
        )

    def test_home_page_availability_for_anonymous_user(self):
        """
        Главная страница доступна анонимному пользователю.
        """
        url = reverse('notes:home')
        response = self.client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_pages_availability_for_anonymous_user(self):
        """
        Всем пользователям доступны:
        - страница регистрации пользователей,
        - страница входа в учётную запись,
        - страница выхода из учётной записи.
        """
        clients = (
            self.client,
            self.author_client,
        )
        url_names = (
            'users:signup',
            'users:login',
            'users:logout',
        )
        for client in clients:
            for name in url_names:
                with self.subTest(client=client, name=name):
                    url = reverse(name)
                    response = client.get(url)
                    self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_pages_availability_for_auth_user(self):
        """
        Аутентифицированному пользователю доступны:
        - страница со списком заметок 'notes/',
        - страница добавления новой заметки 'add/',
        - страница успешного добавления заметки 'done/'.
        """
        urls = (
            ('notes:list'),
            ('notes:add'),
            ('notes:success'),
        )
        for name in urls:
            with self.subTest(name=name):
                url = reverse(name)
                response = self.author_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_pages_availability_for_users(self):
        """
        Доступны автору и недоступны другим пользователям:
        - страница отдельной заметки,
        - страница редактирования заметки,
        - страница удаления заметки,
        """
        users_statuses = (
            (self.author, HTTPStatus.OK),
            (self.reader, HTTPStatus.NOT_FOUND),
        )
        urls = (
            ('notes:detail', (self.note.slug,)),
            ('notes:edit', (self.note.slug,)),
            ('notes:delete', (self.note.slug,)),
        )
        for user, status in users_statuses:
            for name, args in urls:
                with self.subTest(user=user, name=name):
                    url = reverse(name, args=args)
                    self.client.force_login(user)
                    response = self.client.get(url)
                    self.assertEqual(response.status_code, status)

    def test_redirect_for_anonymous_client(self):
        """
        Анонимный пользователь перенаправляется на страницу логина
        при попытке перейти на:
        - страницу списка заметок,
        - отдельной заметки,
        - страницу успешного добавления записи,
        - страницу добавления заметки,
        - редактирования заметки,
        - удаления заметки
        """
        urls = (
            ('notes:detail', (self.note.slug,)),
            ('notes:edit', (self.note.slug,)),
            ('notes:delete', (self.note.id,)),
            ('notes:add', None),
            ('notes:success', None),
            ('notes:list', None),
        )
        login_url = reverse('users:login')

        for name, args in urls:
            with self.subTest(name=name):
                url = reverse(name, args=args)
                response = self.client.get(url)
                expected_url = f'{login_url}?next={url}'
                self.assertRedirects(response, expected_url)
