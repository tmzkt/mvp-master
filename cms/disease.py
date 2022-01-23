from django.utils.translation import gettext_lazy as _


RELATED_TO_BLOOD_PRESSURE = (
    (0, '-----'),
    (1, _('arterial hypotension')),
    (2, _('arterial hypertension of the 1st degree')),
    (3, _('arterial hypertension of the 2st degree')),
    (4, _('arterial hypertension of the 3st degree')),
    (5, _('borderline arterial hypertension')),
    (6, _('isolated systolic hypertension')),
)

RELATED_TO_HEART_RATE = (
    (0, '-----'),
    (1, _('bradicardia')),
    (2, _('tachycardia')),
    (3, _('arrhythmia')),
)

RELATED_TO_EATING_DISORDERS = (
    (0, '-----'),
    (1, _('obesity of the 1st degree')),
    (2, _('obesity of the 2st degree')),
    (3, _('obesity of the 3st degree')),
)