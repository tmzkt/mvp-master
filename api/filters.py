from cms.models import Disease, Result

def user_recomendations(request):
    bmi = Result.objects.filter(pk=request.user.health_data.result.id).first()
    cat = []
    if not bmi.bmi:
        list = []
    elif bmi.bmi < 18.5:
        list = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
        cat.append(8)
    elif bmi.bmi < 25:
        list = [12, 13, 14, 4, 5, 15, 8, 16, 7, 17, 11]
        cat.append(9)
    elif bmi.bmi >= 25:
        list = [12, 18, 19, 20, 21, 22, 23, 24, 25, 8, 16, 26, 27, 5, 28, 11]
        cat.append(10)

    return (list, cat)


def cardio_recomendations(request):
    result = Disease.objects.filter(user=request.user).first()
    cat_yes = []
    cat_not = []
    list = []
    if result:
        if result.disease_blood_pressure:
            if result.disease_blood_pressure == 1:
                cat_yes.append(3)
                list.append(11)
            elif result.disease_blood_pressure in [2, 3, 4, 5, 6]:
                cat_yes.append(2)
                cat_not.append(7)
                list.append(11)
        elif result.risk_disease_blood_pressure:
            if result.risk_disease_blood_pressure == 1:
                list.append(11)
                cat_yes.append(3)
            elif result.risk_disease_blood_pressure == 3:
                cat_yes.append(2)
                cat_not.append(7)
                list.append(11)

        if result.disease_heart_rate:
            if result.disease_heart_rate == 1:
                cat_yes.append(4)
            elif result.disease_heart_rate == 2:
                cat_yes.append(5)
            elif result.disease_heart_rate == 3:
                cat_yes.append(6)
        elif result.risk_disease_heart_rate:
            if result.risk_disease_heart_rate == 1:
                cat_yes.append(4)
            elif result.risk_disease_heart_rate == 2:
                cat_yes.append(5)

    return (cat_yes, list, cat_not)