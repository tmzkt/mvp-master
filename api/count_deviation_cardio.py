from datetime import datetime, timedelta
from collections import Counter
from django.utils import timezone
from django.db.models import Sum
from cms.models import HealthData, CardioActivity, Disease

def count(request):
    data = request.data
    birth_date = HealthData.objects.filter(user=request.user).first().birth_date
    disease = Disease.objects.filter(user=request.user).first()
    if birth_date and birth_date != "null":
        data["birth_date"] = birth_date.strftime("%d.%m.%Y")
    data['locale'] = "ru" if request.LANGUAGE_CODE.startswith("ru") else "en"
    locale = data['locale']

    json_dict = {"message_pressure": blood_pressure(data['blood_pressure_sys'], data['blood_pressure_dia'], locale)[1],
                 "message_heart_rate": heart_rate(data['heart_rate_alone'], data)[1]}

    start_date = timezone.now() - timedelta(days=6)
    date_count = disease.update_count if disease else None
    end_date = timezone.now()

    if not date_count or datetime.date(date_count) < datetime.date(start_date):
        # Выбираем данные за текущую неделю
        data_pressure_this_week = CardioActivity.objects.filter(health_model=request.user.health_data,
                                                                measuring_date__date__range=(start_date, end_date)). \
                                                                values('measuring_date', 'blood_pressure_sys',
                                                               'blood_pressure_dia', 'heart_rate_alone')
        count_this_week = len(data_pressure_this_week)
        # Выбираем данные за предыдущую неделю
        end_date = start_date - timedelta(days=1)
        start_date = start_date - timedelta(days=7)
        data_pressure_last_week = CardioActivity.objects.filter(health_model=request.user.health_data,
                                                                measuring_date__date__range=(start_date, end_date)). \
                                                                values('measuring_date', 'blood_pressure_sys',
                                                                'blood_pressure_dia', 'heart_rate_alone')
        count_last_week = len(data_pressure_last_week)
        if count_this_week and count_last_week:
            json_dict['message_differ_pressure'] = pressure_differ(data_pressure_this_week, data_pressure_last_week,
                                                                   count_this_week, count_last_week, locale)
            json_dict['message_differ_rate'] = rate_differ(data_pressure_this_week, data_pressure_last_week,
                                                           count_this_week, count_last_week, locale)
        # Проверяем есть ли измерения за последнюю неделю
        measuring_dates = set([datetime.date(i['measuring_date']) for i in data_pressure_this_week])
        dates = set([datetime.date(timezone.now() - timedelta(days=i)) for i in range(7)])
        if dates == measuring_dates:
            res_pressure = calc_pressure(data_pressure_this_week, measuring_dates, disease, locale)
            res_rate = calc_heart_rate(data, data_pressure_this_week, measuring_dates, disease)
            json_dict['message_chance_cardiovascular_disease'] = res_pressure[1]
            json_dict['message_chance_heart_rate_disease'] = res_rate[1]
            Disease.objects.update_or_create(user=request.user, defaults={'user': request.user,
                                            'risk_disease_blood_pressure': res_pressure[0],
                                            'risk_disease_heart_rate': res_rate[0],
                                            'update_count': timezone.now()})


    return json_dict

def user_age(data):
    b_date = datetime.strptime(data['birth_date'], '%d.%m.%Y')
    age = (datetime.today() - b_date).days // 365
    return age

def blood_pressure(sys, dia, locale):
    if sys < 100 and dia < 60:
        return (0, "Давление низкое. Проконсультируйтесь у врача." if locale=="ru" else "The pressure is low. Consult your doctor.")
    elif 100 <= sys < 120 and 60 <= dia < 80:
        return (1, "Давление оптимальное." if locale=="ru" else "The pressure is optimal.")
    elif 120 <= sys < 130 and 80 <= dia < 85:
        return (2, "Давление нормальное." if locale=="ru" else "The pressure is normal.")
    elif 130 <= sys < 140 and 85 <= dia < 90:
        return (3, "Давление нормальное высокое. Проконсультируйтесь у врача." if locale=="ru" else "Normal high blood pressure. Consult your doctor.")
    elif 140 <= sys < 160 and 90 <= dia < 100:
        return (3, "Давление высокое. Проконсультируйтесь у врача." if locale=="ru" else "High pressure. Consult your doctor.")
    elif 160 <= sys < 180 and 100 <= dia < 110:
        return (3, "Давление чрезмерно высокое. Обратитесь к врачу." if locale=="ru" else "The pressure is too high. See your doctor.")
    elif sys >= 180 and dia >= 110:
        return (3, "Давление опасно высокое. Срочная медицинская помощь!" if locale=="ru" else "The pressure is dangerously high. Urgent medical assistance!")
    else:
        return (None, None)

def heart_rate(heart_rate, data):
    locale = data['locale']
    age = user_age(data)
    if (heart_rate < 60 and age >= 11) or (heart_rate < 86 and 4 <= age <= 6) or \
            (heart_rate < 70 and 7 <= age <= 10):
        return (0, "Замедленное сердцебиение. Проконсультируйтесь у врача." if locale=="ru" else "Slow heartbeat. Consult your doctor.")
    elif (86 <= heart_rate <= 130 and 4 <= age <= 6) or (70 <= heart_rate <= 110 and 7 <= age <= 10) \
            or (60 <= heart_rate <= 100 and 11 <= age <= 14) or \
            (60 <= heart_rate <= 90 and age >= 15) :
        return (1, "Нормальное сердцебиение." if locale=="ru" else "Normal heartbeat." )
    elif (heart_rate > 90 and age >= 15) or (heart_rate > 130 and 4 <= age <= 6) or \
            (heart_rate > 110 and 7 <= age <= 10) or (heart_rate > 100 and 11 <= age <= 14):
        return (2, "Учащенное сердцебиение. Проконсультируйтесь у врача." if locale=="ru" else "Cardiopalmus. Consult your doctor." )
    else:
        return (None, None)

