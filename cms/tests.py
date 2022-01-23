from model_bakery import baker
from unittest.mock import Mock

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from users.models import CustomUser
from .models import Result, HealthData

User = get_user_model()


class DashboardTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@test.ru', password='pass1234', email_confirm=True)
        self.client.login(username='test@test.ru', password='pass1234')
        self.healht_data = baker.make(
            HealthData, user=CustomUser.objects.get(id=self.user.id))
        self.parameters = baker.make(
            Result, dashboard=self.healht_data, fat_percent=49, bmi=20)
        self.url = reverse('cms:dashboard')
        self.resp = self.client.get(self.url)

    def test_parameters_template(self):
        self.assertEqual(self.resp.status_code, 200)
        self.assertTemplateUsed(self.resp, 'cms/dashboard.html')
        self.assertContains(self.resp, 'form')
        # self.assertContains(self.resp, 'measuring_system')


class ResultTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='test@test.ru', password='pass1234', email_confirm=True)
        self.client.login(username='test@test.ru', password='pass1234')
        self.healht_data = baker.make(
            HealthData, user=CustomUser.objects.get(id=self.user.id))
        self.parameters = baker.make(
            Result, dashboard=self.healht_data, fat_percent=49, bmi=20)
        self.url = reverse('cms:result')
        self.resp = self.client.get(self.url)

    def test_parameters_template(self):
        self.assertEqual(self.resp.status_code, 200)
        self.assertTemplateUsed(self.resp, 'cms/result.html')
        # self.assertContains(self.resp, 'risks')
        # self.assertContains(self.resp, 'recomendations')


class ParametersTests(TestCase):
    def setUp(self):
        self.user  = User.objects.create_user(email='test@test.ru', password='pass1234', email_confirm=True)
        self.client.login(username='test@test.ru', password='pass1234')
        self.healht_data = baker.make(HealthData, user=CustomUser.objects.get(id=self.user.id))
        self.parameters = baker.make(
            Result, dashboard=self.healht_data, fat_percent=49, bmi=20, body_type='{"en": "Ectomorphic"}'
        )
        self.url = reverse('cms:parameters')
        self.resp = self.client.get(self.url)

    def test_parameters_template(self):
        self.assertEqual(self.resp.status_code, 200)
        self.assertTemplateUsed(self.resp, 'cms/parameters.html')
        self.assertContains(self.resp, 'Parameters')

    def test_parameters_data(self):
        Result.objects.update(obesity_level='Morbidly Obese(Class III)')
        result = Result.objects.get(id=1)
        expected_object_name = f'{result.obesity_level}'
        self.assertEqual(expected_object_name, 'Morbidly Obese(Class III)')
        self.resp = self.client.get(self.url)
        self.assertContains(self.resp, 'Morbidly Obese(Class III)')
        verbose_name = Result._meta.get_field('waist_to_hip_proportion').verbose_name
        self.assertEqual(verbose_name, 'Waist-hip ratio')




