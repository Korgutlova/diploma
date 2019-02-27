from django.shortcuts import render


def params(request):
    return render(request, 'fls/add_params.html', {})
