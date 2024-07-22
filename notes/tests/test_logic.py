from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from pytils.translit import slugify

from notes.forms import WARNING
from notes.models import Note

User = get_user_model()


class TestLogic(TestCase):

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

        cls.URL_SUCCESS = reverse('notes:success')

    @classmethod
    def get_form_data(cls, title=TITLE, text=TEXT, slug=SLUG):
        return {
            'title': title,
            'text': text,
            'slug': slug
        }


class TestNoteCreate(TestLogic):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.note_form_data = super().get_form_data()
        cls.no_slug_form_data = super().get_form_data(slug='')
        cls.note_form_data_with_same_slug = super().get_form_data(
            title=cls.ANOTHER_TITLE,
            text=cls.ANOTHER_TEXT
        )

        cls.URL_NOTES_ADD = reverse('notes:add')

    def test_auth_user_can_create_note(self):
        """
        Залогиненный пользователь может создать заметку
        """
        response = self.author_client.post(
            self.URL_NOTES_ADD,
            data=self.note_form_data
        )
        self.assertRedirects(response, self.URL_SUCCESS)

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
        self.client.post(self.URL_NOTES_ADD, data=self.note_form_data)
        self.assertEqual(Note.objects.count(), 0)

    def test_note_unique_slug(self):
        """
        Нельзя создать 2 заметки с одинаковым slug
        """
        self.author_client.post(self.URL_NOTES_ADD, data=self.note_form_data)
        note = Note.objects.get()
        response = self.author_client.post(
            self.URL_NOTES_ADD,
            data=self.note_form_data_with_same_slug
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
        response = self.author_client.post(
            self.URL_NOTES_ADD,
            data=self.no_slug_form_data
        )
        self.assertRedirects(response, self.URL_SUCCESS)
        self.assertEqual(Note.objects.count(), 1)

        note = Note.objects.get()
        expected_slug = slugify(self.no_slug_form_data['title'])
        self.assertEqual(note.slug, expected_slug)


class TestNoteEdit(TestLogic):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.another_user = User.objects.create(username='Another_user')
        cls.another_user_client = Client()
        cls.another_user_client.force_login(cls.another_user)

        cls.note = Note.objects.create(
            title=cls.TITLE,
            text=cls.TEXT,
            slug=cls.SLUG,
            author=cls.author,
        )
        cls.another_note_form_data = super().get_form_data(
            title=cls.ANOTHER_TITLE,
            text=cls.ANOTHER_TEXT,
            slug=cls.ANOTHER_SLUG,
        )

        cls.URL_NOTES_EDIT = reverse('notes:edit', args=(cls.note.slug,))
        cls.URL_NOTES_DELETE = reverse('notes:delete', args=(cls.note.slug,))

    def test_author_can_edit_note(self):
        """
        Пользователь может редактировать свою заметку
        """
        response = self.author_client.post(
            self.URL_NOTES_EDIT,
            data=self.another_note_form_data
        )
        self.assertRedirects(response, self.URL_SUCCESS)

        self.note.refresh_from_db()
        self.assertEqual(self.note.title, self.ANOTHER_TITLE)
        self.assertEqual(self.note.text, self.ANOTHER_TEXT)
        self.assertEqual(self.note.slug, self.ANOTHER_SLUG)

    def test_author_can_delete_note(self):
        """
        Пользователь может удалить свою заметку
        """
        response = self.author_client.post(self.URL_NOTES_DELETE)
        self.assertRedirects(response, self.URL_SUCCESS)
        self.assertEqual(Note.objects.count(), 0)

    def test_another_user_cannot_edit_note(self):
        """
        Пользователь не может редактировать чужую заметку
        """
        note_from_db = Note.objects.get(id=self.note.id)
        response = self.another_user_client.post(
            self.URL_NOTES_EDIT,
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
        response = self.another_user_client.delete(self.URL_NOTES_DELETE)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertEqual(Note.objects.count(), 1)
