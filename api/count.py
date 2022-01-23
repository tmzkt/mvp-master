from flask import jsonify
import json
import re
import datetime
import numpy as np
from datetime import datetime, timedelta
from datetime import date
from cms.models import HealthData
import logging
from api.CVD_core_production import cvd_value, data_preparation, diabet_value, get_stroke_value

logger = logging.getLogger('django')

_default_locale = "en"
_default_gender = 0

errors_strings = {
    "en":
        {
           "unauthorized": "ERROR: Unauthorized.",
           "no_user_id": "ERROR: User id not provided.",
           "unfilled": "ERROR: Some data has not been filled!"
        },
    "ru":
        {
            "unauthorized": "ОШИБКА: Неавторизованный пользователь.",
            "no_user_id": "ОШИБКА: Не указан id пользователя.",
            "unfilled": "ОШИБКА: Не все поля были заполнены!"
        }
}

params_names = {
    "en":
        {
            "wrist": "wrist",
            "height": "height",
            "birth_date": "date of birth",
            "weight": "weight",
            "waist": "waist measurement",
            "hip": "hip measurement",
            "neck": "neck measurement",
            "cholesterol": "cholesterol level",
            "glucose": "glucose level",
            "blood_pressure_sys": "blood pressure systolic",
            "blood_pressure_dia": "blood pressure diastolic",
            "heart_rate_alone": "heart_rate_alone",
            "gender": "gender",
            "smoker": "smoking habits",
            "daily_activity_level": "daily_activity_level"
        },
    "ru":
        {
            "wrist": "запястье",
            "height": "рост",
            "birth_date": "дата рождения",
            "weight": "вес",
            "waist": "замеры талии",
            "hip": "замеры бедра",
            "neck": "замеры шеи",
            "cholesterol": "уровень холестерина",
            "glucose": "уровень глюкозы",
            "blood_pressure_sys": "кровяное давление систолическое",
            "blood_pressure_dia": "кровяное давление диастолическое",
            "heart_rate_alone": "сердечный ритм",
            "gender": "пол",
            "smoker": "привычки в курении",
            "daily_activity_level": "коэфициент дневной активности"
        }
}


def unfilled_data_error(locale, user_id):
    data = HealthData.objects.filter(user=user_id).values().first()
    unfilled_params = []
    mandatory_params = ['gender', 'birth_date', 'height', 'weight', 'hip', 'waist', 'wrist',
                        'smoker', 'neck', 'daily_activity_level', 'measuring_system']

    if not all([data[param] for param in mandatory_params]):
        for param in mandatory_params:
            if not data[param]:
                unfilled_params.append(param)

    return {"user_id": user_id, "user_calc_data": {"disease_risk": [], "common_recomendations": [],
            "unfilled": errors_strings[locale]["unfilled"] + "\n" + str([params_names[locale].get(param)
                                                                         for param in unfilled_params])}}


def count_risk(data):
    # try:
    #     user_id = int(data["user_id"])
    # except Exception as e:
    #     return f"Incorrect user_id parameter! Should be int.\n{e}\n{data}"
    user_risks = CountUserInfo(data).make_json()
    return user_risks


