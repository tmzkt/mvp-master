from model_bakery import baker
from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.core import mail
from django.db.models import ObjectDoesNotExist

from cms.models import HealthData, Result
from .forms import CustomUserCreationForm, ProfileForm, HealthDataForm
from .models import CustomUser
from cms.converting import feet_tu_cm, cm_to_feet


User = get_user_model()
# Create your tests here.
class CustomUserTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='test@test.ru', password='testpass123')
        self.admin_user = User.objects.create_superuser(email='superadmin@mail.com',password='testpass1234')

    def test_create_user(self):
        self.assertEqual(self.user.email, 'test@test.ru')
        self.assertTrue(self.user.is_active)
        self.assertFalse(self.user.is_staff)
        self.assertFalse(self.user.is_superuser)
        self.assertFalse(self.user.email_confirm)

    def test_create_superuser(self):
        self.assertEqual(self.admin_user.email, 'superadmin@mail.com')
        self.assertTrue(self.admin_user.is_active)
        self.assertTrue(self.admin_user.is_staff)
        self.assertTrue(self.admin_user.is_superuser)
        self.assertTrue(self.admin_user.email_confirm)

class SignupTests(TestCase):
    email = 'newuser@email.com'
    password = 'django1234'
    def setUp(self):
        self.url = reverse('users:signup')
        self.resp = self.client.get(self.url)

    def test_signup_template(self):
        self.assertEqual(self.resp.status_code, 200)
        self.assertTemplateUsed(self.resp, 'registration/signup.html')
        self.assertContains(self.resp, 'Sign up')
        self.assertNotContains(
            self.resp, 'Hi there! I should not be on the page.')

    def test_singup(self):
        self.resp = self.client.post(self.url, data={'email': self.email, 'password1': self.password,
                                  'password2': self.password})
        self.assertEqual(self.resp.status_code, 200)
        self.assertTemplateUsed(self.resp, 'registration/signup_done.html')

    def test_signup_create(self):
        new_user = User.objects.create_user(self.email, self.password)
        dashboard = HealthData.objects.create(user=new_user)
        Result.objects.create(dashboard=dashboard)
        self.assertEqual(User.objects.all().count(), 1)
        self.assertEqual(User.objects.all()[0].email, self.email)
        self.assertEqual(HealthData.objects.all().count(), 1)
        self.assertEqual(Result.objects.all().count(), 1)

    def test_form_is_valid(self):
        data = {'email': self.email, 'password1': self.password, 'password2': self.password}
        form = CustomUserCreationForm(data=data)
        self.assertTrue(isinstance(form, CustomUserCreationForm))
        self.assertTrue(form.is_valid())

    def test_form_is_invalid(self):
        data = {'email': self.email, 'password1': self.password, 'password2': 'wrong'}
        form = CustomUserCreationForm(data=data)
        self.assertFalse(form.is_valid())

    def test_existing_username(self):
        """
        Тестирование процесса регистрации на выявление регистрации пользователя с уже зарегистрированным именем
        """
        new_user = User.objects.create_user(self.email, self.password)
        self.url = reverse('users:signup')
        self.resp = self.client.post(self.url, {'email': 'newuser@email.com', 'password1': 'django1234',
                                                'password2': 'django1234'})
        self.assertFormError(self.resp, 'user_form', 'email', 'User with this Email address already exists.')
        self.resp = self.client.post(self.url, {'email': 'NEWUSER@EMAIL.COM', 'password1': 'django1234',
                                                'password2': 'django1234'})
        self.assertFormError(self.resp, 'user_form', 'email', 'User with this Email address already exists.')

    def test_password_confirmation(self):
        """
        Тестирование процесса регистрации на совпадение и несовпадения пароля и проверки пароля
        """
        self.resp = self.client.post(self.url, {'email': 'new_user@email.mail', 'password1': 'pass1234',
                                                'password2': 'pass4321'})
        self.assertTemplateUsed(self.resp, 'registration/signup.html')
        self.resp = self.client.post(self.url, {'email': 'new_user@email.mail', 'password1': 'fahfgjdsjgu1234',
                                           'password2': 'fahfgjdsjgu1234'})
        self.assertTemplateUsed(self.resp, 'registration/signup_done.html')
        user = User.objects.get(email='new_user@email.mail')
        self.assertEqual(user.email, 'new_user@email.mail')

    def test_invalid_registration(self):
        """
        Тестирование процесса регистрации на выявление данных, не удовлетворяющих условиям валидности
        """
        self.resp = self.client.post(self.url, {'email': '_so !m!e .{em }ail@empo]23ail.mail34^',
                                           'password1': '', 'password2': ''})
        with self.assertRaises(ObjectDoesNotExist):
            User.objects.get(email='_so !m!e .{em }ail@empo]23ail.mail34^')
        self.assertFormError(self.resp, 'user_form', 'email',
                            ['Enter a valid email address.'])
        self.assertFormError(self.resp, 'user_form', 'password1',
            ['This field is required.'])
        self.assertFormError(self.resp, 'user_form', 'password2',
                            ['This field is required.'])
        self.resp = self.client.post(self.url, {'email': '',
                                                'password1': '1234', 'password2': '1234'})
        with self.assertRaises(ObjectDoesNotExist):
            User.objects.get(email='')
        self.assertFormError(self.resp, 'user_form', 'email',
                            ['This field is required.'])
        self.assertFormError(self.resp, 'user_form', 'password1',
            ['Ensure this value has at least 8 characters (it has 4).'])
        self.resp = self.client.post(self.url, {'email': 'new_user@email.mail',
                                                'password1': '01234567890123456789', 'password2': '01234567890123456789'})
        with self.assertRaises(ObjectDoesNotExist):
            User.objects.get(email='new_user@email.mail')
        self.assertFormError(self.resp, 'user_form', 'password1',
                             ['Ensure this value has at most 18 characters (it has 20).'])


