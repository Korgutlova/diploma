from django.contrib.auth.models import User
from django.db import models

METHOD_CHOICES = (
    (1, 'Ручная оценка'),
    (2, 'Взвешенное суммирование'),
    (3, 'Расчёт по формуле'),
)

ROLE_CHOICES = (
    (1, 'Участник'),
    (2, 'Жюри'),
    (3, 'Органзитор'),
)

STATUSES = (
    (1, 'Создание'),
    (2, 'Открыт'),
    (3, 'Оценивание'),
    (4, 'Закрыт'),
)

# добавить textarea?
TYPE_PARAM = (
    (1, 'NUMBER'),
    (2, 'TEXT'),
    (3, 'FILE'),
    (4, 'PHOTO'),
    (5, 'ENUM'),
    (6, 'LINK'),
)


class CustomUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='custom_user')
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

    def is_participant(self):
        return self.role == 1

    def is_jury(self):
        return self.role == 2

    def is_organizer(self):
        return self.role == 3


class Competition(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Название конкурса")

    description = models.TextField(verbose_name="Описание конкурса")

    method_of_estimate = models.IntegerField(choices=METHOD_CHOICES, blank=True, null=True,
                                             default=METHOD_CHOICES[0][0], verbose_name="Метод оценивания")
    status = models.IntegerField(choices=STATUSES, blank=True, null=True,
                                 default=STATUSES[0][0], verbose_name="Статус конкурса")
    organizer = models.ForeignKey(CustomUser, related_name='organizer_for_comp', on_delete=models.CASCADE,
                                  blank=True, null=True, verbose_name='Оранизатор конкурса')

    jurys = models.ManyToManyField("CustomUser", verbose_name="Жюри конкурса")

    max_for_criteria = models.IntegerField(default=10, verbose_name="Ограничение критериев")

    class Meta:
        unique_together = (('name', 'description'),)

    def __str__(self):
        return self.name

    def get_criteria(self):
        return self.competition_criterions.all().exclude(result_formula=True)

    def get_status(self):
        for r in STATUSES:
            if r[0] == self.status:
                return r[1]
        return "Не определено"

    def get_count(self):
        size = len(Request.objects.filter(competition=self))
        print(size)
        return size

    def not_exists_formula(self):
        return len(self.competition_criterions.all().exclude(formula=None)) == 0

    def get_next_criterion(self):
        criteria = self.competition_criterions.all().filter(formula=None, result_formula=False)
        if len(criteria) > 0:
            return criteria[0].id
        return -1


class Request(models.Model):
    competition = models.ForeignKey(Competition, related_name='competition_request', on_delete=models.CASCADE,
                                    blank=True, null=True, verbose_name='Конкурс')
    participant = models.ForeignKey(CustomUser, related_name='custom_user', on_delete=models.CASCADE,
                                    blank=True, null=True, verbose_name='Участник')
    result_value = models.FloatField(default=0)

    def __str__(self):
        return "Заявка %s - %s" % (self.participant, self.competition.name)


class CustomEnum(models.Model):
    competition = models.ForeignKey(Competition, related_name='competition_enums', on_delete=models.SET_NULL,
                                    blank=True, null=True)
    name = models.CharField(max_length=50)

    class Meta:
        unique_together = (('name', 'competition'),)

    def __str__(self):
        return "%s" % self.name

    def get_values(self):
        return self.values_for_enum.all()


class ValuesForEnum(models.Model):
    enum = models.ForeignKey(CustomEnum, related_name='values_for_enum', on_delete=models.CASCADE,
                             blank=True, null=True, verbose_name="Перечисление")
    enum_key = models.CharField(max_length=50)
    enum_value = models.FloatField(default=0)

    class Meta:
        unique_together = (('enum', 'enum_key', 'enum_value'),)

    def __str__(self):
        return "%s - %s" % (self.enum_key, self.enum_value)


class Criterion(models.Model):
    competition = models.ForeignKey(Competition, related_name='competition_criterions', on_delete=models.CASCADE,
                                    blank=True, null=True)
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True, null=True)
    max_for_jury = models.IntegerField(blank=True, null=True)
    formula = models.TextField(blank=True, null=True)

    # True - итоговая формула (указываются id критериев)
    # False - промежуточные формулы критериев (там будут указываться id сабпараметров)

    result_formula = models.BooleanField(default=False)

    # для взвешенного суммирования, если это не итоговый критерий
    weight_value = models.FloatField(null=True, blank=True)

    class Meta:
        unique_together = (('competition', 'name'),)

    def __str__(self):
        return "Конкурс %s - критерий %s" % (self.competition, self.name)


