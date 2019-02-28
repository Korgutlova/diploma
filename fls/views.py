from django.shortcuts import render

from fls.models import Param


def params(request):
    if request.method == 'POST':
        for text, desc, min, max in zip(request.POST['text'], request.POST['description'], request.POST['min'],
                                        request.POST['max']):
            Param.objects.create(name=text, description=desc, min=min, max=max)
    return render(request, 'fls/add_params.html', {})