class LoginTests(TestCase):
    def setUp(self):
        self.url = reverse('users:login')
        self.resp = self.client.get(self.url, follow=True)
        self.user = User.objects.create_user(email='test@test.ru', password='pass1234', email_confirm=True)
        self.user.username = self.user.email
        self.user.save()

    def test_correct_login(self):
        self.assertTrue(self.client.login(username='test@test.ru', password='pass1234'))
        self.client.logout()

    def test_wrong_username(self):
        self.assertFalse(self.client.login(username='wrong', password='pass1234'))

    def test_wrong_pssword(self):
        self.assertFalse(self.client.login(username='test@test.ru', password='wrong'))

    def test_login_template(self):
        self.assertEqual(self.resp.status_code, 200)
        self.assertTemplateUsed(self.resp, 'registration/login.html')
        self.assertContains(self.resp, 'Log in')
        self.assertNotContains(self.resp, 'Hi there! I should not be on the page.')

class ProfileTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='test@test.ru', password='pass1234', email_confirm=True)
        self.user.username = self.user.email
        self.user.first_name = 'Ivan'
        self.user.last_name = 'Ivanov'
        self.user.save()
        self.client.login(username='test@test.ru', password='pass1234')
        self.healht_data = baker.make(HealthData, user=CustomUser.objects.get(id=self.user.id))
        self.result = baker.make(Result, dashboard=self.healht_data)
        url = reverse('users:profile')
        self.resp = self.client.get(url)

    def test_correct_login(self):
        self.assertEqual(str(self.resp.context['user']), 'test@test.ru')
        self.assertEqual(self.resp.status_code, 200)
        self.assertIsInstance(self.resp.context['form'], ProfileForm)
        # self.client.logout()

    def test_clean_errors(self):
        url = reverse('users:profile')
        self.resp = self.client.post(url, {'email': '', 'first_name': '', 'last_name': '',
                                           'measuring_system': 2})
        self.assertEquals(self.resp.context['form'].errors.get('email')[0], 'This field is required.')
        self.assertEquals(self.resp.context['form'].errors.get('first_name')[0], 'Enter your name')
        self.assertEquals(self.resp.context['form'].errors.get('last_name')[0], 'Enter your last name')
        self.resp = self.client.post(url, {'email': 'test', 'first_name': 'I', 'last_name': 'A',
                                           'measuring_system': 2})
        self.assertEquals(self.resp.context['form'].errors.get('email')[0], 'Enter a valid email address.')
        self.assertEquals(self.resp.context['form'].errors.get('first_name'),
                                                                ['Ensure this value has at least 2 characters (it has 1).'])
        self.assertEquals(self.resp.context['form'].errors.get('last_name'),
                                                              ['Ensure this value has at least 2 characters (it has 1).'])
        regex = r'^[-a-zA-ZА-Яа-я]+\Z'
        self.assertNotRegex('111', regex)
        self.assertNotRegex('1a2s3s', regex)
        self.assertNotRegex('Ivanov-2', regex)
        self.assertRegex('Ivanov-Sidorov', regex)

    def test_profile_template(self):
        self.assertEqual(self.resp.status_code, 200)
        self.assertTemplateUsed(self.resp, 'profile.html')
        self.assertContains(self.resp, 'Profile')
        self.assertNotContains(self.resp, 'Hi there! I should not be on the page.')

    def test_profile(self):
        self.assertTrue(isinstance(self.user, CustomUser))
        self.assertEqual(self.user.__str__(), self.user.email)
        self.assertTrue(isinstance(self.healht_data, HealthData))

    def test_form_profile_is_valid(self):
        form = ProfileForm({'email': 'form@test.ru', 'first_name': self.user.first_name,
                            'last_name': self.user.last_name})
        self.assertTrue(isinstance(form, ProfileForm))
        self.assertTrue(form.is_valid())
        profile = form.save()
        self.assertEqual(profile.email, 'form@test.ru')
        self.assertEqual(profile.first_name, self.user.first_name)
        self.assertEqual(profile.last_name, self.user.last_name)

    def test_form_profile_blank_data(self):
        form = ProfileForm({})
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors,  {'email': ['This field is required.'],
                                        'first_name': ['Enter your name'],
                                        'last_name': ['Enter your last name']})

    def test_form_profile_is_invalid(self):
        data = {'email': 'wrong', 'first_name': '', 'last_name': self.user.last_name}
        form = ProfileForm(data=data)
        self.assertFalse(form.is_valid())

class HealhtDataTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='test@test.ru', password='pass1234', email_confirm=True)
        self.user.username = self.user.email
        self.user.save()
        self.healht_data = baker.make(HealthData, user=CustomUser.objects.get(id=self.user.id))
        baker.make(Result, dashboard=self.healht_data)
        self.client.login(username='test@test.ru', password='pass1234')

    def test_form_healht_data_is_valid(self):
        form = HealthDataForm({'birth_date': date(2006, 10, 23), 'measuring_system': 2, 'height': 7,
                               'country': 10, 'gender': 1, 'smoker': False},
                               instance=HealthData.objects.get(id=self.user.health_data.id))
        self.assertTrue(isinstance(form, HealthDataForm))
        self.assertTrue(form.is_valid())
        healht_data = form.save()
        self.assertEqual(healht_data.birth_date, date.fromisoformat('2006-10-23'))
        self.assertEqual(healht_data.height, 7)
        self.assertEqual(healht_data.measuring_system, 2)

    def test_feet_to_cm(self):
        self.assertEqual(feet_tu_cm(1.7), 50)
        self.assertEqual(feet_tu_cm(4.11), 150)
        self.assertEqual(feet_tu_cm(8.8), 260)

    def test_cm_to_feet(self):
        self.assertEqual(cm_to_feet(49), 1.8)
        self.assertEqual(cm_to_feet(261), 8.7)
        self.assertEqual(cm_to_feet(165), 5.5)

    def test_form_healht_data_blank_data(self):
        form = HealthDataForm({'measuring_system': 1})
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors,  {'birth_date': ['This field is required.'],
                                        'country': ['Choose a country Residence'],
                                        # 'gender': ['This field is required.'],
                                        'height': ['This field is required.',
                                                   'The value must be between 50 up to 260 cm']})

    def test_clean_errors(self):
        url = reverse('users:profile')
        self.resp = self.client.post(url, {'measuring_system': 2, 'height': 1.7})
        self.assertFormError(self.resp, 'form_data', 'height',
                             'The value must be between 1.8 up to 8.7 ft')
        self.resp = self.client.post(url, {'measuring_system': 2, 'height': 8.8})
        self.assertFormError(self.resp, 'form_data', 'height',
                             'The value must be between 1.8 up to 8.7 ft')
        self.resp = self.client.post(url, {'measuring_system': 1, 'height': 49})
        self.assertFormError(self.resp, 'form_data', 'height',
                             'The value must be between 50 up to 260 cm')

    def test_form_health_data_is_invalid(self):
        data = {'birth_date': '26.10.2006', 'measuring_system': 1,
                'country': 10, 'gender': 1, 'smoker': False}
        form = ProfileForm(data=data)
        self.assertFalse(form.is_valid())

class PasswordResetTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='test@test.ru', password='pass1234')
        self.user.username = self.user.email
        self.user.save()

    def test_password_reset(self):
        url = reverse('users:password_reset')
        self.resp = self.client.get(url)
        self.assertEqual(self.resp.status_code, 200)
        self.assertTemplateUsed(self.resp, 'registration/password_reset_form.html')
        self.assertContains(self.resp, 'Password reset')
        self.assertNotContains(self.resp, 'Hi there! I should not be on the page.')

    def test_user_exists(self):
        url = reverse('users:password_reset')
        self.resp = self.client.post(url, data={'email': 'test@test.ru'}, follow=True)
        self.assertRedirects(self.resp, '/en/account/password_reset/done/')
        self.assertTemplateUsed(self.resp, 'registration/email_sent.html')
        user = User.objects.filter(email__iexact='test@test.ru').exists()
        self.assertTrue(user)

    def test_user_not_exists(self):
        url = reverse('users:password_reset')
        self.resp = self.client.post(url, data={'email': 'user@test.ru'}, follow=True)
        self.assertEqual(self.resp.status_code, 200)
        self.assertTemplateUsed(self.resp, 'registration/password_reset_form.html')
        message = list(self.resp.context.get('messages'))[0]
        self.assertEqual(message.tags, 'alert-danger')
        self.assertTrue(f"User with email user@test.ru doesn\'t exists." in message.message)
        self.assertContains(self.resp, 'User with email')
        user = User.objects.filter(email__iexact='user@test.ru').exists()
        self.assertFalse(user)

    def test_password_reset_done(self):
        url = reverse('users:password_reset_done')
        self.resp = self.client.get(url)
        self.assertEqual(self.resp.status_code, 200)
        self.assertTemplateUsed(self.resp, 'registration/email_sent.html')
        self.assertContains(self.resp, 'We have sent you an e-mail.')
        self.assertNotContains(self.resp, 'Hi there! I should not be on the page.')

class EmailTest(TestCase):
    def test_send_email(self):
        with self.settings(EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'):
            mail.send_mail('Subject here', 'Here is the message.',
                'from@example.com', ['to@example.com'],
                fail_silently=False)
            self.assertEqual(len(mail.outbox), 1)
            self.assertEqual(mail.outbox[0].subject, 'Subject here')













# class UserViewTest(WebTest):
#
#     def test_view_page(self):
#         page=self.app.get(reverse('users:profile'))
#         self.assertEqual(len(page.forms), 1)
#
#     def test_form_error(self):
#         page = self.app.get(reverse('users:profile')).form
#         page = page.form.submit().follow()
#         self.assertContains(page, "This field is required.")
#
#     def test_form_success(self):
#         page = self.app.get(reverse('users:profile')).form
#         page.form['email'] = 'test@test.ru'
#         page.form['first_name'] = 'Ivan'
#         page.form['last_name'] = 'Ivanov'
#         page = page.form.submit().follow()
#         self.assertEqual(resp.context['user'].username, 'test@test.ru')
#         self.assertRedirects(page, reverse('users:profile'))
