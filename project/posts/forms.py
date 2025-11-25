from django import forms
from posts.models import User, Post, PostUnverified
from django.core.exceptions import ValidationError


class UserLoginForm(forms.Form):
    username = forms.CharField(widget=forms.TextInput, min_length=2, max_length=20, label='Prihlasovacie meno')
    password = forms.CharField(widget=forms.PasswordInput, label='Heslo')

class UserRegistrationForm(forms.ModelForm):
    username = forms.CharField(widget=forms.TextInput, label='Prihlasovacie meno')
    email = forms.CharField(widget=forms.EmailInput)
    password = forms.CharField(widget=forms.PasswordInput, label='Heslo')
    confirm_password = forms.CharField(widget=forms.PasswordInput, label='Overiť heslo')

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'confirm_password']

    #overriding clean function to check that passwords match
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")
        email = cleaned_data.get("email")
        username = cleaned_data.get('username')

        if username.startswith('Anon_'):
            self.add_error('username', 'Meno nemože začínať na Anon_')

        if username.startswith(' '):
            self.add_error('username', 'Meno nemože začínať medzerou')

        if password and confirm_password and password != confirm_password:
            self.add_error('password', "Heslá nesedia.")
        
        if User.objects.filter(email=email, is_active=True).exists():
            self.add_error('email', "Tento email je už použitý.")
        
        return cleaned_data
    
class CreatePostForm(forms.ModelForm):
    post_title = forms.CharField(widget=forms.TextInput, label='Výraz')
    post_text = forms.CharField(widget=forms.Textarea, label='Definícia')
    post_example = forms.CharField(widget=forms.Textarea, label='Príklad')
    
    class Meta:
        model = Post
        fields = ['post_title', 'post_text', 'post_example']

#same as CreatePostForm just with email field
class CreatePostFormGuest(CreatePostForm):
    email_for_verification = forms.CharField(widget=forms.EmailInput, label='Email pre overenie')
    class Meta:
        model = PostUnverified
        fields = ['post_title', 'post_text', 'post_example','email_for_verification']