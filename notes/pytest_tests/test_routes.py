from http import HTTPStatus

import pytest
from pytest_django.asserts import assertRedirects

from django.urls import reverse


# Указываем в фикстурах встроенный клиент.
def test_home_availability_for_anonymous_user(client):
    # Адрес страницы получаем через reverse():
    url = reverse('notes:home')
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK


# параметризованный тест, в котором объединим все адреса,
# доступные для анонимных пользователей.
@pytest.mark.parametrize(
    'name',  # Имя параметра функции.
    # Значения, которые будут передаваться в name.
    ('notes:home', 'users:login', 'users:logout', 'users:signup')
)
# Указываем имя изменяемого параметра в сигнатуре теста.
def test_pages_availability_for_anonymous_user(client, name):
    url = reverse(name)  # Получаем ссылку на нужный адрес.
    response = client.get(url)  # Выполняем запрос.
    assert response.status_code == HTTPStatus.OK


# Тестирование доступности страниц для авторизованного пользователя
# @pytest.mark.parametrize(
#     'name',
#     ('notes:list', 'notes:add', 'notes:success')
# )
# def test_pages_availability_for_auth_user(admin_client, name):
#     url = reverse(name)
#     response = admin_client.get(url)
#     assert response.status_code == HTTPStatus.OK

# Применение встроенной фикстуры admin_client может дать побочный эффект,
# если вдруг права администратора системы будут более широкими,
# чем права обычного залогиненного пользователя.
# Поэтому лучше не «злоупотреблять» с фикстурой admin_client,
# а создать отдельную пользовательскую фикстуру для залогиненного пользователя.
@pytest.mark.parametrize(
    'name',
    ('notes:list', 'notes:add', 'notes:success')
)
def test_pages_availability_for_auth_user(not_author_client, name):
    url = reverse(name)
    response = not_author_client.get(url)
    assert response.status_code == HTTPStatus.OK


# Проверим, что автору заметки доступны:
# страницы отдельной заметки, её редактирования и удаления.
# а "не автор" заметки будет получать 404
# Параметризуем тестирующую функцию двумя декорматорами:

# Добавляем к тесту ещё один декоратор parametrize; в его параметры
# нужно передать фикстуры-клиенты и ожидаемый код ответа для каждого клиента.
@pytest.mark.parametrize(
    # parametrized_client - название параметра,
    # в который будут передаваться фикстуры;
    # Параметр expected_status - ожидаемый статус ответа.
    'parametrized_client, expected_status',
    # В кортеже с кортежами передаём значения для параметров:
    (
        (pytest.lazy_fixture('not_author_client'), HTTPStatus.NOT_FOUND),
        (pytest.lazy_fixture('author_client'), HTTPStatus.OK)
    ),
)
@pytest.mark.parametrize(
    'name',
    ('notes:detail', 'notes:edit', 'notes:delete'),
)
# В параметры теста добавляем имена parametrized_client и expected_status.
def test_pages_availability_for_different_users(
    parametrized_client, expected_status, name, slug_for_args
):
    url = reverse(name, args=slug_for_args)
    # Делаем запрос от имени клиента parametrized_client:
    response = parametrized_client.get(url)
    # Ожидаем ответ страницы, указанный в expected_status:
    assert response.status_code == expected_status


# Тестирование редиректов
# При тестировании редиректов нужно проверить шесть страниц:
    # страницу отдельной записи,
    # страницу редактирования записи,
    # страницу удаления записи,
    # страницу добавления записи,
    # страницу успешного добавления записи,
    # страницу со списком записей.
@pytest.mark.parametrize(
    # Вторым параметром передаём note_object,
    # в котором будет либо фикстура с объектом заметки, либо None.
    'name, args',
    (
        ('notes:detail', pytest.lazy_fixture('slug_for_args')),
        ('notes:edit', pytest.lazy_fixture('slug_for_args')),
        ('notes:delete', pytest.lazy_fixture('slug_for_args')),
        ('notes:add', None),
        ('notes:success', None),
        ('notes:list', None),
    ),
)
# Передаём в тест анонимный клиент, name проверяемых страниц и note_object:
def test_redirects(client, name, args):
    login_url = reverse('users:login')
    # Формируем URL в зависимости от того, передан ли объект заметки:
    url = reverse(name, args=args)
    expected_url = f'{login_url}?next={url}'
    response = client.get(url)
    # Ожидаем, что со всех проверяемых страниц анонимный клиент
    # будет перенаправлен на страницу логина:
    assertRedirects(response, expected_url)

