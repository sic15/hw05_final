from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django import forms
from posts.models import Group, Post
from django.core.cache import cache

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='TestName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

        self.user1 = User.objects.create_user(username='TestName1')
        self.authorized_client1 = Client()
        self.authorized_client1.force_login(self.user1)

    def test_post_in_followers(self):
        """Новая запись пользователя появляется в ленте тех, кто на него подписан."""
        form_data = {'text': 'Тестовый пост'}
        self.authorized_client.post(reverse('posts:post_create'),
                                    data=form_data,
                                    follow=True
                                    )
        self.authorized_client1.post(
            reverse('posts:profile_follow', args=['TestName']),
            follow=True)
        response = self.authorized_client1.get(reverse('posts:follow_index'))
        self.assertIn('Тестовый пост', response.content.decode())

    def test_post_in_not_followers(self):
        """Новая запись пользователя не появляется в ленте тех, кто на него не подписан."""
        form_data = {'text': 'Тестовый пост'}
        self.authorized_client.post(reverse('posts:post_create'),
                                    data=form_data,
                                    follow=True
                                    )
        response = self.authorized_client1.get(reverse('posts:follow_index'))
        self.assertNotIn('Тестовый пост', response.content.decode())

    def test_subscribe(self):
        """Авторизованный пользователь может подписываться на других пользователей."""
        form_data = {'text': 'Тестовый пост'}
        self.authorized_client.post(reverse('posts:post_create'),
                                    data=form_data,
                                    follow=True
                                    )
        self.authorized_client1.post(
            reverse('posts:profile_follow', args=['TestName']),
            follow=True)
        # Проверяем, что удалось подписаться
        response = self.authorized_client1.get(reverse('posts:follow_index'))
        self.assertIn('Тестовый пост', response.content.decode())

    def test_unsubscribe(self):
        """Авторизованный пользователь может отписываться от других пользователей."""
        form_data = {'text': 'Тестовый пост'}
        self.authorized_client.post(reverse('posts:post_create'),
                                    data=form_data,
                                    follow=True
                                    )
        self.authorized_client1.post(
            reverse('posts:profile_follow', args=['TestName']),
            follow=True)
        # Проверяем, что удалось отписаться
        response1 = self.authorized_client1.get(
            reverse('posts:profile_unfollow', args=['TestName']))
        self.assertNotIn('Тестовый пост', response1.content.decode())
