from django.contrib.auth.models import User
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

METHOD_CHOICES = (
    (1, 'Окончательная (абсолютная) оценка заявки'),
    (2, 'Попарное сравнение заявок'),
    (3, 'Попарные сравнения параметров'),
    (4, 'Ранжирование параметров'),
    (5, 'Автоматически'),
)

ROLE_CHOICES = (
    (1, 'Участник'),
    (2, 'Жюри'),
    (3, 'Эксперт-организатор'),
    (4, 'Эксперт оценок жюри'),
)


class Competition(models.Model):
    # можно еще тут указать поле, групповой или же единичный (на одного человека) конкурс
    name = models.CharField(max_length=100, unique=True, verbose_name="Название")
    year_of_study = models.IntegerField(choices=YEAR_CHOICES, blank=True, null=True, default=YEAR_CHOICES[0][0],
                                        verbose_name="Курс")
    description = models.TextField(verbose_name="Описание конкурса")
    # либо это, либо types в Estimation/Weight
    method_of_estimate = models.IntegerField(choices=METHOD_CHOICES, blank=True, null=True,
                                             default=METHOD_CHOICES[0][0], verbose_name="Метод оценивания")

    class Meta:
        unique_together = (('name', 'description'),)

    def __str__(self):
        return self.name


class Group(models.Model):
    year_of_study = models.IntegerField(choices=YEAR_CHOICES)
    faculty = models.CharField(max_length=50)
    person_number = models.IntegerField()
    name = models.CharField(max_length=10, unique=True)

    def __str__(self):
        return self.name


class CustomUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='custom_user')
    # exists if role=participant
    group = models.ForeignKey(Group, related_name="current_group", on_delete=models.SET_NULL,
                              blank=True, null=True, verbose_name="Группа участника")
    role = models.IntegerField(choices=ROLE_CHOICES, blank=True, null=True, default=ROLE_CHOICES[0][0],
                               verbose_name="Роль")

    def __str__(self):
        return self.user.username

    def get_username(self):
        return self.user.username

    def get_role(self):
        for r in ROLE_CHOICES:
            if r[0] == self.role:
                return r[1]
        return "Анонимус"


class Request(models.Model):
    competition = models.ForeignKey(Competition, related_name='competition_request', on_delete=models.CASCADE,
                                    blank=True, null=True, verbose_name='Конкурс')
    participant = models.ForeignKey(CustomUser, related_name='custom_user', on_delete=models.CASCADE,
                                    blank=True, null=True, verbose_name='Участник')

    # rang = models.IntegerField(default=0)
    # result_value = models.FloatField(default=0)

    def __str__(self):
        return "Заявка %s - %s" % (self.participant.group, self.competition.name)


class RequestEstimation(models.Model):
    request = models.ForeignKey(Request, related_name='request_values', on_delete=models.CASCADE, blank=False,
                                null=False)
    type = models.IntegerField(choices=METHOD_CHOICES[:4], default=METHOD_CHOICES[0][0], null=False,
                               blank=False, verbose_name='Тип оценивания')
    value = models.FloatField()
    rank = models.IntegerField(null=True, blank=True)

    # для различных формул объединения жюри в случае методов 1,2
    jury_formula = models.ForeignKey('CalcEstimationJury', related_name='formula_request_values', null=True, blank=True,
                                     on_delete=models.CASCADE)

    class Meta:
        unique_together = (('request', 'type', 'jury_formula'),)


class Param(models.Model):
    competition = models.ForeignKey(Competition, related_name='competition_params', on_delete=models.CASCADE,
                                    blank=True, null=True)
    name = models.CharField(max_length=30)
    description = models.TextField()
    max = models.IntegerField()

    # result_weight = models.FloatField(default=0)

    class Meta:
        unique_together = (('name', 'description'),)

    def __str__(self):
        return self.name


