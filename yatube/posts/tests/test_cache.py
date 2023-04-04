from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Post

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='TestName')
        self.post = Post.objects.create(
            author=self.user,
            text='Тестовый пост',
        )

    def test_cache(self):
        """Проверка кеширования главной страницы."""
        response = self.guest_client.get(reverse('posts:index'))
        self.assertIn(self.post.text, response.content.decode())
        self.post.delete()
        response_cache = self.guest_client.get(reverse('posts:index'))
        self.assertIn(self.post.text, response_cache.content.decode())
        cache.clear()
        response_empty = self.guest_client.get(reverse('posts:index'))
        self.assertNotIn(self.post.text, response_empty.content.decode())
