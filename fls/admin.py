from django.contrib import admin

# Register your models here.

from fls.models import Competition, Group, Param, ParamValue, Criterion, CriterionValue, CustomUser, Request, \
    EstimationJury, CalcEstimationJury, WeightParamJury

admin.site.register(Competition)
admin.site.register(Group)
admin.site.register(Param)
admin.site.register(ParamValue)
admin.site.register(Criterion)
admin.site.register(CriterionValue)
admin.site.register(CustomUser)
admin.site.register(Request)
admin.site.register(EstimationJury)
admin.site.register(CalcEstimationJury)
admin.site.register(WeightParamJury)