class ParamResultWeight(models.Model):
    param = models.ForeignKey(Param, related_name='param_weights', on_delete=models.CASCADE,
                              blank=False, null=False)
    type = models.IntegerField(choices=METHOD_CHOICES[2:4], default=METHOD_CHOICES[2][0], null=False,
                               blank=False, verbose_name='Тип оценивания')
    weight_value = models.FloatField(default=0)

    class Meta:
        unique_together = (('param', 'type'),)

    def __str__(self):
        return '%s - %s' % (self.param, self.type)


class ParamValue(models.Model):
    param = models.ForeignKey(Param, related_name='param_values', on_delete=models.CASCADE, blank=False, null=False)
    request = models.ForeignKey(Request, related_name='request_param_values', on_delete=models.CASCADE, blank=False,
                                null=False)
    value = models.FloatField(default=0)
    person_count = models.IntegerField()

    class Meta:
        unique_together = (('param', 'request'),)

    def __str__(self):
        return "%s - %s" % (self.param.name, self.value)


class Criterion(models.Model):
    competition = models.ForeignKey(Competition, related_name='competition_criterions', on_delete=models.CASCADE,
                                    blank=True, null=True)
    name = models.CharField(max_length=20, unique=True)
    formula = models.TextField()

    def __str__(self):
        return self.name


class CriterionValue(models.Model):
    criterion = models.ForeignKey(Criterion, related_name='criterion_values', on_delete=models.CASCADE, blank=False,
                                  null=False)
    request = models.ForeignKey(Request, related_name='request_criterion_values', on_delete=models.CASCADE, blank=False,
                                null=False)
    value = models.FloatField(default=0)

    class Meta:
        unique_together = (('criterion', 'request'),)

    def __str__(self):
        return "%s - %s" % (self.criterion.name, self.value)


class EstimationJury(models.Model):
    # method_choices[:4], значения последнего типа в criterion_value
    # пока пусть null
    type = models.IntegerField(choices=METHOD_CHOICES[:4], default=METHOD_CHOICES[0][0], null=True,
                               blank=True, verbose_name='Тип оценивания')
    request = models.ForeignKey(Request, related_name='request_jury_values', on_delete=models.CASCADE, blank=False,
                                null=False)
    jury = models.ForeignKey(CustomUser, related_name='jury_values', on_delete=models.CASCADE,
                             blank=True, null=True, verbose_name='Жюри')

    value = models.FloatField(default=0)

    class Meta:
        unique_together = (('jury', 'request', 'type'),)

    def __str__(self):
        return "%s - %s - %s" % (self.jury, self.request, self.type)


class WeightParamJury(models.Model):
    type = models.IntegerField(choices=METHOD_CHOICES[2:4], default=METHOD_CHOICES[2][0], null=True,
                               blank=True, verbose_name='Тип оценивания')
    param = models.ForeignKey(Param, related_name='param_for_jury', on_delete=models.CASCADE, blank=False, null=False)
    jury = models.ForeignKey(CustomUser, related_name='jury2', on_delete=models.CASCADE,
                             blank=True, null=True, verbose_name='Жюри')

    # это ранг или попарные в зависимости от метода
    value = models.FloatField(default=0)

    class Meta:
        unique_together = (('jury', 'param', 'type'),)

    def __str__(self):
        return "Жюри %s - Параметр %s - Тип %s" % (self.jury, self.param, self.type)


class CalcEstimationJury(models.Model):
    expert = models.ForeignKey(CustomUser, related_name='experts', on_delete=models.CASCADE,
                               blank=True, null=True, verbose_name='Эксперт')
    competition = models.ForeignKey(Competition, related_name='competition_formula_for_jury', on_delete=models.CASCADE,
                                    blank=True, null=True)
    name = models.CharField(max_length=20, unique=True)

    formula = models.TextField()

    # для попарных или рнажированных методов
    param = models.ForeignKey(Param, related_name='param_for_formula_jury', on_delete=models.SET_NULL, blank=True,
                              null=True)

    def __str__(self):
        return self.name
