from django import forms
from posts.models import User, Post, PostUnverified
from django.core.exceptions import ValidationError


class UserLoginForm(forms.Form):
    username = forms.CharField(widget=forms.TextInput, min_length=2, max_length=20)
    password = forms.CharField(widget=forms.PasswordInput)

class UserRegistrationForm(forms.ModelForm):
    username = forms.CharField(widget=forms.TextInput)
    email = forms.CharField(widget=forms.EmailInput)
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

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

        errors = []

        if username.startswith('Anon_'):
            errors.append('Meno nemoze zacinat na Anon_')

        if username.startswith(' '):
            errors.append('Meno nemoze zacinat na medzeru')

        if password and confirm_password and password != confirm_password:
            errors.append("Hesla nesedia.")
        
        if User.objects.filter(email=email).exists():
            errors.append("Tento email je uz pouzity.")

        if errors:
            raise ValidationError(errors)
        
        return cleaned_data
    
class CreatePostForm(forms.ModelForm):
    post_title = forms.CharField(widget=forms.TextInput)
    post_text = forms.CharField(widget=forms.Textarea)
    post_example = forms.CharField(widget=forms.Textarea)
    
    class Meta:
        model = Post
        fields = ['post_title', 'post_text', 'post_example']

#same as CreatePostForm just with email field
class CreatePostFormGuest(CreatePostForm):
    email_for_verification = forms.CharField(widget=forms.EmailInput)
    class Meta:
        model = PostUnverified
        fields = ['post_title', 'post_text', 'post_example','email_for_verification']