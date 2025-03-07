from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.core.paginator import Paginator
from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector

from posts.forms import *


#TODO:
#likes
#email verification for post creation and registration
#random word
#search

def redirect_home():
    return redirect('/posts/?page=1')

def feed(request):
    posts = Post.objects.all().order_by('-publish_date')

    paginator = Paginator(posts, 3)                    #paginator objects that handles serving objects on multiple pages
    page_num = request.GET.get("page")
    page_obj = paginator.get_page(page_num)             #retrieves only the posts for the given page

    return render(request, 'feed.html', {'page_obj': page_obj})

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
            if user and user.is_active:
                auth_login(request, user)
                return redirect_home()
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
    return HttpResponse("account page")

def register(request):
    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            #create user
            form.save()
            return redirect('login')
        
    else:
        form = UserRegistrationForm()
        return render(request, "register.html", {"form":form})

def random(request):
    return HttpResponse("random word page")

def create_post(request):
    if request.method == "POST":
        form = CreatePostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.publish_date = timezone.now()
            if request.user.is_authenticated:
                post.author = request.user
                post.save()
                return redirect_home()
            else:
                redirect('create_post_guest', post)      
        else:
            return HttpResponse("invalid form")
    
    else:
        form = CreatePostForm()
        return render(request, 'create_post.html', {"form":form})
    
def search(request):
    if request.method == "GET":
        search_text = request.GET.get('search')
        vector = SearchVector("post_title", "post_text", "post_example")
        query = SearchQuery(search_text)
        posts = Post.objects.annotate(rank=SearchRank(vector, query)).order_by("-rank")
        if posts.exists():
            feed(request, posts, 0)
        else:
            return HttpResponse('No posts found.')
    else:
        return HttpResponse('Invalid request type for search')

