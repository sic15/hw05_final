from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page

from .forms import PostForm, CommentForm
from .models import Group, Post, User, Comment, Follow

POSTS_LIMIT = 10
CACHE_TIME = 20


@cache_page(CACHE_TIME, key_prefix='index_page')
def index(request):
    post_list = Post.objects.select_related('author', 'group')
    paginator = Paginator(post_list, POSTS_LIMIT)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(
        Group.objects.select_related(), slug=slug)
    posts = group.posts.all()
    paginator = Paginator(posts, POSTS_LIMIT)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    user = get_object_or_404(User, username=username)
    all_user_posts = Post.objects.filter(author=user)
    paginator = Paginator(all_user_posts, POSTS_LIMIT)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    following = False
    if request.user.is_authenticated:
        if Follow.objects.filter(author=user, user=request.user).exists():
            following = True
    context = {
        'author': user,
        'count_posts': all_user_posts.count(),
        'page_obj': page_obj,
        'following': following
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    current_post = get_object_or_404(
        Post.objects.select_related('author', 'group', ), id=post_id)
    comments = Comment.objects.filter(post=current_post)
    form = CommentForm(request.POST or None)
    comments = current_post.comments.all()
    if request.method == "POST":
        add_comment(request, current_post.id)
    context = {
        'form': form,
        'current_post': current_post,
        'comments': comments
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(request.POST or None, files=request.FILES or None,)
    if request.method == 'POST':
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('posts:profile', request.user)
        return render(request, 'posts/create_post.html', {'form': form})
    context = {
        'form': form,
        'is_edit': False,
        'title': 'Создание записи'
    }
    return render(request, 'posts/create_post.html', context)


def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if post.author != request.user:
        return redirect('posts:post_detail', post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post)
    if request.method == "POST":
        if form.is_valid():
            form.save()
            return redirect('posts:post_detail', post_id)
    context = {
        'is_edit': True,
        'form': form,
        'title': 'Редактирование записи'
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post.objects.filter(id=post_id))
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    # Посты авторов, на которых подписан текущий пользователь.
    author_list = request.user.follower.values('author')
    posts = Post.objects.filter(author__in=author_list)
    paginator = Paginator(posts, POSTS_LIMIT)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {'page_obj': page_obj}
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    # Подписаться на автора
    user = get_object_or_404(User, username=username)
    if Follow.objects.filter(author=user, user=request.user).count() != 0:
        return redirect('posts:profile', username=username)
    if user != request.user:
        Follow.objects.create(author=user, user=request.user)
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    # Дизлайк, отписка
    user = get_object_or_404(User, username=username)
    follow = Follow.objects.get(author=user, user=request.user)
    follow.delete()
    return redirect('posts:index')