class CountUserInfo:
    def __init__(self, data):
        self.id = data['user_id']
        self.growth = data['height']
        self.weight = data['weight']
        self.birth_date = data['birth_date']
        self.age = self.user_age()
        self.gender = data['gender']
        if self.gender > 1:
            self.gender = _default_gender
        self.gender_1 = data['gender']
        self.wrist = data['wrist']
        self.hip = data['hip']
        self.waist = data['waist']
        self.neck = data['neck']
        self.heart_rate_alone = data.get('heart_rate_alone')
        self.blood_pressure_sistolic = data.get('blood_pressure_sys')
        self.blood_pressure_diastolic = data.get('blood_pressure_dia')
        self.total_cholesterol = data.get('cholesterol')
        self.blood_glucose_level = data.get('glucose')
        self.smoking = int(data.get('smoker', False))
        self.daily_activity_level = data['daily_activity_level']
        self.bmi_value = 0

    def make_json(self):
        disease_risk = []
        disease_risk += self.score_description()
        disease_risk += self.diabetes_risk_bmi()
        disease_risk += self.stroke_risk_bmi()
        disease_risk += self.cancer_risks_bmi()
        recomendations = []
        recomendations += self.recomendations()
        self.bmi_value = self.bmi()
        json_dict = {
            'user_id': self.id,
            'user_calc_data': {
                'bmi': self.bmi_value,
                'obesity_level': self.obesity_level(),
                'ideal_weight': self.ideal_weight(),
                'base_metabolism': self.calory_day(),
                'calories_to_low_weihgt': self.calory_to_low_weight(),
                'waist_to_hip_proportion': self.hip_to_waist_index(),
                'passport_age': self.age,
                'common_risk_level': self.common_risk_level(),
                'prognostic_age': None,
                'fat_percent': self.fat_percent(),
                'fat_category': self.fat_percent_category(),
                'body_type': self.body_type(),
                'unfilled': None,
                'disease_risk': disease_risk,
                'common_recomendations': recomendations,
                'CVD': self.cvd_calculate(),
                'diabetes': self.diabet_predict(),
                'stroke': self.stroke_predict(),
            }
        }
        # ready_json = json.dumps(json_dict, ensure_ascii=False)
        return json_dict

    def diabet_predict(self):
        logger.info('Diabetes calculate beginning')
        # Input: Glucose (mg/dL), blood_pressure_dia, BMI, Age
        return diabet_value(self.blood_glucose_level * 18,
                            self.blood_pressure_diastolic,
                            self.bmi_value,
                            self.age,
                            )
                            
    def stroke_predict(self):
        logger.info('Stroke calculate beginning')
        # Input: Age, Glucose (mg/dL), BMI, blood_pressure_sistolic, blood_pressure_diastolic
        return get_stroke_value(self.age,
                            self.blood_glucose_level * 18,
                            self.bmi_value,
                            self.blood_pressure_sistolic,
                            self.blood_pressure_diastolic
                            )

    def cvd_calculate(self):
        logger.info('CVD calculate beginning')
        return cvd_value(self.age,
                         self.growth,
                         self.blood_pressure_sistolic,
                         self.blood_pressure_diastolic,
                         data_preparation(self.gender, self.total_cholesterol * 18)
                         )

    def common_risk_level(self):
        common_risk_level = {'ru': 'средний', 'en': 'medium'}
        return common_risk_level

    def user_age(self):
        today = date.today()
        # See "DATE_FORMAT" in base.py
        born = datetime.strptime(self.birth_date, '%d.%m.%Y')
        return today.year - born.year - ((today.month, today.day) < (born.month, born.day))

    def fat_percent(self):
        gender = self.gender_1
        waist = self.waist
        neck = self.neck
        growth = self.growth
        hip = self.hip
        try:
            if gender == 1:
                fat_percent = 495/(1.0324 - 0.19077 * np.log10(waist - neck) + 0.15456 * np.log10(growth)) - 450
            elif gender == 2:
                fat_percent = 495/(1.29579 - 0.35004 * np.log10(waist + hip - neck) + 0.22100 * np.log10(growth)) - 450
            fat_percent = 0 if fat_percent < 0 else round(fat_percent)
        except:
            fat_percent = 0
        return fat_percent

    def fat_percent_category(self):
        """
           fat_cat =
           1 - Низкий уровень
           2 - Оптималный уровень
           3 - Высокий уровень
           4 - Ожирение
        """
        fat_percent = self.fat_percent()
        gender = self.gender_1
        age = self.age
        fat_cat = 0

        # [gender, age_group, fat_percent_group]
        age_group = {
            age < 30: 0,
            30 <= age < 40: 1,
            40 <= age < 50: 2,
            50 <= age < 60: 3,
            60 <= age: 4
            }[True]
        
        #print(gender,age_group,fat_percent)

        # fat_cat = {
        #     (gender == 1 and age_group == 1 and 20 < fat_percent) or
        #     (gender == 1 and age_group == 2 and 21 < fat_percent) or
        #     (gender == 1 and age_group == 3 and 22 < fat_percent) or
        #     (gender == 1 and age_group == 4 and 23 < fat_percent) or
        #     (gender == 1 and age_group == 5 and 24 < fat_percent) or
        #     (gender == 2 and age_group == 1 and 14 < fat_percent) or
        #     (gender == 2 and age_group == 2 and 15 < fat_percent) or
        #     (gender == 2 and age_group == 3 and 17 < fat_percent) or
        #     (gender == 2 and age_group == 4 and 18 < fat_percent) or
        #     (gender == 2 and age_group == 5 and 19 < fat_percent): 1,

        #     (gender == 1 and age_group == 1 and 13 < fat_percent < 21) or
        #     (gender == 1 and age_group == 2 and 14 < fat_percent < 22) or
        #     (gender == 1 and age_group == 3 and 16 < fat_percent < 24) or
        #     (gender == 1 and age_group == 4 and 17 < fat_percent < 25) or
        #     (gender == 1 and age_group == 5 and 18 < fat_percent < 26) or
        #     (gender == 2 and age_group == 1 and 19 < fat_percent < 29) or
        #     (gender == 2 and age_group == 2 and 20 < fat_percent < 30) or
        #     (gender == 2 and age_group == 3 and 21 < fat_percent < 31) or
        #     (gender == 2 and age_group == 4 and 22 < fat_percent < 32) or
        #     (gender == 2 and age_group == 5 and 23 < fat_percent < 33): 2,

        #     (gender == 1 and age_group == 1 and 20 < fat_percent < 24) or
        #     (gender == 1 and age_group == 2 and 21 < fat_percent < 25) or
        #     (gender == 1 and age_group == 3 and 23 < fat_percent < 27) or
        #     (gender == 1 and age_group == 4 and 23 < fat_percent < 28) or
        #     (gender == 1 and age_group == 5 and 25 < fat_percent < 29) or
        #     (gender == 2 and age_group == 1 and 28 < fat_percent < 32) or
        #     (gender == 2 and age_group == 2 and 29 < fat_percent < 33) or
        #     (gender == 2 and age_group == 3 and 30 < fat_percent < 34) or
        #     (gender == 2 and age_group == 4 and 31 < fat_percent < 34) or
        #     (gender == 2 and age_group == 5 and 32 < fat_percent < 36): 3,

        #     (gender == 1 and age_group == 1 and 23 < fat_percent) or
        #     (gender == 1 and age_group == 2 and 24 < fat_percent) or
        #     (gender == 1 and age_group == 3 and 26 < fat_percent) or
        #     (gender == 1 and age_group == 4 and 27 < fat_percent) or
        #     (gender == 1 and age_group == 5 and 28 < fat_percent) or
        #     (gender == 2 and age_group == 1 and 31 < fat_percent) or
        #     (gender == 2 and age_group == 2 and 32 < fat_percent) or
        #     (gender == 2 and age_group == 3 and 33 < fat_percent) or
        #     (gender == 2 and age_group == 4 and 33 < fat_percent) or
        #     (gender == 2 and age_group == 5 and 35 < fat_percent): 4,

        # }[True]

        if gender == 1:
            if (age < 30 and fat_percent < 11) or (30 <= age <= 39 and fat_percent < 12) or \
                (40 <= age <= 49 and fat_percent < 14) or (50 <= age <= 59 and fat_percent < 15) or \
                (age >= 60 and fat_percent < 16):
                fat_cat = 0
            elif (age < 30 and 11 <= fat_percent <= 13) or (30 <= age <= 39 and 12 <= fat_percent <= 14) or \
                  (40 <= age <= 49 and 14 <= fat_percent <= 16) or (50 <= age <= 59 and 15 <= fat_percent <= 17) or \
                  (age >= 60 and 16 <= fat_percent <= 18):
                fat_cat = 1
            elif (age < 30 and 14 <= fat_percent <= 20) or (30 <= age <= 39 and 15 <= fat_percent <= 21) or \
                  (40 <= age <= 49 and 17 <= fat_percent <= 23) or (50 <= age <= 59 and 18 <= fat_percent <= 24) or \
                  (age >= 60 and 19 <= fat_percent <= 25):
                fat_cat = 2
            elif (age < 30 and 21 <= fat_percent <= 23) or (30 <= age <= 39 and 22 <= fat_percent <= 24) or \
                  (40 <= age <= 49 and 24 <= fat_percent <= 26) or (50 <= age <= 59 and 25 <= fat_percent <= 27) or \
                  (age >= 60 and 26 <= fat_percent <= 28):
                fat_cat = 3
            elif (age < 30 and fat_percent >= 24) or (30 <= age <= 39 and fat_percent >= 25) or \
                  (40 <= age <= 49 and fat_percent >= 27) or (50 <= age <= 59 and fat_percent >= 28) or \
                  (age >= 60 and fat_percent >= 29):
                fat_cat = 4
        elif gender == 2:
            if (age < 30 and fat_percent < 16) or (30 <= age <= 39 and fat_percent < 17) or \
                    (40 <= age <= 49 and fat_percent < 18) or (50 <= age <= 59 and fat_percent < 19) or \
                    (age >= 60 and fat_percent < 20):
                fat_cat = 0
            elif (age < 30 and 16 <= fat_percent <= 19) or (30 <= age <= 39 and 17 <= fat_percent <= 20) or \
                    (40 <= age <= 49 and 18 <= fat_percent <= 21) or (50 <= age <= 59 and 19 <= fat_percent <= 22) or \
                    (age >= 60 and 20 <= fat_percent <= 23):
                fat_cat = 1
            elif (age < 30 and 20 <= fat_percent <= 28) or (30 <= age <= 39 and 21 <= fat_percent <= 29) or \
                    (40 <= age <= 49 and 22 <= fat_percent <= 30) or (50 <= age <= 59 and 23 <= fat_percent <= 31) or \
                    (age >= 60 and 24 <= fat_percent <= 32):
                fat_cat = 2
            elif (age < 30 and 29 <= fat_percent <= 31) or (30 <= age <= 39 and 30 <= fat_percent <= 32) or \
                    (40 <= age <= 49 and 31 <= fat_percent <= 33) or (50 <= age <= 59 and 32 <= fat_percent <= 33) or \
                    (age >= 60 and 33 <= fat_percent <= 35):
                fat_cat = 3
            elif (age < 30 and fat_percent >= 32) or (30 <= age <= 39 and fat_percent >= 33) or \
                    (40 <= age <= 49 and fat_percent >= 34) or (50 <= age <= 59 and fat_percent >= 34) or \
                    (age >= 60 and fat_percent >= 36):
                fat_cat = 4
        return fat_cat

    def bmi(self):
        fat_cat = self.fat_percent_category()
        growth = float(self.growth) / 100
        bmi = round((self.weight / growth**2), 1)
        # if fat_cat <= 1:
        #     bmi = bmi if bmi < 18.5 else 18
        # elif fat_cat == 2:
        #     if bmi <= 18.5:
        #         bmi = 18.5
        #     elif bmi > 25:
        #         bmi = 24.9
        #     else:
        #         bmi = bmi
        # elif fat_cat == 3:
        #     if bmi <= 25:
        #         bmi = 25
        #     else:
        #         bmi = bmi
        # elif fat_cat == 4:
        #     if bmi <= 30:
        #         bmi = 30
        #     else:
        #         bmi = bmi
        return bmi

    def obesity_level(self):
        bmi = self.bmi()
        bmi_description = {
            bmi < 18.5: {'ru': 'Пониженный вес', 'en': 'Underweight'},
            18.5 <= bmi < 25: {'ru': 'Вес в норме', 'en': 'Normal weight'},
            25 <= bmi < 30: {'ru': 'Избыточный вес', 'en': 'Overweight'},
            30 <= bmi < 35: {'ru': 'Ожирение 1 ст.', 'en': 'Moderatelyover weight(Obese Class I)'},
            35 <= bmi < 40: {'ru': 'Ожирение 2 ст.', 'en': 'Severely Obese(Class II)'},
            40 <= bmi: {'ru': 'Ожирение 3 ст.', 'en': 'Morbidly Obese(Class III)'}
        }[True]

        return bmi_description

    def ideal_weight(self):
        growth = self.growth
        wrist = self.wrist
        age = self.age
        k = {
            wrist < 15: 0.9,
            15 <= wrist <= 17: 1,
            17 < wrist: 1.1
        }[True]
        ideal1 = growth**2 * 0.00225
        ideal2 = (growth - 100 + age / 10) * 0.9 * k
        ideal = (ideal1 + ideal2) / 2
        return round(ideal * 2) / 2

    def calory_day(self):
        growth = self.growth
        weight = self.weight
        age = self.age
        activity_k = self.daily_activity_level
        gender = self.gender_1
        if gender == 1:
            calory_day = ((10 * weight) + (6.25 * growth) - (5 * age) + 5) * activity_k
        elif gender == 2:
            calory_day = ((10 * weight) + (6.25 * growth) - (5 * age) - 161) * activity_k
        return round(calory_day)

    def calorie_surplus(self):
        bmi = self.bmi()
        calory_day = self.calory_day()
        if bmi > 30:
            calorie_surplus = calory_day * 1.25
        else:
            calorie_surplus = calory_day * 1.15
        return round(calorie_surplus)

    def calorie_deficiency(self):
        bmi = self.bmi()
        calory_day = self.calory_day()
        if bmi > 30:
            calorie_deficiency = calory_day / 1.25
        else:
            calorie_deficiency = calory_day /1.15
        return round(calorie_deficiency)

    def calory_to_low_weight(self):
        calory_day = self.calory_day()
        low_calory = calory_day - calory_day * 0.2

        return round(low_calory)

    def body_type(self):
        gender = self.gender_1
        wrist = self.wrist
        if gender == 1:
            if wrist < 18:
                body_type = {'ru': 'Эктоморфный', 'en': 'Ectomorphic'}
            elif 18 <= wrist <= 20:
                body_type = {'ru': 'Мезоморфный', 'en': 'Mesomorphic'}
            elif wrist > 20:
                body_type = {'ru': 'Эндоморфный', 'en': 'Endomorphic'}
        elif gender == 2:
            if wrist < 15:
                body_type = {'ru': 'Эктоморфный', 'en': 'Ectomorphic'}
            elif 15 <= wrist <= 17:
                body_type = {'ru': 'Мезоморфный', 'en': 'Mesomorphic'}
            elif wrist > 17:
                body_type = {'ru': 'Эндоморфный', 'en': 'Endomorphic'}
        else:
            body_type = ''
        return body_type

    def hip_to_waist_index(self):
        waist = float(self.waist)
        hip = float(self.hip)
        index = waist / hip

        return round(index, 3)

    def hip_to_waist_description(self):
        index = self.hip_to_waist_index()
        description_norm = {'ru': 'Норма', 'en': 'Normal index'}
        description_obes = {'ru': 'Ожирение', 'en': 'Obesity'}
        if self.gender == 1:
            if index < 0.9:
                description = description_norm
            else:
                description = description_obes
        else:
            if index < 0.85:
                description = description_norm
            else:
                description = description_obes

        return description

    def cancer_risks_bmi(self):
        comon_bmi_cancer_risks = []
        bmi = self.bmi()
        bmi_k = (bmi - 25) // 5 + 1
        if bmi < 25:
            description = {
                'icd_id': None,
                'risk_string': 'low',
                'risk_percents': None,
                'message': {'ru': 'У Вас низкий шанс развития онкологических заболеваний.',
                            'en': 'You have a low chance of developing cancer'},
                'recomendation': {'ru': None, 'en': None}
            }
            comon_bmi_cancer_risks.append(description)
        else:
            risk_string = 'High'
            if self.gender == 1:
                # k for male
                cancer_k = {
                    'пищевода (аденокарцинома)': [1.216, {'ru': 'пищевода (аденокарцинома)',
                                                          'en': 'Esophageal adenocarcinoma'}],
                    'щитовидной железы': [0.931, {'ru': 'щитовидной железы', 'en': 'Thyroid'}],
                    'толстой кишки': [5.456, {'ru': 'толстой кишки', 'en': 'Colon'}],
                    'почки': [2.505, {'ru': 'почек', 'en': 'Renal'}],
                    'печени': [1.786, {'ru': 'печени', 'en': 'Liver'}],
                    'меланомы': [4.212, {'ru': 'меланомы', 'en': 'Malignant melanoma'}],
                    'крови (множественной миеломы)': [1.032, {'ru': 'крови (множественной миеломы)',
                                                              'en': 'Multiple myeloma'}],
                    'прямой кишки': [4.796, {'ru': 'прямой кишки', 'en': 'Recrum'}],
                    # 'желчного пузыря': 1.09,
                    'крови (лейкоза)': [2.009, {'ru': 'крови (лейкоза)', 'en': 'Leukemia'}],
                    'поджелудочной желзы': [1.776, {'ru': 'поджелудочной желзы', 'en': 'Pancreas'}],
                    'лимфатической системы (неходжкинской лимфомы)': [
                        2.576, {'ru': 'лимфатической системы (неходжкинской лимфомы)',
                                'en': 'Non-Hodgkin\'s lymphoma'}
                    ],
                    'предстательной железы': [11.948, {'ru': 'предстательной железы', 'en': 'Prostate'}]
                }
            else:
                # k for female
                cancer_k = {
                    'эндометрия': [4.929, {'ru': 'эндометрия', 'en': 'Endometrium'}],
                    # 'желчного пузыря': 1.59,
                    'пищевода (аденокарцинома)': [0.378, {'ru': 'пищевода (аденокарцинома)',
                                                          'en': 'Esophageal adenocarcinoma'}],
                    'почки': [1.367, {'ru': 'почек', 'en': 'Renal'}],
                    'крови (лейкоза)': [1.509, {'ru': 'крови (лейкоза)', 'en': 'Leukemia'}],
                    'щитовидной железы': [2.2, {'ru': 'щитовидной железы', 'en': 'Thyroid'}],
                    'молочной железы (после менапаузы)': [14.56, {'ru': 'молочной железы (после менапаузы)',
                                                                  'en': 'Breast (postmenopausal)'}],
                    'поджелудочной желзы': [1.792, {'ru': 'поджелудочной желзы', 'en': 'Pancreas'}],
                    'крови (множественной миеломы)': [0.788, {'ru': 'крови (множественной миеломы)',
                                                              'en': 'Multiple myeloma'}],
                    'толстой кишки': [4.469, {'ru': 'толстой кишки', 'en': 'Colon'}],
                    'лимфатической системы (неходжкинской лимфомы)': [
                        2.065, {'ru': 'лимфатической системы (неходжкинской лимфомы)',
                                'en': 'Non-Hodgkin\'s lymphoma'}
                    ],
                    'печени': [0.663, {'ru': 'печени', 'en': 'Liver'}]
                }

            for key in cancer_k:
                # cancer_level = round(cancer_k[key]**bmi_k, 2)
                cancer_level = round(cancer_k[key][0], 1)
                description = {
                    'icd_id': None,
                    'risk_string': risk_string,
                    'risk_percents': str(cancer_level) + ' %.',
                    'message': {'ru': 'Ожирение увеличивает риск развития злокачественных образований ' + cancer_k[key][1]['ru'] + ' на ',
                                'en': 'Obesity increases ' + cancer_k[key][1]['en'] + ' cancer level by '},
                    'recomendation': {'ru': 'Снижение веса позволит снизить риск развития раковых заболеваний.',
                                      'en': 'Lowering weight will reduce your risk of developing cancer.'}
                }
                comon_bmi_cancer_risks.append(description)
        return comon_bmi_cancer_risks

    def diabetes_risk_bmi(self):
        bmi = self.bmi()
        risk = []
        if bmi >= 25:
            diabetes_risk = {
                25 <= bmi < 30: 2,
                bmi >= 30: 5
            }[True]
            description = {
                'icd_id': None,
                'risk_string':  'High',
                'risk_percents': None,
                'message': {'ru': 'Ожирение увеличивает риск развития диабета 2 типа в ' + str(diabetes_risk) + ' раз(а).',
                            'en': 'Obesity increases diabetes risk by ' + str(diabetes_risk) + ' times.'},
                'recomendation': {'ru': 'Снижение веса позволит снизить риск развития раковых заболеваний и улучшить контроль за уровнем сахара в крови.',
                                  'en': 'Lowering weight will reduce your risk of developing cancer and improve your blood sugar control.'}
            }
            risk.append(description)
        return risk

    def stroke_risk_bmi(self):
        bmi = self.bmi()
        risk = []
        if bmi >= 25:
            stroke_risk = {
                25 <= bmi < 30: 1.22,
                bmi >= 30: 1.7
            }[True]
            description = {
                'icd_id': None,
                'risk_string':  'High',
                'risk_percents': None,
                'message': {'ru': 'Ожирение повышает риск развития инсульта в ' + str(stroke_risk) + ' раз.',
                            'en': 'Obesity increases stroke risk by ' + str(stroke_risk) + ' times.'},
                'recomendation': {'ru': 'Снижение веса позволит снизить риск инсульта.',
                                  'en': 'Lowering weight will reduce your risk of stroke.'}
            }
            risk.append(description)
        return risk

    def score_description(self):
        score = self.score_risk()
        dict = []
        if score is not None:
            if score > 5:
                risk_string = 'High'
            else:
                risk_string = 'low'
            recomendation = {'ru': 'Данный индекс зависит от уровня холестерина в крови, артериального давления и курения. Приведение целевых показателей в норму позволит снизить риск развития сердечно-сосудистых заболеваний.',
                             'en': 'This index depend on cholesterol level, arterial pressure and smoking. Bringing target values back to normal will reduce the risk of cardiovascular diseases.'}
            if score == 0:
                description = {
                    'icd_id': None,
                    'risk_string': risk_string,
                    'risk_percents': None,
                    'message': {
                        'ru': 'В ближайшие 10 лет у вас низкий риск развития серьезных последствий, связанных с сердечно-сосудистыми заболеваниями.',
                        'en': 'You have a low risk of developing serious consequences associated with cardiovascular diseases in the next 10 years.'},
                    'recomendation': {'ru': None, 'en': None}
                }
            else:
                description = {
                    'icd_id': None,
                    'risk_string': risk_string,
                    'risk_percents': str(score) + ' %',
                    'message': {'ru': 'Вероятность серьезных последствий связанных с сердечно-сосудистыми заболеваниями в ближайшие 10 лет ',
                                'en': 'The probability of serious consequences associated with cardiovascular diseases in the next 10 years '},
                    'recomendation': recomendation
                }
            dict.append(description)
            return dict
        else:
            return dict

    def score_risk(self):
        if self.blood_pressure_sistolic is not None and self.total_cholesterol is not None:
            risk_list = np.array([
                # female
                [
                    # no smoke
                    [
                        # 40yo
                        [
                            # 120
                            [0, 0, 0, 0, 0],
                            # 140
                            [0, 0, 0, 0, 0],
                            # 160
                            [0, 0, 0, 0, 0],
                            # 180
                            [0, 0, 0, 0, 0]
                        ],
                        # 45yo
                        [
                            # 120
                            [0, 0, 1, 1, 1],
                            # 140
                            [0, 1, 1, 1, 1],
                            # 160
                            [1, 1, 1, 1, 1],
                            # 180
                            [1, 1, 1, 2, 2]
                        ],
                        # 55yo
                        [
                            # 120
                            [1, 1, 1, 1, 1],
                            # 140
                            [1, 1, 1, 1, 2],
                            # 160
                            [1, 2, 2, 2, 3],
                            # 180
                            [2, 2, 3, 3, 4]
                        ],
                        # 60yo
                        [
                            # 120
                            [1, 1, 2, 2, 2],
                            # 140
                            [2, 2, 2, 3, 3],
                            # 160
                            [3, 3, 3, 4, 5],
                            # 180
                            [4, 4, 5, 6, 7]
                        ],
                        # 65yo
                        [
                            # 120
                            [2, 2, 3, 3, 4],
                            # 140
                            [3, 3, 4, 5, 6],
                            # 160
                            [5, 5, 6, 7, 8],
                            # 180
                            [7, 8, 9, 10, 12]
                        ]
                    ],
                    # smoke
                    [
                        # 40yo
                        [
                            # 120
                            [0, 0, 0, 0, 0],
                            # 140
                            [0, 0, 0, 0, 0],
                            # 160
                            [0, 0, 0, 0, 0],
                            # 180
                            [0, 0, 0, 1, 1]
                        ],
                        # 45yo
                        [
                            # 120
                            [1, 1, 1, 1, 1],
                            # 140
                            [1, 1, 1, 1, 2],
                            # 160
                            [1, 2, 2, 2, 3],
                            # 180
                            [2, 2, 3, 3, 4]
                        ],
                        # 55yo
                        [
                            # 120
                            [1, 1, 2, 2, 2],
                            # 140
                            [2, 2, 2, 3, 3],
                            # 160
                            [3, 3, 4, 4, 5],
                            # 180
                            [4, 5, 5, 6, 7]
                        ],
                        # 60yo
                        [
                            # 120
                            [2, 3, 3, 4, 4],
                            # 140
                            [3, 4, 5, 5, 6],
                            # 160
                            [5, 6, 7, 8, 9],
                            # 180
                            [8, 9, 10, 11, 13]
                        ],
                        # 65yo
                        [
                            # 120
                            [4, 5, 5, 6, 7],
                            # 140
                            [6, 7, 8, 9, 11],
                            # 160
                            [9, 10, 12, 13, 16],
                            # 180
                            [13, 15, 17, 19, 22]
                        ]
                    ]

                ],
                # male
                [
                    # no smoke
                    [
                        # 40yo
                        [
                            # 120
                            [0, 0, 1, 1, 1],
                            # 140
                            [0, 1, 1, 1, 1],
                            # 160
                            [1, 1, 1, 1, 1],
                            # 180
                            [1, 1, 1, 2, 2]
                        ],
                        # 45yo
                        [
                            # 120
                            [1, 1, 2, 2, 2],
                            # 140
                            [2, 2, 2, 3, 3],
                            # 160
                            [2, 3, 3, 4, 5],
                            # 180
                            [4, 4, 5, 6, 7]
                        ],
                        # 55yo
                        [
                            # 120
                            [2, 2, 3, 3, 4],
                            # 140
                            [3, 3, 4, 5, 6],
                            # 160
                            [4, 5, 6, 7, 8],
                            # 180
                            [6, 7, 8, 10, 12]
                        ],
                        # 60yo
                        [
                            # 120
                            [3, 3, 4, 5, 6],
                            # 140
                            [4, 5, 6, 7, 9],
                            # 160
                            [6, 7, 9, 10, 12],
                            # 180
                            [9, 11, 13, 15, 18]
                        ],
                        # 65yo
                        [
                            # 120
                            [4, 5, 6, 7, 9],
                            # 140
                            [6, 8, 9, 11, 13],
                            # 160
                            [9, 11, 13, 15, 16],
                            # 180
                            [14, 16, 19, 22, 26]
                        ]
                    ],
                    # smoke
                    [
                        # 40yo
                        [
                            # 120
                            [1, 1, 1, 1, 1],
                            # 140
                            [1, 1, 1, 2, 2],
                            # 160
                            [1, 2, 2, 2, 3],
                            # 180
                            [2, 2, 3, 3, 4]
                        ],
                        # 45yo
                        [
                            # 120
                            [2, 3, 3, 4, 5],
                            # 140
                            [3, 4, 5, 6, 7],
                            # 160
                            [5, 6, 7, 8, 10],
                            # 180
                            [7, 8, 10, 12, 14]
                        ],
                        # 55yo
                        [
                            # 120
                            [4, 4, 5, 6, 8],
                            # 140
                            [5, 6, 8, 9, 11],
                            # 160
                            [8, 9, 11, 13, 16],
                            # 180
                            [12, 13, 16, 19, 22]
                        ],
                        # 60yo
                        [
                            # 120
                            [6, 7, 8, 10, 12],
                            # 140
                            [8, 10, 12, 14, 17],
                            # 160
                            [12, 14, 17, 20, 24],
                            # 180
                            [18, 21, 24, 28, 33]
                        ],
                        # 65yo
                        [
                            # 120
                            [9, 10, 12, 14, 17],
                            # 140
                            [13, 15, 17, 20, 24],
                            # 160
                            [18, 21, 25, 29, 34],
                            # 180
                            [26, 30, 35, 41, 47]
                        ]
                    ]
                ]
            ])
            # risk_list[a][b][c][d][e]
            #   a - gender 0f 1m
            #   b - smoke 1 or 0
            #   c - age groupe
            #   d - presure level
            #   e - cholesterol

            smoking = self.smoking
            cholesterol = self.total_cholesterol
            bp_sist = self.blood_pressure_sistolic
            age = self.user_age()
            gender = self.gender

            presure_to_num = {bp_sist < 120: 0,
                              120 <= bp_sist < 140: 0,
                              140 <= bp_sist < 160: 1,
                              160 <= bp_sist < 180: 2,
                              180 <= bp_sist: 3
                              }[True]

            cholesterol_to_num = {cholesterol < 4: 0,
                                  4 <= cholesterol < 5: 0,
                                  5 <= cholesterol < 6: 1,
                                  6 <= cholesterol < 7: 2,
                                  7 <= cholesterol < 8: 3,
                                  8 <= cholesterol: 4
                                  }[True]

            age_to_num = {age < 40: 0,
                          40 <= age < 45: 0,
                          45 <= age < 55: 1,
                          55 <= age < 60: 2,
                          60 <= age < 65: 3,
                          65 <= age: 4
                          }[True]
            return risk_list[gender][smoking][age_to_num][presure_to_num][cholesterol_to_num]

    def recomendations(self):
        gender = self.gender_1
        ibm = self.bmi()
        wrist = self.wrist
        fat_cat = self.fat_percent_category()
        calory_day = self.calory_day()
        calorie_surplus = self.calorie_surplus()
        calorie_deficiency = self.calorie_deficiency()
        obesity_level = self.obesity_level()
        rec_low = {'message_short': {'ru': 'У вас недостаточный вес.', 'en': 'You are underweight.'},
                   'message_long': {'ru': 'Количество потребляемых килокалорий для поддержания текущего веса: {} кКал. Для набора веса: {} кКал. Соблюдайте соотношение белков, жиров и углеводов в рационе: 25/15/60%'.format(
                          calory_day, calorie_surplus),
                       'en': 'The number of calories consumed to maintain current weight: {} kcal. For weight gain: {} kcal. Maintain the ratio of protein, fat, and carbohydrates in the diet: 25/15/60%'.format(
                          calory_day, calorie_surplus)},
                   'importance_level': 'Without color'}

        rec_norm = {'message_short': {'ru': 'Вес в норме.', 'en': 'Your weight is normal.'},
                    'message_long': {'ru': 'Количество потребляемых килокалорий для поддержания текущего веса: {} кКал. Соблюдайте соотношение белков, жиров и углеводов в рационе: 25/35/40%.'.format(
                           calory_day),
                        'en': 'The number of calories consumed to maintain current weight: {} kcal. Maintain the ratio of protein, fat and carbohydrates in the diet: 25/35/40%.'.format(
                           calory_day)},
                    'importance_level': 'Without color'}

        rec_high = {'message_short': {'ru': '{}'.format(obesity_level['ru']), 'en': '{}'.format(obesity_level['en'])},
                    'message_long': {'ru': 'Количество потребляемых килокалорий для поддержания текущего веса: {} кКал. Для уменьшения веса: {} кКал. Соблюдайте соотношение белков, жиров и углеводов в рационе: 50/30/20%.'.format(
                           calory_day, calorie_deficiency),
                        'en': 'The number of calories consumed to maintain current weight: {} kcal. To reduce weight: {} kcal. Maintain the ratio of protein, fat, and carbohydrates in the diet: 50/30/20%.'.format(
                           calory_day, calorie_deficiency)},
                    'importance_level': 'Without color'}

        rec_wrist = {'message_short': {'ru': 'Предрасположенность к избыточному весу.', 'en': 'Overweight predisposition.'},
                    'message_long': {'ru': 'Вы предрасполложены к избыточному весу.', 'en': 'You are predisposed to being overweight.'},
                    'importance_level': 'Without color'}

        recomendations = [{
            'message_short': {'ru': 'Старайтесь проходить за день более 8000 шагов.', 'en': 'Walk more than 8000 steps per day.'},
            'message_long': {'ru': 'Достаточный уровень активности позволит чувствовать себя лучше, снизить вес и снизить риски развития заболеваний.',
                             'en': 'Getting enough activity will help you feel better, lose weight, and reduce your risk of diseases.'},
            'importance_level': 'Without color'
        }]
        if wrist > 20 and gender == 1:
            recomendations.append(rec_wrist)
        elif wrist > 17 and gender == 2:
            recomendations.append(rec_wrist)

        if fat_cat <= 1 or (ibm < 18):
            recomendations.append(rec_low)
        elif fat_cat == 2 or (18 < ibm < 25):
            recomendations.append(rec_norm)
        elif fat_cat >= 3 and ibm > 25:
            recomendations.append(rec_high)
            rec = {
                'message_short': {'ru': 'Постарайтесь снизить свой вес.', 'en': 'Low your weight.'},
                'message_long': {'ru': 'Индекс массы тела должен быть от 18.5 до 24.9.',
                                 'en': 'Body mass index should be from 18.5 to 24.9.'},
                'importance_level': 'High'
            }
            recomendations.append(rec)
        if self.smoking == 1:
            rec = {
                'message_short': {'ru': 'Откажитесь от курения или снизьте число выкуриваемых в день сигарет.',
                                  'en': 'Stop smoking or decrease cigarette count per day.'},
                'message_long': {'ru': 'Курение способно спровоцировать развитие онкологических заболеваний, повысить риск легочных и сердечно-сосудистых заболеваний.',
                                 'en': 'Smoking can provoke the development of cancer, increase the risk of lung and cardiovascular diseases.'},
                'importance_level': 'High'
            }
            recomendations.append(rec)

        if self.total_cholesterol and self.total_cholesterol > 5:
            rec = {
                'message_short': {'ru': 'Снизте уровень холестирина.', 'en': 'Low your cholesterol.'},
                'message_long': {'ru': 'Уровень холестирина в крови должен быть менее 5 ммоль/л.',
                                 'en': 'Cholesterol level should be less than 5 mmol/L.'},
                'importance_level': 'High'
            }
            recomendations.append(rec)
        if self.blood_glucose_level and self.blood_glucose_level > 5.5:
            rec = {
                'message_short': {'ru': 'Повышен уровень глюкозы.', 'en': 'The glucose level is increased.'},
                'message_long': {'ru': 'Уровень глюкозы в крови должен быть менее 6.2 ммоль/л. Повышенный уровень глюкозы в крови может быть первым признаком диабета.',
                                 'en': 'Glucose level should be less than 6.2 mmol/L. Glucose upper than normal level may be first sign of diabetes.'},
                'importance_level': 'High'
            }
            recomendations.append(rec)
        return recomendations









