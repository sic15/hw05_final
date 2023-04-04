from django import forms
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='TestName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def tearDown(self):
        cache.clear()

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        id = self.post.id
        templates_pages_names = {
            'posts/index.html': '',
            'posts/group_list.html':
            reverse('posts:group_list', args=['test']),
            'posts/profile.html': reverse('posts:profile', args=['TestName']),
            'posts/post_detail.html': reverse('posts:post_detail', args=[id]),
            'posts/create_post.html': '/create/',
        }
        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.guest_client.get(reverse('posts:index'))
        first = response.context.get('page_obj')[0]
        self.assertIn('page_obj', response.context.keys())
        self.assertEqual(first.author.username, 'auth')
        self.assertEqual(first.text, 'Тестовый пост')
        self.assertEqual(first.group.title, 'Тестовая группа')

    def test_group_list_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.guest_client.get(
            reverse('posts:group_list', args=['test']))
        context = {'group', 'page_obj'}
        for key in context:
            self.assertIn(key, response.context.keys())
        self.assertEqual(
            response.context.get('group').title, 'Тестовая группа')
        first = response.context.get('page_obj')[0]
        self.assertEqual(first.author.username, 'auth')
        self.assertEqual(first.text, 'Тестовый пост')
        self.assertEqual(first.group.title, 'Тестовая группа')

    def test_profile_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        author = self.post.author
        response = self.authorized_client.get(
            reverse('posts:profile', args=[author]))
        context = {'author', 'count_posts', 'page_obj', 'following'}
        for key in context:
            self.assertIn(key, response.context.keys())
        first = response.context.get('page_obj')[0]
        self.assertEqual(first.author.username, 'auth')
        self.assertEqual(first.text, 'Тестовый пост')
        self.assertEqual(first.group.title, 'Тестовая группа')

    def test_post_detail_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        id = self.post.id
        response = self.guest_client.get(
            reverse('posts:post_detail', args=[id]))
        context = {'current_post'}
        for key in context:
            self.assertIn(key, response.context.keys())
        self.assertEqual(response.context.get('current_post').text,
                         'Тестовый пост')

    def test_post_create_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.CharField,
            'group': forms.ModelChoiceField,
        }
        context = {'form', 'is_edit', 'title'}
        for key in context:
            self.assertIn(key, response.context.keys())
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        id = self.post.id
        self.author = self.post.author
        self.author_client = Client()
        self.author_client.force_login(self.author)
        response = self.author_client.get(
            reverse('posts:post_edit', args=[id]))
        form_fields = {
            'text': forms.CharField,
            'group': forms.ModelChoiceField
        }
        context = {'form', 'is_edit', 'title'}
        for key in context:
            self.assertIn(key, response.context.keys())
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_group_in_index(self):
        """Пост с указанной группой появился на главной странице."""
        response = self.guest_client.get(reverse('posts:index'))
        first = response.context.get('page_obj')[0]
        id = self.post.id
        self.assertEqual(first.id, id)

    def test_post_group_in_group_list(self):
        """Пост с указанной группой появился на странице группы."""
        response = self.guest_client.get(
            reverse('posts:group_list', args=['test']))
        first = response.context.get('page_obj')[0]
        id = self.post.id
        self.assertEqual(first.id, id)

    def test_post_group_in_profile(self):
        """Пост с указанной группой появился на странице profile."""
        author = self.post.author.username
        response = self.guest_client.get(
            reverse('posts:profile', args=[author]))
        first = response.context.get('page_obj')[0]
        id = self.post.id
        self.assertEqual(first.id, id)

    def test_post_group_not_in_wrong_group(self):
        """Пост с указанной группой не появился на странице неверной группы."""
        group1 = Group.objects.create(
            title='Тестовая группа 1 ',
            slug='test1',
            description='Тестовое описание1',
        )
        self.guest_client.get(reverse('posts:group_list', args=['test1']))
        self.assertEqual(Post.objects.filter(group=group1).count(), 0)