def calc_pressure(data_pressure, measuring_dates, disease, locale):
    pressure_7 = []
    for date in measuring_dates:
        pressure = [blood_pressure(data_pressure[i]['blood_pressure_sys'], data_pressure[i]['blood_pressure_dia'], locale)[0]
                    for i in range(len(data_pressure)) if datetime.date(data_pressure[i]['measuring_date'])==date]
        l = len(pressure)
        if l > 1:
            dict = Counter(pressure)
            if dict[0] >= l * 0.6:
                pressure_7.append(0)
            elif dict[3] >= l * 0.6:
                pressure_7.append(4)
            else:
                pressure_7.append(max([dict[1], dict[2]]))
        else:
            pressure_7 += pressure
    dict = Counter(pressure_7)
    if dict[0] >= 4 and (not disease or disease.disease_blood_pressure != 1):
        return (1, "Вероятность наличия артериальной гипотензии (пониженное АД). Пожалуйста проконсультируйтесь у Вашего врача." if locale=="ru" else "The likelihood of arterial hypotension (low blood pressure). Please consult your doctor.")
    elif dict[3] >= 4 and (not disease or disease.disease_blood_pressure not in [2, 3, 4, 5, 6]):
        return (3, "Вероятность наличия артериальной гипертонии (повышенное артериальное давление). Пожалуйста проконсультируйтесь у Вашего врача" if locale=="ru" else "The likelihood of arterial hypertension (high blood pressure). Please consult your doctor")
    else:
        if not disease or not disease.disease_blood_pressure:
            a = (max([dict[1], dict[2]]))
            return (1, "Давление оптимальное" if locale=="ru" else "Optimal pressure") if a == 1 else (2, "Давление нормальное" if locale=="ru" else "Normal pressure")
        return (None, None)

def calc_heart_rate(data, data_pressure, measuring_dates, disease):
    locale = data['locale']
    rate_7 = []
    for date in measuring_dates:
        rate = [heart_rate(data_pressure[i]['heart_rate_alone'], data)[0] for i in range(len(data_pressure))
                if datetime.date(data_pressure[i]['measuring_date'])==date]
        l = len(rate)
        if l > 1:
            dict = Counter(rate)
            if dict[0] >= l * 0.6:
                rate_7.append(0)
            elif dict[2] >= l * 0.6:
                rate_7.append(2)
            else:
                rate_7.append(1)
        else:
            rate_7 += rate
    dict = Counter(rate_7)
    if dict[0] >= 4 and (not disease or disease.disease_heart_rate != 1):
        return (1, "Вероятность наличия, брадикардии (замедленное сердцебиение). Пожалуйста проконсультируйтесь у Вашего врача." if locale=="ru" else "The likelihood of having bradycardia (slow heartbeat). Please consult your doctor." )
    elif dict[2] >= 4 and (not disease or disease.disease_heart_rate != 2):
        return (2, "Вероятность наличия тахикардии (учащенное сердцебиение). Пожалуйста проконсультируйтесь у Вашего врача." if locale=="ru" else "The likelihood of having tachycardia (heart palpitations). Please consult your doctor.")
    else:
        if not disease or not disease.disease_heart_rate:
            return (0, "Сердцебиение в норме." if locale=="ru" else "Heartbeat is normal.")
        return (None, None)

def pressure_differ(data_pressure_this_week, data_pressure_last_week,
                                    count_this_week, count_last_week, locale):
    mean_sys_this_week = round(
        data_pressure_this_week.aggregate(total=Sum('blood_pressure_sys'))['total'] / count_this_week)
    mean_dia_this_week = round(
        data_pressure_this_week.aggregate(total=Sum('blood_pressure_dia'))['total'] / count_this_week)

    mean_sys_last_week = round(
        data_pressure_last_week.aggregate(total=Sum('blood_pressure_sys'))['total'] / count_last_week)
    mean_dia_last_week = round(
        data_pressure_last_week.aggregate(total=Sum('blood_pressure_dia'))['total'] / count_last_week)

    if mean_sys_this_week > mean_sys_last_week and mean_dia_this_week > mean_dia_last_week:
        return "Ваше артериальное давление повысилось относительно предыдущих замеров." if locale=="ru" else "Your blood pressure has increased relative to previous measurements."
    elif mean_sys_this_week < mean_sys_last_week and mean_dia_this_week < mean_dia_last_week:
        return "Ваше артериальное давление понизилось относительно предыдущих замеров." if locale=="ru" else "Your blood pressure has dropped relative to previous measurements."

def rate_differ(data_pressure_this_week, data_pressure_last_week,
                                count_this_week, count_last_week, locale):
    mean_rate_this_week = round(
        data_pressure_this_week.aggregate(total=Sum('heart_rate_alone'))['total'] / count_this_week)
    mean_rate_last_week = round(
        data_pressure_last_week.aggregate(total=Sum('heart_rate_alone'))['total'] / count_last_week)
    if mean_rate_this_week > mean_rate_last_week:
        return "Ваше сердцебиение повысилось относительно предыдущих замеров." if locale=="ru" else "Your heart rate has increased relative to previous measurements."
    elif mean_rate_this_week < mean_rate_last_week:
        return "Ваше сердцебиение понизилось относительно предыдущих замеров." if locale=="ru" else "Your heart rate has dropped from previous measurements."
















