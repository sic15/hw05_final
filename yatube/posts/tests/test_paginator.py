from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.core.cache import cache

from posts.models import Group, Post

User = get_user_model()


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test',
            description='Тестовое описание',
        )
        for i in range(15):
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

    def test_padjinator_index_records(self):
        '''Проверка паджинатора на главной странице'''
        response = self.client.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']), 10)
        response = self.client.get(reverse('posts:index') + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 5)

    def test_padjinator_group_list_records(self):
        '''Проверка паджинатора на group_list странице'''
        group = self.post.group.slug
        response = self.client.get(reverse('posts:group_list', args=[group]))
        self.assertEqual(len(response.context['page_obj']), 10)
        response = self.client.get(
            reverse(
                'posts:group_list',
                args=[group]) + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 5)

    def test_padjinator_profile_records(self):
        '''Проверка паджинатора на profile странице'''
        author = self.post.author.username
        response = self.client.get(reverse('posts:profile', args=[author]))
        self.assertEqual(len(response.context['page_obj']), 10)
        response = self.client.get(
            reverse(
                'posts:profile',
                args=[author]) + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 5)
