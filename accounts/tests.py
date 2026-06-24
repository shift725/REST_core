"""accounts app 單元測試（model、註冊／登入／登出、使用者列表／詳細）。"""

import uuid

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class CustomUserModelTests(APITestCase):
    """CustomUser model 行為（USERNAME_FIELD、UUIDv7 主鍵等）。"""

    def test_create_user_with_email_success(self):
        user = User.objects.create_user(
            username='alice',
            email='alice@example.com',
            password='strongpass123',
        )
        self.assertEqual(user.email, 'alice@example.com')
        self.assertEqual(user.username, 'alice')
        self.assertTrue(user.check_password('strongpass123'))
        self.assertFalse(user.check_password('wrongpass'))
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertEqual(user.role, 'member')

    def test_create_superuser_success(self):
        admin = User.objects.create_superuser(
            username='root',
            email='root@example.com',
            password='adminpass123',
        )
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)

    def test_primary_key_is_uuidv7(self):
        user = User.objects.create_user(
            username='bob', email='bob@example.com', password='pass12345'
        )
        self.assertIsInstance(user.id, uuid.UUID)
        self.assertEqual(user.id.version, 7)

    def test_str_returns_email(self):
        user = User.objects.create_user(
            username='carol', email='carol@example.com', password='pass12345'
        )
        self.assertEqual(str(user), 'carol@example.com')

    def test_email_must_be_unique(self):
        User.objects.create_user(username='u1', email='dup@example.com', password='pass12345')
        with self.assertRaises(IntegrityError):
            User.objects.create_user(username='u2', email='dup@example.com', password='pass12345')


class UserRegisterAPITests(APITestCase):
    """POST /api/auth/register/"""

    def setUp(self):
        self.url = reverse('auth:register')
        self.valid_payload = {
            'username': 'newbie',
            'email': 'newbie@example.com',
            'password': 'strongpass123',
            'password_confirm': 'strongpass123',
            'phone': '0912345678',
        }

    def test_register_success_returns_201_and_tokens(self):
        response = self.client.post(self.url, self.valid_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['message'], '註冊成功')
        self.assertIn('user', response.data)
        self.assertIn('tokens', response.data)
        self.assertIn('access', response.data['tokens'])
        self.assertIn('refresh', response.data['tokens'])
        self.assertTrue(User.objects.filter(email='newbie@example.com').exists())
        self.assertNotIn('password', response.data['user'])

    def test_register_password_mismatch_returns_400(self):
        payload = {**self.valid_payload, 'password_confirm': 'different123'}
        response = self.client.post(self.url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password_confirm', response.data)
        self.assertEqual(User.objects.count(), 0)

    def test_register_duplicate_email_returns_400(self):
        User.objects.create_user(
            username='existing', email='newbie@example.com', password='pass12345'
        )
        response = self.client.post(self.url, self.valid_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)
        self.assertEqual(str(response.data['email'][0]), '此 email 已被註冊')

    def test_register_duplicate_username_returns_400(self):
        User.objects.create_user(
            username='newbie', email='other@example.com', password='pass12345'
        )
        response = self.client.post(self.url, self.valid_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('username', response.data)

    def test_register_short_password_returns_400(self):
        payload = {**self.valid_payload, 'password': 'short', 'password_confirm': 'short'}
        response = self.client.post(self.url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)

    def test_register_numeric_password_returns_400(self):
        payload = {**self.valid_payload, 'password': '12345678', 'password_confirm': '12345678'}
        response = self.client.post(self.url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)


class LoginAPITests(APITestCase):
    """POST /api/auth/login/（CustomTokenObtainPairView）。"""

    @classmethod
    def setUpTestData(cls):
        cls.password = 'strongpass123'
        cls.user = User.objects.create_user(
            username='loginer',
            email='loginer@example.com',
            password=cls.password,
            role='staff',
        )

    def setUp(self):
        self.url = reverse('auth:login')

    def test_login_with_correct_credentials_returns_tokens(self):
        response = self.client.post(
            self.url,
            {'email': self.user.email, 'password': self.password},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertEqual(response.data['user']['email'], self.user.email)
        self.assertEqual(response.data['user']['username'], self.user.username)
        self.assertEqual(response.data['user']['role'], 'staff')

    def test_login_with_wrong_password_returns_401(self):
        response = self.client.post(
            self.url,
            {'email': self.user.email, 'password': 'wrong-password'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_with_username_field_does_not_work(self):
        response = self.client.post(
            self.url,
            {'username': self.user.username, 'password': self.password},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class LogoutAPITests(APITestCase):
    """POST /api/auth/logout/（refresh token 加入黑名單）。"""

    def setUp(self):
        self.url = reverse('auth:logout')
        self.user = User.objects.create_user(
            username='logoutuser',
            email='logout@example.com',
            password='pass12345',
        )
        self.refresh = RefreshToken.for_user(self.user)
        self.client.force_authenticate(user=self.user)

    def test_logout_success_blacklists_refresh_token(self):
        response = self.client.post(self.url, {'refresh': str(self.refresh)}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], '登出成功')

        # 同一 refresh 應無法再換 access token
        self.client.force_authenticate(user=None)
        refresh_response = self.client.post(
            reverse('auth:token_refresh'), {'refresh': str(self.refresh)}, format='json'
        )
        self.assertEqual(refresh_response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_with_invalid_token_returns_400(self):
        response = self.client.post(self.url, {'refresh': 'this-is-not-a-jwt'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_logout_without_authentication_returns_401(self):
        self.client.force_authenticate(user=None)
        response = self.client.post(self.url, {'refresh': str(self.refresh)}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class UserListAPITests(APITestCase):
    """GET /api/auth/users/（需登入）。"""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username='member1', email='m1@example.com', password='pass12345'
        )
        cls.other = User.objects.create_user(
            username='member2', email='m2@example.com', password='pass12345'
        )

    def setUp(self):
        self.url = reverse('auth:user_list')

    def test_list_requires_authentication(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_returns_all_users_when_authenticated(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)


class UserDetailAPITests(APITestCase):
    """GET / PATCH /api/auth/users/<uuid:pk>/。"""

    def setUp(self):
        self.member = User.objects.create_user(
            username='mem', email='mem@example.com', password='pass12345', role='member'
        )
        self.admin = User.objects.create_superuser(
            username='admin', email='admin@example.com', password='pass12345'
        )
        self.url = reverse('auth:user_detail', kwargs={'pk': self.member.pk})

    def test_detail_get_requires_authentication(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_detail_get_works_for_any_authenticated_user(self):
        self.client.force_authenticate(user=self.member)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'mem@example.com')

    def test_detail_patch_forbidden_for_non_admin(self):
        self.client.force_authenticate(user=self.member)
        response = self.client.patch(self.url, {'phone': '0900000000'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_detail_patch_allowed_for_admin(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.patch(self.url, {'phone': '0911222333'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.member.refresh_from_db()
        self.assertEqual(self.member.phone, '0911222333')
