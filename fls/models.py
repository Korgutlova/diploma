from django.db import models


# Create your models here.

YEAR_CHOICES = (
    (1, '1'),
    (2, '2'),
    (3, '3'),
    (4, '4'),
    (5, '1(магистратура)'),
    (6, '2(магистратура)'),
)

class Competition(models.Model):
    name = models.CharField(max_length=40, unique=True)
    year_of_study = models.IntegerField(choices=YEAR_CHOICES, blank=True, null=True)
    description = models.TextField()


    class Meta:
        unique_together = (('name', 'description'),)



class Group(models.Model):
    year_of_study = models.IntegerField(choices=YEAR_CHOICES)
    faculty = models.CharField(max_length=50)
    person_number = models.IntegerField()
    name = models.CharField(max_length=10, unique=True)


class Param(models.Model):
    competition = models.ForeignKey(Competition, related_name='competition_params', on_delete=models.CASCADE,
                                    blank=True, null=True)
    name = models.CharField(max_length=30)
    description = models.TextField()
    max = models.IntegerField()
    min = models.IntegerField()

    class Meta:
        unique_together = (('name', 'description'),)


class ParamValue(models.Model):
    param = models.ForeignKey(Param, related_name='param_values', on_delete=models.CASCADE, blank=False, null=False)
    group = models.ForeignKey(Group, related_name='group_param_values', on_delete=models.CASCADE, blank=False,
                              null=False)
    value = models.FloatField(default=0)
    person_count = models.IntegerField()

    class Meta:
        unique_together = (('param', 'group'),)


class Criterion(models.Model):
    competition = models.ForeignKey(Competition, related_name='competition_criterions', on_delete=models.CASCADE,
                                    blank=True, null=True)
    name = models.CharField(max_length=20, unique=True)
    formula = models.TextField()


class CriterionValue(models.Model):

    criterion = models.ForeignKey(Criterion, related_name='criterion_values', on_delete=models.CASCADE, blank=False,
                                  null=False)
    group = models.ForeignKey(Group, related_name='group_criterion_values', on_delete=models.CASCADE, blank=False,
                              null=False)
    value = models.FloatField(default=0)

    class Meta:
        unique_together = (('criterion', 'group'),)
