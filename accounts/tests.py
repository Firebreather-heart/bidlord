from django.test import TestCase
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.urls import reverse

from rest_framework.test import APIClient, APITestCase
from rest_framework import status 
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.exceptions import ValidationError as VError

from .serializers import UserCreationSerializer
# Create your tests here.


User = get_user_model()


class CustomUserModelTests(TestCase):
    """Tests for the CustomUser model."""

    def setUp(self):
        self.user_data = {
            'username': 'testuser',
            'email': 'testmail@example.com',
            'password': 'testpassword',
            'password_confirm': 'testpassword'
        }

    def test_create_user(self):
        """Test creating a user with valid data."""
        user = User.objects.create_user(
            username=self.user_data['username'],
            email=self.user_data['email'],
            password=self.user_data['password']
        )
        self.assertEqual(user.username, self.user_data['username'])
        self.assertEqual(user.email, self.user_data['email'])
        self.assertTrue(user.check_password(self.user_data['password']))
        self.assertTrue(user.is_active)

    def test_create_user_with_duplicate_email(self):
        """Test creating a user with a duplicate email raises IntegrityError."""
        User = get_user_model()
        User.objects.create_user(
            username=self.user_data['username'],
            email=self.user_data['email'],
            password=self.user_data['password']
        )
        with self.assertRaises(IntegrityError):
            User.objects.create_user(
                username='anotheruser',
                email=self.user_data['email'],  
                password='anotherpassword123#P'
            )
    
    def test_create_user_with_duplicate_username(self):
        """Test creating a user with a duplicate username raises IntegrityError."""
        User = get_user_model()
        User.objects.create_user(
            username=self.user_data['username'],
            email=self.user_data['email'],
            password=self.user_data['password']
        )
        with self.assertRaises(IntegrityError):
            User.objects.create_user(
                username=self.user_data['username'],
                email="another@rmail.com",
                password='anotherpassword123P%'
            )

    def test_password_validator(self):
        """Test that the password meets the strength requirements."""
        User = get_user_model()
        with self.assertRaises(VError):
            user = UserCreationSerializer(
                data = self.user_data
            )
            user.is_valid(raise_exception=True)
            user.save()

class UserViewTests(APITestCase):
    """Tests for user views."""

    def setUp(self):
        self.client = APIClient()
        self.register_url = reverse('register')
        self.login_url = reverse('login')
        self.logout_url = reverse('logout')
        self.profile_url = reverse('edit_profile')

        self.valid_user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'password': 'SecurePass123!',
            'password_confirm': 'SecurePass123!'
        }

        self.conflict_user_data1 = {
            'username': 'existinguser',
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'password': 'SecurePass123!',
            'password_confirm': 'SecurePass123!'
        }

        self.conflict_user_data2 = {
            'username': 'newuser',
            'email': 'existing@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'password': 'SecurePass123!',
            'password_confirm': 'SecurePass123!'
        }

        self.weak_password_data = {
            'username': 'weakuser',
            'email': 'weak@example.com',
            'first_name': 'Weak',
            'last_name': 'User',
            'password': 'weak',  
            'password_confirm': 'weak'
        }

        self.existing_user = User.objects.create_user(
            username='existinguser',
            email='existing@example.com',
            password='SecurePass123!'
        )

    def test_user_registration_success(self):
        """Test user registration with valid data."""
        response = self.client.post(
            self.register_url,
            self.valid_user_data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('data', response.data) #type:ignore
        
        user_exists = User.objects.filter(
            username=self.valid_user_data['username'],
            email=self.valid_user_data['email']
        ).exists()
        self.assertTrue(user_exists)

    def test_user_registration_with_weak_password(self):
        """Test user registration with a weak password."""
        response = self.client.post(
            self.register_url,
            self.weak_password_data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('errors', response.data) #type:ignore
        self.assertIn('password', response.data['errors']) #type:ignore

    def test_registration_with_conflicting_username(self):
        """Test registration with an existing username."""
        response = self.client.post(
            self.register_url,
            self.conflict_user_data1,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('errors', response.data) #type:ignore
        self.assertIn('username', response.data['errors']) #type:ignore

    def test_registration_with_conflicting_email(self):
        """Test registration with an existing email."""
        response = self.client.post(
            self.register_url,
            self.conflict_user_data2,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('errors', response.data) #type:ignore
        self.assertIn('email', response.data['errors']) #type:ignore

    def test_user_login_success(self):
        """Test user login with valid credentials."""
        response = self.client.post(
            self.login_url,
            {
                'username_or_email': self.existing_user.username,
                'password': 'SecurePass123!'
            },
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data['data']) #type:ignore
        self.assertIn('refresh', response.data['data'])  # type:ignore
        self.assertEqual(response.data['data']['user']['username'], self.existing_user.username) #type:ignore

        response2 = self.client.post(
            self.login_url,
            {
                'username_or_email': self.existing_user.email,
                'password': 'SecurePass123!'
            },
            format='json'
        )
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        self.assertIn('access', response2.data['data'])  # type:ignore
        self.assertIn('refresh', response2.data['data'])  # type:ignore
        self.assertEqual(response2.data['data']['user']['username'], self.existing_user.username) #type:ignore

    