class Param(models.Model):
    criterion = models.ForeignKey(Criterion, related_name='param_criterion', on_delete=models.CASCADE,
                                  blank=False, null=False, verbose_name="Ссылка на параметр")
    name = models.CharField(max_length=50)
    # True - for formula
    # False - for jury

    for_formula = models.BooleanField()
    type = models.IntegerField(choices=TYPE_PARAM, null=False,
                               blank=False, default=TYPE_PARAM[0][0], verbose_name="Тип данных")
    enum = models.ForeignKey(CustomEnum, related_name='param_enum', on_delete=models.SET_NULL,
                             blank=True, null=True, verbose_name="Перечисление")

    max = models.IntegerField(blank=True, null=True)

    def __str__(self):
        return "Критерий %s - параметр критерия %s" % (self.criterion.name, self.name)


class ParamValue(models.Model):
    param = models.ForeignKey(Param, related_name='param_values', on_delete=models.CASCADE, blank=False,
                              null=False)
    request = models.ForeignKey(Request, related_name='request_param_values', on_delete=models.CASCADE, blank=False,
                                null=False)
    value = models.FloatField(default=0, blank=True, null=True)
    text = models.TextField(blank=True, null=True)
    enum_val = models.ForeignKey(ValuesForEnum, related_name='cur_value_enum_values', on_delete=models.SET_NULL,
                                 blank=True, null=True)

    class Meta:
        unique_together = (('param', 'request'),)

    def __str__(self):
        return "%s - %s - %s" % (self.request.participant, self.param.name, self.value)

    def is_number(self):
        return self.param.type == 1

    def is_file(self):
        return self.param.type == 3

    def is_photo(self):
        return self.param.type == 4

    def is_enum(self):
        return self.param.type == 5

    def get_name(self):
        return self.param.name

    def get_files(self):
        return self.files.all()


class UploadData(models.Model):
    sub_param_value = models.ForeignKey(ParamValue, related_name="files", on_delete=models.CASCADE, blank=False,
                                        null=False)
    header_for_file = models.CharField(max_length=100, null=True, blank=True)
    image = models.ImageField()

    def __str__(self):
        return '%s - %s - %s' % (self.sub_param_value.param.name, self.header_for_file, self.image.url)


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
    type = models.IntegerField(choices=METHOD_CHOICES[:2], default=METHOD_CHOICES[0][0], null=True,
                               blank=True, verbose_name='Тип оценивания')
    request = models.ForeignKey(Request, related_name='request_jury_values', on_delete=models.CASCADE, blank=False,
                                null=False)
    jury = models.ForeignKey(CustomUser, related_name='jury_values', on_delete=models.CASCADE,
                             blank=True, null=True, verbose_name='Жюри')
    criterion = models.ForeignKey(Criterion, related_name='criterion_value_for_request', on_delete=models.CASCADE,
                                  blank=False,
                                  null=False)
    value = models.FloatField(default=0)

    class Meta:
        unique_together = (('jury', 'request', 'type', 'criterion'),)

    def __str__(self):
        return "%s - %s - %s" % (self.jury, self.request, self.type)


class WeightParamJury(models.Model):
    param = models.ForeignKey(Param, related_name='param_weights', on_delete=models.CASCADE, blank=False,
                              null=False)
    jury = models.ForeignKey(CustomUser, related_name='jury_param_weights', on_delete=models.CASCADE,
                             blank=True, null=True, verbose_name='Жюри')

    weight_value = models.FloatField(default=0)

    class Meta:
        unique_together = (('jury', 'param'),)

    def __str__(self):
        return "Жюри %s - Параметр %s" % (self.jury, self.param)


class ClusterNumber(models.Model):
    criterion = models.ForeignKey(Criterion, related_name='criterion_ks', on_delete=models.CASCADE, blank=False,
                                  null=False)
    type = models.IntegerField(choices=METHOD_CHOICES[:2], default=METHOD_CHOICES[0][0], null=True,
                               blank=True, verbose_name='Тип оценивания')
    k_number = models.IntegerField(default=1)

    class Meta:
        unique_together = (('criterion', 'type', 'k_number'),)

    def __str__(self):
        return "Критерий %s - Тип %s - %s" % (self.criterion, self.type, self.k_number)
