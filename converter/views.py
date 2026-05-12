from django.shortcuts import render

def converter_home (request):
    """Page principale du convertisseur de devises"""
    return render(request, 'converter/home.html')
