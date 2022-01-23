from django.http import Http404
from django.utils.translation import gettext_lazy as _
from collections import OrderedDict

#import logging
#logger = logging.getLogger('django')


def marker(obj):

    if isinstance(obj, dict):
        obj['bmi'] = [obj['bmi'], '#2C8F3C'] if 18.5 <= obj['bmi'] < 25 else [obj['bmi'], '#FF1744']
        obj['obesity_level'] = [obj['obesity_level'], '#0254B8'] if obj['obesity_level'] in \
                        ['Вес в норме', 'Normal weight'] else [obj['obesity_level'], '#FF1744']
        obj['common_risk_level'] = [obj['common_risk_level'], '#0254B8'] if obj['common_risk_level'] \
                        in ['средний', 'medium'] else [obj['common_risk_level'], '#FF1744']
        

        fat_percent = '{} %'.format(obj['fat_percent'])
        obj['fat_percent'] = [fat_percent, '#2C8F3C'] if obj['fat_category'] == 2 else [fat_percent, '#FF1744']
        return obj
    else:
        obj.bmi = [obj.bmi, '#2C8F3C'] if 18.5 <= obj.bmi < 25 else [obj.bmi, '#FF1744']
        obj.obesity_level = [obj.obesity_level, '#0254B8'] if obj.obesity_level in \
                            ['Вес в норме', 'Normal weight'] else [obj.obesity_level, '#FF1744']
        obj.common_risk_level = [obj.common_risk_level, '#0254B8'] if obj.common_risk_level \
                            in ['средний', 'medium'] else [obj.common_risk_level, '#FF1744']

        fat_percent = '{} %'.format(obj.fat_percent)
        obj.fat_percent = [fat_percent, '#2C8F3C'] if obj.fat_category == 2 else [fat_percent, '#FF1744']
        return obj


def marker_1(obj):
    for key in range(len(obj['disease_risk'])):
        if obj['disease_risk'][key]['risk_percents']:
            obj['disease_risk'][key]['risk_percents'] = float(obj['disease_risk'][key]['risk_percents'].split(' ')[0])
        if obj['disease_risk'][key]['risk_string'] == 'High':
            obj['disease_risk'][key]['risk_string'] = '#FFC6D1'
        else:
            obj['disease_risk'][key]['risk_string'] = '#C7FFD0'
    for key in range(len(obj['common_recomendations'])):
        if obj['common_recomendations'][key]['importance_level'] == 'High':
            obj['common_recomendations'][key]['importance_level'] = '#FFC6D1'
        elif obj['common_recomendations'][key]['importance_level'] == 'Without color':
            obj['common_recomendations'][key]['importance_level'] = ''
        else:
            obj['common_recomendations'][key]['importance_level'] = '#C7FFD0'
    return obj


def disease_risk_marker(disease_risk):
    for item in disease_risk:
        item['risk_string'] = '#FFC6D1' if item['risk_string'] == 'High' else '#C7FFD0'
        if item['risk_percents'] is not None :
            item['risk_percents'] = float(item['risk_percents'].split(' ')[0])
    return disease_risk


def common_recomendations_marker(common_recomendations):
    for item in common_recomendations:
        level = {
            item['importance_level'] == 'High': '#FFC6D1',
            item['importance_level'] == 'Without color': '#FFC6D1',
        }
        item['importance_level'] = level.get(True, '#C7FFD0')
    return common_recomendations


def disease_and_recomendation_decorator(func):
    def disease_and_recomendation_wrapper(obj):
        disease_risk = obj.pop('disease_risk', None)
        common_recomendations = obj.pop('common_recomendations', None)

        obj = func(obj)

        if disease_risk is not None:  # cms.view.params
            obj['disease_risk'] = disease_risk_marker(disease_risk)
        if common_recomendations is not None:
            obj['common_recomendations'] = common_recomendations_marker(common_recomendations)

        return obj
    return disease_and_recomendation_wrapper


