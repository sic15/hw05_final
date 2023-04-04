import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Comment, Group, Post

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class FormTests(TestCase):
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
            group=cls.group,
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_create_post(self):
        """Валидная форма создает запись с картинкой в базе данных."""
        posts_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Тестовый текст1',
            'image': uploaded,
        }
        response = self.authorized_client.post(reverse('posts:post_create'),
                                               data=form_data,
                                               follow=True
                                               )
        self.assertRedirects(response,
                             reverse('posts:profile',
                                     args=['auth']))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text='Тестовый текст1',
                image='posts/small.gif'
            ).exists()
        )

    def test_guest_create_post(self):
        """Неавторизованный пользователь пытается создать пост."""
        form_data = {
            'text': 'Тестовый текст1',
        }
        response = self.guest_client.post(reverse('posts:post_create'),
                                          data=form_data,
                                          follow=True
                                          )
        self.assertRedirects(response, '/auth/login/?next=/create/')

    def test_edit_post(self):
        """Валидная форма изменяет запись в базе данных."""
        form_data = {
            'text': 'Новый тестовый текст',
        }
        id = self.post.id
        response = self.authorized_client.post(
            reverse('posts:post_edit', args=[id]),
            data=form_data,
            follow=True)
        self.assertRedirects(response, reverse('posts:post_detail', args=[id]))
        self.assertTrue(
            Post.objects.filter(
                text='Новый тестовый текст',
            ).exists())

    def test_create_comment(self):
        """Валидная форма создает комментарий в базе данных."""
        comments_count = Comment.objects.count()
        form_data = {'text': 'Тестовый комментарий'}
        id = self.post.id
        response = self.authorized_client.post(
            reverse(
                'posts:add_comment',
                args=[id]),
            data=form_data,
            follow=True)
        self.assertRedirects(response,
                             reverse('posts:post_detail',
                                     args=[id]))
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        self.assertTrue(
            Comment.objects.filter(
                text='Тестовый комментарий'
            ).exists()
        )

    def test_guest_create_comment(self):
        """Неавторизованный пользователь пытается оставить комментарий."""
        form_data = {
            'text': 'Тестовый комментарий',
        }
        comments_count = Comment.objects.count()
        response = self.guest_client.post(
            reverse(
                'posts:add_comment',
                args=[
                    self.post.id]),
            data=form_data,
            follow=True)
        self.assertRedirects(
            response, f'/auth/login/?next=/posts/{self.post.id}/comment/')
        self.assertEqual(Comment.objects.count(), comments_count)

    def test_create_post_with_wrong_picture_format(self):
        """Форма не создает запись в базе данных,
        если формат картинки неверный."""
        posts_count = Post.objects.count()
        file_field = SimpleUploadedFile(
            "best_file_eva.txt",
            # note the b in front of the string [bytes]
            b"these are the file contents!"
        )
        form_data = {
            'text': 'Тестовый текст1',
            'image': file_field,
        }
        response = self.authorized_client.post(reverse('posts:post_create'),
                                               data=form_data,
                                               follow=True
                                               )
        self.assertEqual(Post.objects.count(), posts_count)
        super().assertFormError(
            response,
            'form',
            'image',
            'Загрузите правильное изображение. Файл,'
            'который вы загрузили, поврежден или не является изображением.')
