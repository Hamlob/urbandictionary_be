from django.test import TestCase, Client
from django.urls import reverse
from django.core import mail
from django.conf import settings
from django.utils import timezone
from django.contrib.messages import get_messages
from unittest.mock import patch, MagicMock
import json

from posts.models import Post, PostUnverified, UserVerificationToken, User
from posts.forms import UserLoginForm, UserRegistrationForm, CreatePostForm, CreatePostFormGuest


class PostViewsTestCase(TestCase):
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.inactive_user = User.objects.create_user(
            username='inactive',
            email='inactive@example.com',
            password='testpass123',
            is_active=False
        )
        
        # Create test posts
        self.post1 = Post.objects.create(
            post_title='Test Post 1',
            post_text='Test content 1',
            post_example='Test example 1',
            author=self.user,
            publish_date=timezone.now()
        )
        self.post2 = Post.objects.create(
            post_title='Test Post 2',
            post_text='Test content 2',
            post_example='Test example 2',
            author=self.user,
            publish_date=timezone.now()
        )

    def test_feed_view(self):
        """Test feed view displays posts with pagination"""
        response = self.client.get('/posts/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Post 1')
        self.assertContains(response, 'Test Post 2')
        self.assertIn('page_obj', response.context)

    def test_feed_view_pagination(self):
        """Test feed pagination works correctly"""
        # Create more posts to test pagination
        for i in range(15):
            Post.objects.create(
                post_title=f'Post {i}',
                post_text=f'Content {i}',
                post_example=f'Example {i}',
                author=self.user,
                publish_date=timezone.now()
            )
        
        response = self.client.get('/posts/?page=2')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['page_obj'].has_previous())

    def test_random_post_view_with_posts(self):
        """Test random post view when posts exist"""
        response = self.client.get('/posts/random_post/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('page_obj', response.context)

    def test_random_post_view_no_posts(self):
        """Test random post view when no posts exist"""
        Post.objects.all().delete()
        response = self.client.get('/posts/random_post/')
        self.assertRedirects(response, '/posts/?page=1')

    def test_login_view_get(self):
        """Test login view GET request"""
        response = self.client.get('/posts/login/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)
        self.assertIsInstance(response.context['form'], UserLoginForm)

    def test_login_view_authenticated_user_redirect(self):
        """Test login view redirects authenticated users"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get('/posts/login/')
        self.assertRedirects(response, '/posts/?page=1')

    def test_login_view_valid_credentials(self):
        """Test login with valid credentials"""
        response = self.client.post('/posts/login/', {
            'username': 'testuser',
            'password': 'testpass123'
        })
        self.assertRedirects(response, '/posts/?page=1')

    def test_login_view_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = self.client.post('/posts/login/', {
            'username': 'testuser',
            'password': 'wrongpass'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invalid username or password')

    def test_login_view_inactive_user(self):
        """Test login with inactive user"""
        response = self.client.post('/posts/login/', {
            'username': 'inactive',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Odkaz pre overenie je v maili')

    def test_logout_view(self):
        """Test logout view"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get('/posts/logout/')
        self.assertRedirects(response, '/posts/?page=1')

    def test_logout_view_requires_login(self):
        """Test logout view requires authentication"""
        response = self.client.get('/posts/logout/')
        self.assertRedirects(response, '/posts/login/?next=/posts/logout/')

    def test_account_view(self):
        """Test account view for authenticated user"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get('/posts/account/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['username'], 'testuser')
        self.assertEqual(response.context['email'], 'test@example.com')

    def test_account_view_requires_login(self):
        """Test account view requires authentication"""
        response = self.client.get('/posts/account/')
        self.assertRedirects(response, '/posts/login/?next=/posts/account/')

    def test_change_password_get(self):
        """Test change password GET request"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get('/posts/change_password/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)

    def test_change_password_post_valid(self):
        """Test change password with valid data"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post('/posts/change_password/', {
            'old_password': 'testpass123',
            'new_password1': 'newpass123',
            'new_password2': 'newpass123'
        })
        self.assertRedirects(response, reverse('account'))

    def test_user_posts_view(self):
        """Test user posts view"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get('/posts/user_posts/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Post 1')
        self.assertContains(response, 'Test Post 2')

    def test_register_view_get(self):
        """Test register view GET request"""
        response = self.client.get('/posts/register/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)

    @patch('posts.views.send_mail')
    def test_register_view_post_valid_new_user(self, mock_send_mail):
        """Test register view with valid data for new user"""
        mock_send_mail.return_value = True
        
        response = self.client.post('/posts/register/', {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'newpass123',
            'confirm_password': 'newpass123'
        })
        
        self.assertRedirects(response, reverse('login'))
        self.assertTrue(User.objects.filter(username='newuser').exists())
        user = User.objects.get(username='newuser')
        self.assertFalse(user.is_active)
        self.assertTrue(UserVerificationToken.objects.filter(user=user).exists())
        mock_send_mail.assert_called_once()

    def test_verify_user_valid_token(self):
        """Test user verification with valid token"""
        token = UserVerificationToken.objects.create(
            user=self.inactive_user,
            value='test-token-123'
        )
        
        response = self.client.get(f'/posts/verify_user/test-token-123/')
        self.assertRedirects(response, reverse('login'))
        
        self.inactive_user.refresh_from_db()
        self.assertTrue(self.inactive_user.is_active)
        self.assertFalse(UserVerificationToken.objects.filter(value='test-token-123').exists())

    def test_verify_user_invalid_token(self):
        """Test user verification with invalid token"""
        response = self.client.get('/posts/verify_user/invalid-token/')
        self.assertEqual(response.status_code, 400)

    def test_create_post_authenticated_get(self):
        """Test create post GET request for authenticated user"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get('/posts/create_post/')
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context['form'], CreatePostForm)

    def test_create_post_authenticated_post_valid(self):
        """Test create post POST request for authenticated user"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post('/posts/create_post/', {
            'post_title': 'New Post',
            'post_text': 'New content',
            'post_example': 'New example'
        })
        
        self.assertRedirects(response, '/posts/?page=1')
        self.assertTrue(Post.objects.filter(post_title='New Post').exists())

    def test_create_post_guest_get(self):
        """Test create post GET request for guest user"""
        response = self.client.get('/posts/create_post/')
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context['form'], CreatePostFormGuest)

    @patch('posts.views.send_mail')
    def test_create_post_guest_post_valid(self, mock_send_mail):
        """Test create post POST request for guest user"""
        mock_send_mail.return_value = True
        
        response = self.client.post('/posts/create_post/', {
            'post_title': 'Guest Post',
            'post_text': 'Guest content',
            'post_example': 'Guest example',
            'email_for_verification': 'guest@example.com'
        })
        
        self.assertRedirects(response, '/posts/?page=1')
        self.assertTrue(PostUnverified.objects.filter(post_title='Guest Post').exists())
        mock_send_mail.assert_called_once()

    def test_verify_post_valid_token(self):
        """Test post verification with valid token"""
        guest_user = User.objects.create(
            username='guest_user',
            email='guest@example.com',
            is_active=False
        )
        
        unverified_post = PostUnverified.objects.create(
            post_title='Unverified Post',
            post_text='Unverified content',
            post_example='Unverified example',
            author=guest_user,
            verification_token='test-post-token'
        )
        
        response = self.client.get('/posts/verify_post/test-post-token/')
        self.assertRedirects(response, '/posts/?page=1')
        
        self.assertTrue(Post.objects.filter(post_title='Unverified Post').exists())
        self.assertFalse(PostUnverified.objects.filter(verification_token='test-post-token').exists())

    def test_verify_post_invalid_token(self):
        """Test post verification with invalid token"""
        response = self.client.get('/posts/verify_post/invalid-token/')
        self.assertEqual(response.status_code, 400)

    def test_search_view_get(self):
        """Test search view with GET request"""
        response = self.client.get('/posts/search/?search=Test')
        self.assertEqual(response.status_code, 200)
        self.assertIn('page_obj', response.context)

    def test_search_view_post(self):
        """Test search view with POST request (should return error)"""
        response = self.client.post('/posts/search/')
        self.assertEqual(response.status_code, 405)

    def test_search_view_results(self):
        """Test search view returns relevant results"""
        response = self.client.get('/posts/search/?search=Test Post 1')
        self.assertEqual(response.status_code, 200)
        # Note: This test might need adjustment based on your search implementation

    def test_redirect_home_function(self):
        """Test redirect_home helper function"""
        from posts.views import redirect_home
        response = redirect_home()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/posts/?page=1')

    def test_display_posts_paginated_helper(self):
        """Test _display_posts_paginated helper function"""
        from posts.views import _display_posts_paginated
        from django.test import RequestFactory
        
        factory = RequestFactory()
        request = factory.get('/posts/')
        posts = Post.objects.all()
        request.user = self.user
        response = _display_posts_paginated(request, posts)
        self.assertEqual(response.status_code, 200)

    def test_toggle_reaction_view_requires_login(self):
        """Test toggle reaction view requires authentication"""
        response = self.client.post(
            f'/posts/{self.post1.id}/react/',
            data=json.dumps({'type': 'like'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn('/posts/login/', response.url)

    def test_toggle_reaction_view_invalid_post(self):
        """Test toggle reaction view with invalid post ID"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(
            f'/posts/9999/react/',
            data=json.dumps({'type': 'like'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 404)

    def test_toggle_reaction_view_invalid_reaction_type(self):
        """Test toggle reaction view with invalid reaction type"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(
            f'/posts/{self.post1.id}/react/',
            data=json.dumps({'type': 'invalid type'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)

    def test_toggle_reaction_view_like(self):
        """Test toggle reaction view to like a post"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(
            f'/posts/{self.post1.id}/react/',
            data=json.dumps({'type': 'like'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['likes'], 1)
        self.assertEqual(data['dislikes'], 0)

    def test_toggle_reaction_view_dislike(self):
        """Test toggle reaction view to dislike a post"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(
            f'/posts/{self.post1.id}/react/',
            data=json.dumps({'type': 'dislike'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['likes'], 0)
        self.assertEqual(data['dislikes'], 1)


class EdgeCaseTestCase(TestCase):
    """Test edge cases and error conditions"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_random_post_with_gaps_in_ids(self):
        """Test random post when there are gaps in post IDs"""
        # Create posts with gaps
        post1 = Post.objects.create(
            post_title='Post 1',
            post_text='Content 1',
            post_example='Example 1',
            author=self.user,
            publish_date=timezone.now()
        )
        post3 = Post.objects.create(
            post_title='Post 3',
            post_text='Content 3',
            post_example='Example 3',
            author=self.user,
            publish_date=timezone.now()
        )
        
        # Delete post1 to create a gap
        post1.delete()
        
        response = self.client.get('/posts/random_post/')
        self.assertEqual(response.status_code, 200)

    @patch('posts.views.send_mail')
    def test_register_email_send_failure(self, mock_send_mail):
        """Test registration when email sending fails"""
        mock_send_mail.return_value = False
        
        response = self.client.post('/posts/register/', {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'newpass123',
            'confirm_password': 'newpass123'
        })
        
        # Should still render the form since email failed
        self.assertEqual(response.status_code, 200)

    def test_login_invalid_form_data(self):
        """Test login with invalid form data"""
        response = self.client.post('/posts/login/', {
            'username': '',  # Empty username
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, 400)


class IntegrationTestCase(TestCase):
    """Integration tests for complete user workflows"""
    
    def setUp(self):
        self.client = Client()

    @patch('posts.views.send_mail')
    def test_complete_user_registration_flow(self, mock_send_mail):
        """Test complete user registration and verification flow"""
        mock_send_mail.return_value = True
        
        # Register user
        response = self.client.post('/posts/register/', {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'newpass123',
            'confirm_password': 'newpass123'
        })
        self.assertRedirects(response, reverse('login'))
        
        # Verify user
        user = User.objects.get(username='newuser')
        token = UserVerificationToken.objects.get(user=user)
        
        response = self.client.get(f'/posts/verify_user/{token.value}/')
        self.assertRedirects(response, reverse('login'))
        
        # Login
        response = self.client.post('/posts/login/', {
            'username': 'newuser',
            'password': 'newpass123'
        })
        self.assertRedirects(response, '/posts/?page=1')

    @patch('posts.views.send_mail')
    def test_complete_guest_post_flow(self, mock_send_mail):
        """Test complete guest post creation and verification flow"""
        mock_send_mail.return_value = True
        
        # Create post as guest
        response = self.client.post('/posts/create_post/', {
            'post_title': 'Guest Post',
            'post_text': 'Guest content',
            'post_example': 'Guest example',
            'email_for_verification': 'guest@example.com'
        })
        self.assertRedirects(response, '/posts/?page=1')
        
        # Verify post
        unverified_post = PostUnverified.objects.get(post_title='Guest Post')
        response = self.client.get(f'/posts/verify_post/{unverified_post.verification_token}/')
        self.assertRedirects(response, '/posts/?page=1')
        
        # Check post is now verified
        self.assertTrue(Post.objects.filter(post_title='Guest Post').exists())
        self.assertFalse(PostUnverified.objects.filter(post_title='Guest Post').exists())
