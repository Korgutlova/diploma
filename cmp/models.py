from django.db import models

# Create your models here.

TYPES = (
    ('kfavg', 'KF+AVG'),
    ('kf', 'KF'),
    ('avg', 'AVG'),
    ('c', 'COUNT')
)


class Weights(models.Model):
    weights = models.TextField()
    deviations_sum = models.FloatField()
    type = models.CharField(choices=TYPES, default=TYPES[0][0], max_length=10)

class GroupWeights(models.Model):
    group_name = models.CharField(max_length=30)
    weights = models.TextField()
    deviations_sum = models.FloatField()
    type = models.CharField(choices=TYPES, max_length=10)
