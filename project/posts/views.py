from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseNotAllowed, HttpResponseBadRequest, JsonResponse
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.core.paginator import Paginator
from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
from django.core.mail import send_mail
from django.conf import settings
from django.db import transaction, models

import json

from uuid import uuid4
from random import randint

from posts.forms import *
from posts.models import *

from .services.verification import generate_signed_token, verify_signed_token

POSTS_PER_PAGE = 10


#TODO:
#likes

def _display_posts_paginated(request, posts):
    """
    Helper function to display posts with pagination
    """
    paginator = Paginator(posts, POSTS_PER_PAGE)                    #paginator objects that handles serving objects on multiple pages
    page_num = request.GET.get("page")
    page_obj = paginator.get_page(page_num)             #retrieves only the posts for the given page

    # handle user reactions to posts for both logged in and anonymous users
    user_reactions = {}

    if request.user.is_authenticated:
        post_ids = [p.id for p in page_obj.object_list]
        for reaction in Reaction.objects.filter(post_id__in=post_ids, user=request.user):
            user_reactions[reaction.post_id] = reaction.type #like, dislake or none

    for post in page_obj.object_list:
        post.user_reaction = user_reactions.get(post.id, 'none')
 
    return render(request, 'feed.html', {'page_obj': page_obj})


def redirect_home():
    return redirect('/posts/?page=1')


def feed(request):
    posts = Post.objects.all().order_by('-publish_date')
    return _display_posts_paginated(request, posts)


def random_post(request):

    #edge case when there are no posts
    if Post.objects.all().exists():
        max_id = Post.objects.latest('id').id
    else:
        return redirect_home()

    random_id = randint(1,max_id)
    random_post = Post.objects.filter(id=random_id)
    #check in case of deleted items
    while not random_post.exists() and random_id < max_id:
        random_id += 1
        random_post = Post.objects.filter(id=random_id)

    return render(request, 'feed.html', {'page_obj': random_post})



def login(request):

    #redirect user to home if they are already logged in
    if request.user.is_authenticated:
        return redirect_home()

    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(username=username, password=password)
            if user:
                auth_login(request, user)
                return redirect_home()
            else:
                user = User.objects.filter(username=username).first()
                if user and not user.is_active:
                    form.add_error(None, "Odkaz pre overenie je v maili")
                else:
                    form.add_error(None, "Invalid username or password")
    else:
        form = UserLoginForm()
    
    return render(request, 'login.html', {"form":form})
    
    
@login_required(login_url='/posts/login/')   
def logout(request):
    auth_logout(request)
    return redirect_home()


@login_required(login_url='/posts/login/')   
def account(request):
    user = request.user
    name = user.username
    email = user.email

    return render(request, 'account.html', {
        'username': name,
        'email': email})

@login_required(login_url='/posts/login/')
def change_password(request):
    if request.method == "POST":
        user = request.user
        form = PasswordChangeForm(user,request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request,user)
            return redirect('account')
        
    else:
        form = PasswordChangeForm(request.user)
        return render(request, 'change_password.html', {'form': form})


@login_required
def user_posts(request):
    user = request.user
    posts = Post.objects.filter(author = user)
    return _display_posts_paginated(request, posts)


def register(request):
    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            
            #send verification mail
            user_email = form.cleaned_data['email']
            verification_token = generate_signed_token(user_id=user_email, purpose="email_verify")
            verification_url = f"{request.build_absolute_uri('/posts/verify_user/')}{verification_token}/"
            email_sent = send_mail(subject='Overenie registrácie - Urban Dictionary',
                message=f'Pre overenie účtu kliknite na link: {verification_url}',
                from_email=settings.EMAIL_HOST_USER,
                auth_user=settings.EMAIL_HOST_USER,
                auth_password=settings.EMAIL_HOST_PASSWORD,
                recipient_list=[user_email],
                fail_silently=False,
            )

            if email_sent:
                user = User.objects.filter(email=user_email).first()
                # update the username for user that was created previously
                if user:
                    user.username = form.cleaned_data['username']
                # create inactive user
                else:
                    user = form.save(commit=False)
                    user.is_active = False

                user.set_password(form.cleaned_data['password'])
                user.save()
                    
                messages.success(request, "Email pre overenie bol poslany.")
                return redirect('login')

    elif request.method == "GET":
        form = UserRegistrationForm()
    else:
        return HttpResponseNotAllowed(['GET', 'POST'])

    return render(request, "register.html", {"form":form})


def verify_user(request, token: str):
    """
    Verifies verification link and makes user active
    """
    try:
        user_mail = verify_signed_token(token, expected_purpose="email_verify")
    except ValueError as e:
        return HttpResponseBadRequest(str(e))
    
    user = User.objects.filter(email=user_mail).first()
    if user and not user.is_active:
        user.is_active = True
        user.save()
        
        messages.success(request, 'Účet bol vytvorený.')
        return redirect('login')
    else:
        return HttpResponseBadRequest("Neplatný odkaz")


def _create_post_authenticated(request):
    """
    Helper function for creating posts for registered users
    """
    if request.method == "POST":
        form = CreatePostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.publish_date = timezone.now()
            post.author = request.user
            post.save()
            return redirect_home()     
    
    elif request.method == "GET":
        form = CreatePostForm()
    else:
        return HttpResponseNotAllowed(['GET', 'POST'])

    return render(request, 'create_post.html', {"form":form})

