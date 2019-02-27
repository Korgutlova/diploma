from django.db import models


# Create your models here.

class Competition(models.Model):
    name = models.CharField(max_length=40)
    description = models.TextField()




YEAR_CHOICES = (
    (1, '1'),
    (2, '2'),
    (3, '3'),
    (4, '4'),
    (5, '1(магистратура)'),
    (6, '2(магистратура)'),
)


class Group(models.Model):
    year_of_study = models.IntegerField(choices=YEAR_CHOICES)
    faculty = models.CharField(max_length=50)
    person_number = models.IntegerField()
    name = models.CharField(max_length=10)

class Param(models.Model):
    competition = models.ForeignKey(Competition, on_delete=models.CASCADE, blank=False, null=False)
    name = models.CharField(max_length=30)
    max = models.IntegerField()
    min = models.IntegerField()

class ParamValue(models.Model):
    param = models.ForeignKey(Param, on_delete=models.CASCADE, blank=False, null=False)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, blank=False, null=False)
    value = models.FloatField()
    person_count = models.IntegerField()

    class Meta:
        unique_together = (('param', 'group'),)

class Criterion(models.Model):
    name = models.CharField(max_length=20)
    formula = models.TextField()
    params = models.ManyToManyField(Param)

class CriterionValue(models.Model):
    criterion = models.ForeignKey(Criterion, on_delete=models.CASCADE, blank=False, null=False)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, blank=False, null=False)
    value = models.FloatField()

    class Meta:
        unique_together = (('criterion', 'group'),)

