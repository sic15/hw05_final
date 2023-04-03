from django.db import models

from django.contrib.auth import get_user_model

User = get_user_model()


class Group(models.Model):
    title = models.CharField('Название группы', max_length=200)
    slug = models.SlugField(max_length=200, unique=True,)
    description = models.TextField('Описание группы')

    def __str__(self):
        return self.title


class Post(models.Model):
    text = models.TextField('Текст поста', help_text='Введите текст поста')
    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата публикации')
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name='Автор')
    group = models.ForeignKey(
        Group,
        blank=True,
        null=True,
        related_name='posts',
        on_delete=models.SET_NULL,
        verbose_name='Группа',
        help_text='Группа, к которой будет относиться пост')
    image = models.ImageField(
        'Картинка',
        upload_to='posts/',
        blank=True
    )

    def __str__(self):
        return self.text[:15]

    class Meta:
        ordering = ['-pub_date']
        verbose_name = 'Пост'
        verbose_name_plural = 'Посты'


class Comment(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Автор')
    text = models.TextField(
        'Текст комментария',
        help_text='Введите текст комментария')
    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата публикации')
    post = models.ForeignKey(
        Post,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='comments',
    )


class Follow(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Автор')
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Пользователь')
