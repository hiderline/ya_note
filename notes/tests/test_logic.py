from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from notes.forms import WARNING
from notes.models import Note

User = get_user_model()

TITLE = 'Note title'
ANOTHER_TITLE = 'Another note title'
TEXT = 'Some note text'
ANOTHER_TEXT = 'Another note text'
SLUG = 'note-slug'


class TestLogic(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Author_user')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)

        cls.note_form_data = {
            'title': TITLE,
            'text': TEXT,
            'slug': SLUG,
        }
        cls.another_note_form_data = {
            'title': ANOTHER_TITLE,
            'text': ANOTHER_TEXT,
            'slug': SLUG,
        }

    def test_auth_user_can_create_note(self):
        """
        Залогиненный пользователь может создать заметку
        """
        url = reverse('notes:add')
        expected_url = reverse('notes:success')
        response = self.author_client.post(url, data=self.note_form_data)
        self.assertRedirects(response, expected_url)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)
        note = Note.objects.get()
        self.assertEqual(note.author, self.author)
        self.assertEqual(note.title, TITLE)
        self.assertEqual(note.text, TEXT)
        self.assertEqual(note.slug, SLUG)

    def test_anonymous_user_cannot_create_note(self):
        """
        Анонимный пользователь не может создать заметку
        """
        url = reverse('notes:add')
        self.client.post(url, data=self.note_form_data)
        self.assertEqual(Note.objects.count(), 0)

    def test_note_unique_slug(self):
        """
        Нельзя создать 2 заметки с одинаковым slug
        """
        url = reverse('notes:add')
        self.author_client.post(url, data=self.note_form_data)
        note = Note.objects.get()
        response = self.author_client.post(
            url,
            data=self.another_note_form_data
        )
        self.assertFormError(
            response,
            'form',
            'slug',
            errors=(note.slug + WARNING)
        )
        self.assertEqual(Note.objects.count(), 1)


# Если при создании заметки не заполнен slug,
#   то он формируется автоматически, с помощью функции pytils.translit.slugify.

# Пользователь может редактировать и удалять свои заметки,
#   но не может редактировать или удалять чужие.
