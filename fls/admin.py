from django.contrib import admin

# Register your models here.

from fls.models import Competition, Group, Param, ParamValue, Criterion, CriterionValue

admin.site.register(Competition)
admin.site.register(Group)
admin.site.register (Param)
admin.site.register(ParamValue)
admin.site.register(Criterion)
admin.site.register(CriterionValue)

