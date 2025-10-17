from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.core.paginator import Paginator
from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
from django.core.mail import send_mail
from django.conf import settings

from uuid import uuid4
from random import randint

from posts.forms import *
from posts.models import *

POSTS_PER_PAGE = 10


#TODO:
#likes
#email verification for registration

def _display_posts_paginated(request, posts):
    """
    Helper function to display posts with pagination
    """
    paginator = Paginator(posts, POSTS_PER_PAGE)                    #paginator objects that handles serving objects on multiple pages
    page_num = request.GET.get("page")
    page_obj = paginator.get_page(page_num)             #retrieves only the posts for the given page

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
            return HttpResponse("invalid form")
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
            verification_token = str(uuid4())
            verification_url = f"{request.build_absolute_uri('/posts/verify_user/')}{verification_token}/"
            email_sent = send_mail(subject='Overenie registracie - Urban Dictionary',
                message=f'Pre overenie uctu kliknite na link: {verification_url}',
                from_email=settings.EMAIL_HOST_USER,
                auth_user=settings.EMAIL_HOST_USER,
                auth_password=settings.EMAIL_HOST_PASSWORD,
                recipient_list=[user_email],
                fail_silently=False,
            )

            if email_sent:

                user = User.objects.filter(email=user_email).first()
                if user:
                    token = UserVerificationToken.objects.filter(user=user)
                    # update the verification token for existing user that exists from previous registration without verifying
                    if token.exists():
                        token.value = verification_token
                        token.save()
                    # update the user that was created from unregistered post creation
                    else:
                        token_obj = UserVerificationToken.objects.create(user=user, value=verification_token)
                        user.username = form.cleaned_data['username']
                        user.set_password(form.cleaned_data['password'])
                        user.save()

                # create inactive user and verification token
                else:
                    user = form.save(commit=False)
                    user.is_active = False
                    user.set_password(form.cleaned_data['password'])
                    user.save()
                    token_obj = UserVerificationToken.objects.create(user=user, value=verification_token)
                    
                messages.success(request, "Email pre overenie bol poslany.")
                return redirect('login')
        
    else:
        form = UserRegistrationForm()

    return render(request, "register.html", {"form":form})


def verify_user(request, token: str):
    """
    Verifies verification link and makes user active
    """
    token_obj = UserVerificationToken.objects.filter(value=token).first()
    if token_obj:
        #find associated user and make it active
        user = token_obj.user
        user.is_active = True
        user.save()

        token_obj.delete()
        
        messages.success(request, 'Ucet bol vytvoreny.')
        return redirect('login')
    else:
        return HttpResponse("Neplatny odkaz")


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
        else:
            form.add_error('Neplatny formular')
    
    else:
        form = CreatePostForm()

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
            verification_token = str(uuid4())
            verification_url = f"{request.build_absolute_uri('/posts/verify_post/')}{verification_token}/"
            email_sent = send_mail(subject='Vytvorenie prispevku - Urban Dictionary',
                message=f'Vytvorte prispevok kliknutim na link: {verification_url}',
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

                #create inactive with the mail and assigns temporary username using the token, then generates automatic username from PK
                # token is used to avoid collision before the username is generated using a PK which is unknown until creation of the object
                else:
                    user = User.objects.create(username=verification_token, email=guest_email, is_active=False)
                    user.username = f'Anon_{user.pk}'
                    user.save()

                #create a post (separate table from verified posts)
                post = form.save(commit=False)
                post.author = user          #connects the email to the post
                post.verification_token = verification_token
                post.save()

                messages.success(request, "Email pre overenie bol poslany.")
                return redirect_home()
            
            else:
                return HttpResponse("Nepodarilo sa poslat email pre overenie.")    
        else:
            return HttpResponse("invalid form")
    
    else:
        form = CreatePostFormGuest()
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
    post = PostUnverified.objects.filter(verification_token=token).first()
    if post:
        #move the post from unverified table to verified table
        title = post.post_title
        text = post.post_text
        example = post.post_example
        author = post.author
        date = timezone.now()
        Post.objects.create(post_title=title, post_text=text, post_example=example, author=author, publish_date=date)
        post.delete()
        
        return redirect_home()
    else:
        return HttpResponse("Neplatny odkaz")


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
        return HttpResponse('Invalid request type for search')
    