from django.core.validators import MinValueValidator

class MinValidatorUniversal(MinValueValidator):
    def compare(self, a, b):
        if a == 0:
            return a < -1
        else:
            return a < b







