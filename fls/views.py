from django.shortcuts import render

from fls.models import Param


def params(request):
    if request.method == 'POST':
        print(request.POST.getlist('text'))
        for text, desc, min, max in zip(request.POST.getlist('text'), request.POST.getlist('description'), request.POST.getlist('min'),
                                        request.POST.getlist('max')):
            Param.objects.create(name=text, description=desc, min=min, max=max)
    return render(request, 'fls/add_params.html', {})
