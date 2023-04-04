from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post

User = get_user_model()


class StaticURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_homepage(self):
        '''Дымовая проверка главной страницы'''
        response = self.guest_client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_homepage(self):
        '''Проверка несуществующей страницы'''
        response = self.guest_client.get('/test')
        self.assertEqual(response.status_code, 404)

    def test_about_url_exists_at_desired_location(self):
        """Проверка доступности адреса /about/author/."""
        response = self.guest_client.get('/about/author/')
        self.assertEqual(response.status_code, 200)

    def test_about_url_uses_correct_template(self):
        """Проверка шаблона для адреса /about/author/."""
        response = self.guest_client.get('/about/author/')
        self.assertTemplateUsed(response, 'about/author.html')


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_author = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user_author,
            text='Тестовый пост',
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='TestName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def tearDown(self):
        # super().tearDown()
        cache.clear()

    def test_posts_edit_url_uses_correct_template(self):
        """Страница /posts/*/edit использует шаблон posts/create_post.html."""
        id = self.post.id
        self.author_client = Client()
        self.author_client.force_login(self.user_author)
        response = self.author_client.get(
            reverse('posts:post_edit', args=[id]))
        self.assertTemplateUsed(response, 'posts/create_post.html')

    def test_urls_uses_correct_template_guest(self):
        """URL-адрес использует соответствующий шаблон (пользователь гость)."""
        id = self.post.id
        # Шаблоны по адресам
        templates_url_names = {
            'posts/index.html': '/',
            'posts/group_list.html': '/group/test/',
            'posts/profile.html': '/profile/TestName/',
            'posts/post_detail.html': reverse('posts:post_detail', args=[id]),
        }
        for template, address in templates_url_names.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_urls_uses_correct_template_authorized(self):
        """URL-адрес использует соответствующий шаблон'''
        '''(авторизованный пользователь)."""
        id = self.post.id
        templates_url_names = {
            'posts/index.html': '/',
            'posts/group_list.html': '/group/test/',
            'posts/profile.html': '/profile/TestName/',
            'posts/post_detail.html': reverse('posts:post_detail', args=[id]),
            'posts/create_post.html': '/create/',
        }
        for template, address in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_create_url_redirect_anonymous(self):
        """Страница /create/ перенаправляет анонимного
        пользователя."""
        response = self.guest_client.get('/create/')
        self.assertEqual(response.status_code, 302)

    def test_edit_url_redirect_anonymous(self):
        """Страница /edit/ перенаправляет всех, кроме автора."""
        id = self.post.id
        response = self.guest_client.get(reverse('posts:post_edit', args=[id]))

        self.assertEqual(response.status_code, 302)
        response = self.authorized_client.get(
            reverse('posts:post_edit', args=[id]))
        self.assertEqual(response.status_code, 302)

    def test_404_custom_template(self):
        """Страница 404 отдаёт кастомный шаблон."""
        response = self.guest_client.get('/nonexist-page/')
        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, 'core/404.html')