def _create_post_guest(request):
    """
    Helper function for creating posts for guest users
    """
    if request.method == "POST":
        form = CreatePostFormGuest(request.POST)
        if form.is_valid():
            #send verification mail
            guest_email =form.cleaned_data['email_for_verification']
            verification_token = generate_signed_token(user_id=guest_email, purpose="post_verify")
            verification_url = f"{request.build_absolute_uri('/posts/verify_post/')}{verification_token}/"
            email_sent = send_mail(subject='Vytvorenie príspevku - Urban Dictionary',
                message=f'Vytvorte príspevok kliknutím na link: {verification_url}',
                from_email=settings.EMAIL_HOST_USER,
                auth_user=settings.EMAIL_HOST_USER,
                auth_password=settings.EMAIL_HOST_PASSWORD,
                recipient_list=[guest_email],
                fail_silently=False,
            )

            if email_sent:
                #remove any unverified posts connected to the user email
                user = User.objects.filter(email=guest_email).first()
                if user:
                    posts = PostUnverified.objects.filter(author = user)
                    if posts.exists():
                        posts.delete()

                #create inactive user with the mail and assigns temporary username, then generates automatic username from PK
                # Anon_ is used to avoid conflict as this username cannot be created by user in normal flow
                else:
                    #atomic operation to avoid race condition in case of multiple posts from the same email at the same time
                    with transaction.atomic():
                        user = User.objects.create(username='Anon_', email=guest_email, is_active=False)
                        user.username = f'Anon_{user.pk}'
                        user.save()

                #create a post (separate table from verified posts)
                post = form.save(commit=False)
                post.author = user          #connects the email to the post
                post.save()

                messages.success(request, "Email pre overenie bol poslaný.")
                return redirect_home()
            
            else:
                return HttpResponse("Nepodarilo sa poslat email pre overenie.", status=503)    
    
    elif request.method == "GET":
        form = CreatePostFormGuest()
    else:
        return HttpResponseNotAllowed(['GET', 'POST'])
    
    return render(request, 'create_post.html', {"form":form})

def create_post(request):
    """
    Top level function for creating posts for both registered and guest users
    """
    if request.user.is_authenticated:
        return _create_post_authenticated(request)
    else:
        return _create_post_guest(request)


def verify_post(request, token: str):
    """
    Verifies verification link and 
    """
    try:
        guest_email = verify_signed_token(token, expected_purpose="post_verify")
    except ValueError as e:
        return HttpResponseBadRequest(str(e))

    #there should be only one post connected to the email as we delete any unverified posts when new post is created with the same email
    post = PostUnverified.objects.get(author__email=guest_email)
    # move unverified post to verified post
    if post:
        Post.objects.create(
            post_title=post.post_title, 
            post_text=post.post_text, 
            post_example=post.post_example, 
            author=post.author, 
            publish_date=timezone.now()
            )
        post.delete()
        
        return redirect_home()
    else:
        return HttpResponseBadRequest("Neplatny odkaz")


def search(request):
    if request.method == "GET":
        search_text = request.GET.get('search')
        vector = SearchVector("post_title", "post_text", "post_example")
        query = SearchQuery(search_text)
        search_results = Post.objects\
            .annotate(rank=SearchRank(vector, query))\
            .filter(rank__gt=0)\
            .order_by("-rank")
        return _display_posts_paginated(request, search_results)
    else:
        return HttpResponseNotAllowed(['GET'])

@login_required(login_url='/posts/login/')
def toggle_reaction(request, post_id):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    
    post = get_object_or_404(Post, id=post_id)
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return HttpResponseBadRequest('Invalid JSON')
    type = payload.get('type')     #like or dislike
    if type not in (Reaction.ReactionType.LIKE, Reaction.ReactionType.DISLIKE):
        return HttpResponseBadRequest('Invalid reaction type.')
    
    with transaction.atomic():
        # user reaction to the post already exists
        try:
            reaction = Reaction.objects.select_for_update().get(user=request.user, post=post)

            # case for removing an existing reaction (e.g. clicking a like on liked post)
            if reaction.type == type:
                reaction.delete()
                # update post reaction counter
                if type == Reaction.ReactionType.LIKE:
                    post.like_count -= 1
                else:
                    post.dislike_count -= 1
                state = 'none'  # user has no reaction to the post
            
            # switching from like to dislike or vice versa case
            else:
                reaction.type = type
                reaction.save(update_fields=['type'])
                if type == Reaction.ReactionType.LIKE:
                    post.like_count += 1
                    post.dislike_count -= 1
                else:
                    post.dislike_count += 1
                    post.like_count -= 1
                state = type
            
        except Reaction.DoesNotExist:
            Reaction.objects.create(user=request.user, post=post, type=type)
            if type == Reaction.ReactionType.LIKE:
                post.like_count += 1
            else:
                post.dislike_count += 1
            state = type

        finally:
            post.save()

    post.refresh_from_db(fields=['like_count', 'dislike_count'])
    return JsonResponse({
        'state': state,     # 'like', 'dislike', 'none'
        'likes': post.like_count,
        'dislikes': post.dislike_count,
        'post_id': post_id
    })




    