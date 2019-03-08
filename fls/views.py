from django.http import HttpResponseRedirect as redirect
from django.shortcuts import render

from fls.forms import CompetitionForm
from fls.models import Param, Competition


def criteria(request, id):
    comp = Competition.objects.get(id=id)
    params = Param.objects.filter(competition=comp)
    return render(request, 'fls/add_criteria.html', {"params": params, "id": id})


def comp(request):
    form = CompetitionForm()
    if request.method == 'POST':
        form = CompetitionForm(request.POST)
        if form.is_valid():
            comp = form.save()

            for text, desc, min, max in zip(request.POST.getlist('text'), request.POST.getlist('description'),
                                            request.POST.getlist('min'),
                                            request.POST.getlist('max')):
                Param.objects.create(name=text, description=desc, min=min, max=max, competition=comp)
            return redirect("list_comp")

    return render(request, 'fls/add_comp.html', {"form": form})


def list_comp(request):
    comps = Competition.objects.all()
    return render(request, 'fls/list_comp.html', {"comps": comps})