@disease_and_recomendation_decorator
def add_descriptions(obj):
    if obj['bmi']:
        bmi = obj['bmi']
        category_obesity_level = {
            bmi < 18.5: 'cat1',
            18.5 <= bmi < 25: 'cat2',
            25 <= bmi < 30: 'cat3',
            30 <= bmi < 35: 'cat4',
            35 <= bmi < 40: 'cat5',
            40 <= bmi: 'cat6'
        }[True]
    else:
        raise Http404

    dict_obesity_level_description = {
        'cat1': _('Low body weight is based on your body parameters, height, and body fat percentage. '
                  'May lead to the development of serious diseases and, over time, with a further decrease, '
                  'develop into anorexia'),
        'cat2': _('Normal body weight based on your body parameters, height, and percentage of body fat. '
                  'Does not have any serious health consequences associated with being overweight'),
        'cat3': _('Being overweight is based on your body parameters, height, and percentage of subcutaneous fat. '
                  'With further weight gain, obesity of the 1st degree may develop'),
        'cat4': _('Not significantly exceeding normal body weight, which will not lead to serious health '
                  'consequences. However, with further weight gain, obesity of the 2nd degree may develop.'),
        'cat5': _('Significant increase in body weight, which is possibly chronic. With obesity of the 2nd degree, '
                  'all types of metabolism are disrupted, it may lead to the development of serious pathologies: '
                  'heart disease, stroke, diabetes mellitus, risk of sudden cardiac death, etc.'),
        'cat6': _('Significant increase in body weight, in which the body mass index is more than 40. Obesity of 3rd '
                  'degree is accompanied by numerous changes in the work of all organs, systems, and hormonal '
                  'disorders')
    }

    category_body_type = {
        obj['body_type'] == 'Эктоморфный' or obj['body_type'] == 'Ectomorphic': 'cat1',
        obj['body_type'] == 'Мезоморфный' or obj['body_type'] == 'Mesomorphic': 'cat2',
        obj['body_type'] == 'Эндоморфный' or obj['body_type'] == 'Endomorphic': 'cat3'
    }[True]

    dict_body_type_description = {
        'cat1': _('This type is characterized by a fragile and refined figure. Narrow shoulders and ribcage, '
                  'lean and weak muscles'),
        'cat2': _('This type is usually characterized by well-developed muscles. Medium height, strong skeleton, '
                  'harmonious length of the limbs, and a moderately wide chest'),
        'cat3': _('This type is characterized by relatively short stature and a dense physique. Mainly short limbs '
                  'and neck, broad ribcage, and hips, strong skeleton')
    }

    try:
        obesity_level_description = dict_obesity_level_description[category_obesity_level]
    except KeyError:
        obesity_level_description = 'Without description'

    try:
        body_type_description = dict_body_type_description[category_body_type]
    except KeyError:
        body_type_description = 'Without description'

    dict_descriptions = {
        'bmi': _("Body mass index is a value that allows you to assess the degree of correspondence between a "
                 "person's weight and his height and thereby, indirectly, assess whether the mass is low, normal, "
                 "or overweight"),
        'obesity_level': obesity_level_description,
        'ideal_weight': _('Displays the ideal body weight calculated based on '
                          'your body and height parameters'),
        'base_metabolism': _('The minimum amount of calories (energy) that your body burns at rest, necessary to '
                             'ensure normal functioning'),
        'calories_to_low_weight': _('Some of the calories'),
        'waist_to_hip_proportion': _("The ratio is determined by dividing the waist circumference by the pelvic "
                                     "circumference. This value is an indicator of a person's health and the risk of "
                                     "developing serious diseases. (Изменена русская формулировка)"),
        'passport_age': _('Your age according to the birth date'),
        'common_risk_level': _('Overall risk of developing serious obesity-related diseases. '
                               'Determined based on your physical and biological parameters'),
        'prognostic_age': _('Calculated age'),
        'fat_percent': _('One of the indicators that means the presence or absence of excess weight'),
        'body_type': body_type_description,
        'fat_category': '',
        'CVD': '',
        'unfilled': ''
    }

    dict_color = {
        'bmi': '#2C8F3C' if 18.5 <= obj['bmi'] < 25 else '#FF1744',
        'obesity_level': '#0254B8' if category_obesity_level == 'cat2' else '#FF1744',
        'ideal_weight': '',
        'base_metabolism': '',
        'calories_to_low_weight': '',
        'waist_to_hip_proportion': '',
        'passport_age': '',
        'common_risk_level': '#0254B8',
        'prognostic_age': '',
        'fat_percent': '#2C8F3C' if obj.get('fat_category', None) == 2 else '#FF1744',
        #'fat_percent': '#2C8F3C' if obj['fat_percent'][1] == 2 else '#FF1744',
        'body_type': '',
        'fat_category': '',
        'CVD': '',
        'unfilled': ''
    }

    list_of_dicts = []
    for key, item in obj.items():
        list_of_dicts.append(
            {
                'name': key,
                'value': item,
                'color': dict_color[key],
                'desc': dict_descriptions[key]
            }
        )

    dict_to_ord_dict = [("params", list_of_dicts)]

    return OrderedDict(dict_to_ord_dict)
