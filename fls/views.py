from django.shortcuts import render, redirect

from fls.forms import CompetitionForm
from fls.models import Param, Competition, Criterion, Group, ParamValue


def criteria(request, id):
    comp = Competition.objects.get(id=id)
    params = Param.objects.filter(competition=comp)
    if request.method == "POST":
        c = Criterion(name=request.POST["name"], formula=request.POST["formula"], competition=comp)
        c.save()
        return redirect("fls:list_comp")
    return render(request, 'fls/add_criteria.html', {"params": params, "id": id})


def comp(request):
    form = CompetitionForm()
    if request.method == 'POST':
        form = CompetitionForm(request.POST)
        if form.is_valid():
            comp = form.save()

            for text, desc, min, max in zip(request.POST.getlist('text'), request.POST.getlist('description'),
                                            request.POST.getlist('max')):
                Param.objects.create(name=text, description=desc, max=max, competition=comp)
            return redirect("fls:list_comp")

    return render(request, 'fls/add_comp.html', {"form": form})


def list_comp(request):
    comps = Competition.objects.all()
    return render(request, 'fls/list_comp.html', {"comps": comps})


def load_request(request, comp_id):
    comp = Competition.objects.get(id=comp_id)
    params = Param.objects.filter(competition=comp)
    groups = Group.objects.all()
    if request.method == 'POST':
        print(request.POST)
        # needed_group = groups.get(id=request.POST["group"])
        # for p in params:
        #     pv = ParamValue(group=needed_group, param=p, value=request.POST["value_%s" % p.id],
        #                     person_count=request.POST["person_%s" % p.id])
        #     pv.save()
        # print("saving")
    return render(request, 'fls/load_request.html', {"params": params, "comp": comp, "groups": groups})


def process_request(request):
    # взять необходимые параметры
    # сопоставить соответсвующим значениям -> получить массив value
    # для всех критериев данного конкурса вычилисть значения  и каждый соотвественно сохранить
    pass
