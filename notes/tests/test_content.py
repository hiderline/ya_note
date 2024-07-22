from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from notes.forms import NoteForm
from notes.models import Note

User = get_user_model()


class TestContent(TestCase):
    TITLE = 'Note title'
    TEXT = 'Some note text'
    SLUG = 'note-slug'

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Author_user')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)

        cls.another_user = User.objects.create(username='Another_user')
        cls.another_user_client = Client()
        cls.another_user_client.force_login(cls.another_user)

        cls.note = Note.objects.create(
            title=cls.TITLE,
            text=cls.TEXT,
            slug=cls.SLUG,
            author=cls.author,
        )

        cls.URL_NOTES_LIST = reverse('notes:list')

    def test_note_in_list_for_author_client(self):
        """
        Отдельная заметка передаётся на страницу со списком заметок
        в списке object_list, в словаре context.
        """
        response = self.author_client.get(self.URL_NOTES_LIST)
        object_list = response.context['object_list']
        self.assertIn(self.note, object_list)

    def test_note_is_not_in_list_for_nonauthor_client(self):
        """
        В список заметок одного пользователя не попадают заметки
        другого пользователя.
        """
        response = self.another_user_client.get(self.URL_NOTES_LIST)
        object_list = response.context['object_list']
        self.assertNotIn(self.note, object_list)

    def test_note_in_list_availability_for_users(self):
        """
        Заметка передаётся в context['object_list']
        Пользователь может просматирвать только свои заметки
        """
        clients_status = (
            (self.author_client, True),
            (self.another_user_client, False),
        )
        for user_client, status in clients_status:
            with self.subTest(user_client):
                response = user_client.get(self.URL_NOTES_LIST)
                object_list = response.context['object_list']
                self.assertEqual(self.note in object_list, status)

    def test_note_creation_and_editing_pages_have_form(self):
        """
        На страницы создания и редактирования заметки передаются формы.
        """
        urls = (
            ('notes:add', None),
            ('notes:edit', (self.note.slug,)),
        )
        for url, args in urls:
            with self.subTest(url):
                url = reverse(url, args=args)
                response = self.author_client.get(url)
                self.assertIn('form', response.context)
                self.assertIsInstance(response.context['form'], NoteForm)
