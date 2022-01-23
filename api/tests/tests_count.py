from django.test import TestCase
from unittest.mock import Mock

from api.count import CountUserInfo


class CountTests(TestCase):
    def setUp(self):
        self.birth_date = '10.03.1964'
        self.growth = 150
        self.age = 40
        self.waist = 100
        self.hip = 30
        self.gender_1 = 1
        self.neck = 40
        self.weight = 80
        self.daily_activity_level = 1.55
        self.wrist = 19
        self.gender = 1
        self.blood_pressure_sistolic = 150
        self.total_cholesterol = 5
        self.blood_glucose_level = 5
        self.smoking = True

    def test_user_age(self):
        self.assertEqual(CountUserInfo.user_age(self), 57)
        self.assertNotEqual(CountUserInfo.user_age(self), 81)

    def test_fat_percent(self):
        self.assertEqual(CountUserInfo.fat_percent(self), 31)
        self.assertNotEqual(CountUserInfo.fat_percent(self), 29)
        self.gender_1 = 2
        self.assertEqual(CountUserInfo.fat_percent(self), 3)
        self.assertNotEqual(CountUserInfo.fat_percent(self), 9)

    def test_fat_percent_category(self):
        self.fat_percent = Mock(return_value=23)
        self.assertEqual(CountUserInfo.fat_percent_category(self), 2)
        self.assertNotEqual(CountUserInfo.fat_percent_category(self), 3)
        self.gender_1 = 1
        self.fat_percent = Mock(return_value=25)
        self.assertEqual(CountUserInfo.fat_percent_category(self), 3)
        self.assertNotEqual(CountUserInfo.fat_percent_category(self), 2)

    def test_bmi(self):
        self.growth = 170
        self.weight = 150
        self.fat_percent_category = Mock(return_value=4)
        self.assertEqual(CountUserInfo.bmi(self), 51.9)
        self.growth = 170
        self.weight = 100
        self.fat_percent_category = Mock(return_value=3)
        self.assertEqual(CountUserInfo.bmi(self), 34.6)
        self.growth = 170
        self.weight = 70
        self.fat_percent_category = Mock(return_value=2)
        self.assertEqual(CountUserInfo.bmi(self), 24.2)

    def test_obesity_level(self):
        self.bmi = Mock(return_value=18)
        self.assertEqual(CountUserInfo.obesity_level(self),
                         {'ru': 'Пониженный вес', 'en': 'Underweight'})
        self.bmi = Mock(return_value=33)
        self.assertEqual(CountUserInfo.obesity_level(self),
                         {'ru': 'Ожирение 1 ст.', 'en': 'Moderatelyover weight(Obese Class I)'})
        self.bmi = Mock(return_value=60)
        self.assertEqual(CountUserInfo.obesity_level(self),
                         {'ru': 'Ожирение 3 ст.', 'en': 'Morbidly Obese(Class III)'})

    def test_ideal_weight(self):
        # wrist < 15
        self.wrist = 14
        self.assertEqual(CountUserInfo.ideal_weight(self), 47)
        # 15 <= wrist <= 17
        self.wrist = 16
        self.assertEqual(CountUserInfo.ideal_weight(self), 49.5)
        # 17 < wrist
        self.wrist = 20
        self.assertEqual(CountUserInfo.ideal_weight(self), 52)
        #wrong
        self.growth = 170
        self.wrist = 25
        self.age = 350
        self.assertNotEqual(CountUserInfo.ideal_weight(self), 100)

    def test_calory_day(self):
        self.assertEqual(CountUserInfo.calory_day(self), 2391)
        self.assertNotEqual(CountUserInfo.calory_day(self), 2542)
        self.gender_1 = 2
        self.assertEqual(CountUserInfo.calory_day(self), 2134)
        self.assertNotEqual(CountUserInfo.calory_day(self), 2068)

    def test_calorie_surplus(self):
        self.calory_day = Mock(return_value=2569)
        self.bmi = Mock(return_value=35)
        self.assertEquals(CountUserInfo.calorie_surplus(self), 3211)
        self.bmi = Mock(return_value=24)
        self.assertEquals(CountUserInfo.calorie_surplus(self), 2954)
        self.assertNotEquals(CountUserInfo.calorie_surplus(self), 3211)

    def test_calorie_deficiency(self):
        self.calory_day = Mock(return_value=3861)
        self.bmi = Mock(return_value=35)
        self.assertEquals(CountUserInfo.calorie_surplus(self), 4826)
        self.bmi = Mock(return_value=24)
        self.assertEquals(CountUserInfo.calorie_surplus(self), 4440)
        self.assertNotEquals(CountUserInfo.calorie_surplus(self), 3211)

    def test_calory_to_low_weight(self):
        self.calory_day = Mock(return_value=3167)
        self.assertEqual(CountUserInfo.calory_day(self), 2391)
        self.assertNotEqual(CountUserInfo.calory_day(self), 2539)

    def test_body_type(self):
        self.assertEqual(CountUserInfo.body_type(self), {'ru': 'Мезоморфный', 'en': 'Mesomorphic'})
        self.gender_1 = 2
        self.assertEqual(CountUserInfo.body_type(self), {'ru': 'Эндоморфный', 'en': 'Endomorphic'})
        self.gender_1 = None
        self.assertEqual(CountUserInfo.body_type(self), '')

    def test_hip_to_waist_index(self):
        self.assertEqual(CountUserInfo.hip_to_waist_index(self), 3.333)
        self.assertNotEqual(CountUserInfo.hip_to_waist_index(self), 4)

    def test_hip_to_waist_description(self):
        self.hip_to_waist_index = Mock(return_value=0.88)
        self.assertEqual(CountUserInfo.hip_to_waist_description(self), {'ru': 'Норма', 'en': 'Normal index'})
        self.gender = 0
        self.assertEqual(CountUserInfo.hip_to_waist_description(self), {'ru': 'Ожирение', 'en': 'Obesity'})
        self.assertNotEqual(CountUserInfo.hip_to_waist_description(self), {'ru': 'Норма', 'en': 'Normal index'})

    def test_cancer_risks_bmi(self):
        self.bmi = Mock(return_value=23)
        self.assertEqual(CountUserInfo.cancer_risks_bmi(self),  [{
                'icd_id': None,
                'risk_string': 'low',
                'risk_percents': None,
                'message': {'ru': 'У Вас низкий шанс развития онкологических заболеваний.', 'en': 'You have a low chance of developing cancer'},
                'recomendation': {'ru': None, 'en': None}
            }])
        self.bmi = Mock(return_value=34)
        self.assertNotEqual(CountUserInfo.cancer_risks_bmi(self), [{
            'icd_id': None,
            'risk_string': 'low',
            'risk_percents': None,
            'message': {'ru': 'У Вас низкий шанс развития онкологических заболеваний.',
                        'en': 'You have a low chance of developing cancer'},
            'recomendation': {'ru': None, 'en': None}
        }])

    def test_diabetes_risk_bmi(self):
        self.bmi = Mock(return_value=26)
        diabetes_risk = 2
        self.assertEqual(CountUserInfo.diabetes_risk_bmi(self), [{
                'icd_id': None,
                'risk_string':  'High',
                'risk_percents': None,
                'message': {'ru': 'Ожирение увеличивает риск развития диабета 2 типа в ' + str(diabetes_risk) + ' раз(а).',
                            'en': 'Obesity increases diabetes risk by ' + str(diabetes_risk) + ' times.'},
                'recomendation': {'ru': 'Снижение веса позволит снизить риск развития раковых заболеваний и улучшить контроль за уровнем сахара в крови.',
                                  'en': 'Lowering weight will reduce your risk of developing cancer and improve your blood sugar control.'}
            }])
        self.bmi = Mock(return_value=35)
        self.assertNotEqual(CountUserInfo.diabetes_risk_bmi(self), [{
            'icd_id': None,
            'risk_string': 'High',
            'risk_percents': None,
            'message': {'ru': 'Ожирение увеличивает риск развития диабета 2 типа в ' + str(diabetes_risk) + ' раз(а).',
                        'en': 'Obesity increases diabetes risk by ' + str(diabetes_risk) + ' times.'},
            'recomendation': {
                'ru': 'Снижение веса позволит снизить риск развития раковых заболеваний и улучшить контроль за уровнем сахара в крови.',
                'en': 'Lowering weight will reduce your risk of developing cancer and improve your blood sugar control.'}
        }])

    def test_stroke_risk_bmi(self):
        self.bmi = Mock(return_value=28)
        stroke_risk = 1.7
        self.assertNotEqual(CountUserInfo.stroke_risk_bmi(self), [{
                'icd_id': None,
                'risk_string':  'High',
                'risk_percents': None,
                'message': {'ru': 'Ожирение повышает риск развития инсульта в ' + str(stroke_risk) + ' раз.',
                            'en': 'Obesity increases stroke risk by ' + str(stroke_risk) + ' times.'},
                'recomendation': {'ru': 'Снижение веса позволит снизить риск инсульта.',
                                  'en': 'Lowering weight will reduce your risk of stroke.'}
            }])
        self.bmi = Mock(return_value=38)
        self.assertEqual(CountUserInfo.stroke_risk_bmi(self), [{
                'icd_id': None,
                'risk_string':  'High',
                'risk_percents': None,
                'message': {'ru': 'Ожирение повышает риск развития инсульта в ' + str(stroke_risk) + ' раз.',
                            'en': 'Obesity increases stroke risk by ' + str(stroke_risk) + ' times.'},
                'recomendation': {'ru': 'Снижение веса позволит снизить риск инсульта.',
                                  'en': 'Lowering weight will reduce your risk of stroke.'}
            }])

    def test_score_description(self):
        self.score_risk = Mock(return_value=7)
        score = 7
        risk_string = 'High'
        recomendation = {'ru': 'Данный индекс зависит от уровня холестерина в крови, артериального давления и курения. Приведение целевых показателей в норму позволит снизить риск развития сердечно-сосудистых заболеваний.',
                             'en': 'This index depend on cholesterol level, arterial pressure and smoking. Bringing target values back to normal will reduce the risk of cardiovascular diseases.'}
        self.assertEqual(CountUserInfo.score_description(self), [{
                    'icd_id': None,
                    'risk_string': risk_string,
                    'risk_percents': str(score) + ' %',
                    'message': {'ru': 'Вероятность серьезных последствий связанных с сердечно-сосудистыми заболеваниями в ближайшие 10 лет ',
                                'en': 'The probability of serious consequences associated with cardiovascular diseases in the next 10 years '},
                    'recomendation': recomendation
                }])
        self.score_risk = Mock(return_value=0)
        score = 0
        risk_string = 'low'
        self.assertEqual(CountUserInfo.score_description(self), [{
                    'icd_id': None,
                    'risk_string': risk_string,
                    'risk_percents': None,
                    'message': {
                        'ru': 'В ближайшие 10 лет у вас низкий риск развития серьезных последствий, связанных с сердечно-сосудистыми заболеваниями.',
                        'en': 'You have a low risk of developing serious consequences associated with cardiovascular diseases in the next 10 years.'},
                    'recomendation': {'ru': None, 'en': None}
                }])

    def test_recomendations(self):
        self.bmi = Mock(return_value=34)
        self.fat_percent_category = Mock(return_value=3)
        self.calory_day = Mock(return_value=2687)
        self.calorie_surplus = Mock(return_value=2768)
        self.calorie_deficiency = Mock(return_value=2546)
        self.obesity_level = Mock(return_value={'ru': 'Ожирение 1 ст.', 'en': 'Moderatelyover weight(Obese Class I)'})
        calory_day = 2687
        calorie_surplus = 2768
        calorie_deficiency = 2546
        obesity_level = {'ru': 'Ожирение 1 ст.', 'en': 'Moderatelyover weight(Obese Class I)'}

        self.assertEqual(CountUserInfo.recomendations(self), [{'message_short': {'ru': 'Старайтесь проходить за день более 8000 шагов.',
                                                                              'en': 'Walk more than 8000 steps per day.'},
                                                            'message_long': {'ru': 'Достаточный уровень активности позволит чувствовать себя лучше, снизить вес и снизить риски развития заболеваний.',
                                                                             'en': 'Getting enough activity will help you feel better, lose weight, and reduce your risk of diseases.'},
                                                            'importance_level': 'Without color'}, {'message_short': {'ru': '{}'.format(obesity_level['ru']), 'en': '{}'.format(obesity_level['en'])},
                    'message_long': {'ru': 'Количество потребляемых килокалорий для поддержания текущего веса: {} кКал. Для уменьшения веса: {} кКал. Соблюдайте соотношение белков, жиров и углеводов в рационе: 50/30/20%.'.format(
                           calory_day, calorie_deficiency),
                        'en': 'The number of calories consumed to maintain current weight: {} kcal. To reduce weight: {} kcal. Maintain the ratio of protein, fat, and carbohydrates in the diet: 50/30/20%.'.format(
                           calory_day, calorie_deficiency)},
                    'importance_level': 'Without color'},  {'message_short': {'ru': 'Постарайтесь снизить свой вес.', 'en': 'Low your weight.'}, 'message_long': {'ru': 'Индекс массы тела должен быть от 18.5 до 24.9.',
                                                                                                                                                                  'en': 'Body mass index should be from 18.5 to 24.9.'}, 'importance_level': 'High'},
                                                           {'message_short': {'ru': 'Откажитесь от курения или снизьте число выкуриваемых в день сигарет.', 'en': 'Stop smoking or decrease cigarette count per day.'}, 'message_long':
                                                               {'ru': 'Курение способно спровоцировать развитие онкологических заболеваний, повысить риск легочных и сердечно-сосудистых заболеваний.', 'en': 'Smoking can provoke the development of cancer, increase the risk of lung and cardiovascular diseases.'}, 'importance_level': 'High'}])

