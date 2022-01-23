import json
from api.serializers import User
from model_bakery import baker
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from users.models import CustomUser
from api.count import CountUserInfo

from cms.models import Result, HealthData, DiseaseRisk, CommonRecomendations

#!!!!!!!!!!!!!!!!!!!! cut here !!!!!!!!
#import logging
#logger = logging.getLogger('django')
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

User = get_user_model()

class ResultWithHints(TestCase):
 
    def setUp(self) -> None:
        self.user = User.objects.create_user(email='test@test.ru', password='qwerty', email_confirm=True)
        self.client.login(username='test@test.ru', password='qwerty')
        self.healht_data = baker.make(HealthData, user=self.user)
        self.result = baker.make(Result, dashboard=self.healht_data, 
            bmi = 25,
            obesity_level = {'ru': 'Избыточный вес', 'en': 'Overweight'},
            body_type = {'ru': 'Эктоморфный', 'en':'Ectomorphic'},
            ideal_weight = 70,
            #fat_percent='49 %, 3',
            fat_percent='49',
            fat_category= 3
            )
        baker.make(DiseaseRisk, result= self.result)
        baker.make(CommonRecomendations, result= self.result)


    def test_hints(self):
        self.url = reverse('v2:result')
        self.resp = self.client.get(self.url)

        self.data = json.loads(self.resp.content)
        self.assertEqual(self.resp.status_code, 200)

        self.assertEqual(self.data['fat_percent'], ["49 %","#FF1744"])
        

    def test_data_hints(self):
        self.url = reverse('v2:resultdata')
        self.resp = self.client.get(self.url)
        self.assertEqual(self.resp.status_code, 200)

        self.data = json.loads(self.resp.content)
        params = self.data['params']
        for obj in params:
            if obj['name'] == 'fat_percent':
                self.assertEqual(obj['value'], 49)
                self.assertEqual(obj['color'], '#FF1744')        

