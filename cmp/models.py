from django.db import models


# Create your models here.


class Weights(models.Model):
    weights = models.TextField()
    deviations_sum = models.FloatField()
