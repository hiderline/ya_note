from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from pytils.translit import slugify

from notes.forms import WARNING
from notes.models import Note

User = get_user_model()


class TestNoteCreate(TestCase):
    TITLE = 'Note title'
    ANOTHER_TITLE = 'Another note title'
    TEXT = 'Some note text'
    ANOTHER_TEXT = 'Another note text'
    SLUG = 'note-slug'

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Author_user')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)

        cls.note_form_data = {
            'title': cls.TITLE,
            'text': cls.TEXT,
            'slug': cls.SLUG,
        }
        cls.another_note_form_data = {
            'title': cls.ANOTHER_TITLE,
            'text': cls.ANOTHER_TEXT,
            'slug': cls.SLUG,
        }
        cls.form_without_slug = {
            'title': cls.TITLE,
            'text': cls.TEXT,
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
        self.assertEqual(note.title, self.TITLE)
        self.assertEqual(note.text, self.TEXT)
        self.assertEqual(note.slug, self.SLUG)

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

    def test_empty_slug_field_in_form(self):
        """
        Автоматическое формирование поля slug, если он отсутствует в форме
        """
        url = reverse('notes:add')
        response = self.author_client.post(url, data=self.form_without_slug)
        self.assertRedirects(response, reverse('notes:success'))
        self.assertEqual(Note.objects.count(), 1)
        note = Note.objects.get()
        expected_slug = slugify(self.form_without_slug['title'])
        self.assertEqual(note.slug, expected_slug)


class TestNoteEdit(TestCase):
# Пользователь может редактировать и удалять свои заметки,
#   но не может редактировать или удалять чужие.
    TITLE = 'Note title'
    ANOTHER_TITLE = 'Another note title'
    TEXT = 'Some note text'
    ANOTHER_TEXT = 'Another note text'
    SLUG = 'note-slug'
    ANOTHER_SLUG = 'another-note-slug'

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

        cls.another_note_form_data = {
            'title': cls.ANOTHER_TITLE,
            'text': cls.ANOTHER_TEXT,
            'slug': cls.ANOTHER_SLUG,
        }

    def test_author_can_edit_note(self):
        """
        Пользователь может редактировать свою заметку
        """
        url = reverse('notes:edit', args=(self.note.slug,))
        response = self.author_client.post(
            url,
            data=self.another_note_form_data
        )
        self.assertRedirects(response, reverse('notes:success'))

        self.note.refresh_from_db()
        self.assertEqual(self.note.title, self.ANOTHER_TITLE)
        self.assertEqual(self.note.text, self.ANOTHER_TEXT)
        self.assertEqual(self.note.slug, self.ANOTHER_SLUG)

    def test_author_can_delete_note(self):
        """
        Пользователь может удалить свою заметку
        """
        url = reverse('notes:delete', args=(self.note.slug,))
        response = self.author_client.post(url)
        self.assertRedirects(response, reverse('notes:success'))
        self.assertEqual(Note.objects.count(), 0)

    def test_another_user_cannot_edit_note(self):
        """
        Пользователь не может редактировать чужую заметку
        """
        url = reverse('notes:edit', args=(self.note.slug,))
        note_from_db = Note.objects.get(id=self.note.id)
        response = self.another_user_client.post(
            url,
            self.another_note_form_data
        )
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.note.refresh_from_db()
        self.assertEqual(self.note.title, note_from_db.title)
        self.assertEqual(self.note.text, note_from_db.text)
        self.assertEqual(self.note.slug, note_from_db.slug)

    def test_another_user_cannot_delete_note(self):
        """
        Пользователь не может удалить чужую заметку
        """
        url = reverse('notes:delete', args=(self.note.slug,))
        response = self.another_user_client.delete(url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertEqual(Note.objects.count(), 1)
