from datetime import timedelta
from django.utils import timezone
from django.db import models
from django.contrib.auth import get_user_model
from cms.models import HealthData


User = get_user_model()

class Payment(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    create = models.DateTimeField(auto_now_add=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=100)
    payment_amount = models.DecimalField(decimal_places=2, max_digits=10)
    summa = models.DecimalField(max_digits=10, decimal_places=2, blank=True, default=0, editable=False)
    end_date = models.DateTimeField(blank=True, editable=False, default=timezone.now)

    def __str__(self):
        return self.user.email

    def save(self, *args, **kwargs):
        self.summa += self.payment_amount
        payment_days = int((self.payment_amount // self.price) * 30)
        end_trial_period = HealthData.objects.get(user=self.user).create + timedelta(days=30)
        if self.end_date > end_trial_period:
            self.end_date += timedelta(days=payment_days)
        else:
            self.end_date = end_trial_period + timedelta(days=payment_days)

        super(Payment, self).save(*args, **kwargs)












