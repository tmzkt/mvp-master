from copy import deepcopy

from django.template.context_processors import request

from .models import HealthData, Result


def health_data_and_result_not_empty(request):
    if request.user.is_authenticated:
        try:
            data = HealthData.objects.filter(user=request.user).values()[0]
        except:
            data = None
        data_res = deepcopy(data)

        # TODO: this code raises an exception when deleting a user profile
        try:
            for key, value in data.items():
                if value or key in ['smoker', 'country', 'cholesterol', 'glucose', 'locale', 'heart_rate_alone',
                                    'blood_pressure_sys', 'blood_pressure_dia', 'measuring_system']:
                    data_res.pop(key, None)
            data_filled = False if data_res else True
        except AttributeError:
            return {'data_filled': False,
                    'result_filled': False}

        try:
            result = Result.objects.filter(pk=request.user.health_data.result.id).first()
        except:
            result = None
        if result:
            result_filled = True if result.bmi else False
        else:
            result_filled = False
    else:
        data_filled = False
        result_filled = False

    return {'data_filled': data_filled,
            'result_filled': result_filled}