# class CardioNotifications:
#     '''Notifications for the single cardio deviation from normal'''
#
#     def cardio_notifications(data, request):
#         notifications_dict = [
#         ]
#
#         heart_rate_alone = data['heart_rate_alone']
#         blood_pressure_sistolic = data['blood_pressure_sys']
#         blood_pressure_diastolic = data['blood_pressure_dia']
#
#         '''User Age'''
#         user_birth_date = HealthData.objects.filter(user=request.user).first().birth_date
#         date_now = datetime.now().date()
#         age = str((date_now - user_birth_date) / 31536000).split(':')
#         user_age = int(float(age[-1]))
#
#         if  4 <= user_age <= 6:
#             if heart_rate_alone < 86:
#                 notif = {'message_heart_rate': 'Брадикардия'}
#                 notifications_dict.append(notif)
#             elif heart_rate_alone > 130:
#                 notif = {'message_heart_rate': 'Тахикардия'}
#                 notifications_dict.append(notif)
#         elif 7 <= user_age <= 10:
#             if heart_rate_alone < 70:
#                 notif = {'message_heart_rate': 'Брадикардия'}
#                 notifications_dict.append(notif)
#             elif heart_rate_alone > 110:
#                 notif = {'message_heart_rate': 'Тахикардия'}
#                 notifications_dict.append(notif)
#         elif user_age >= 15:
#             if heart_rate_alone < 60:
#                 notif = {'message_heart_rate': 'Брадикардия'}
#                 notifications_dict.append(notif)
#             elif heart_rate_alone > 80:
#                 notif = {'message_heart_rate': 'Тахикардия'}
#                 notifications_dict.append(notif)
#             if blood_pressure_sistolic < 100:
#                 notif = {'message_blood_pressure': 'Ваше систолическое давление ниже нормы'}
#                 notifications_dict.append(notif)
#             elif blood_pressure_sistolic > 140:
#                 notif = {'message_blood_pressure': 'Ваше систолическое давление выше нормы'}
#                 notifications_dict.append(notif)
#             if blood_pressure_diastolic < 60:
#                 notif = {'message_blood_pressure': 'Ваше диастолическое давление ниже нормы'}
#                 notifications_dict.append(notif)
#             elif blood_pressure_diastolic > 100:
#                 notif = {'message_blood_pressure': 'Диастолическое давление выше нормы'}
#                 notifications_dict.append(notif)
#             else:
#                 pass
#
#         return notifications_dict


