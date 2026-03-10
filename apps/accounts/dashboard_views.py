from django.shortcuts import render


def login_view(request):
    return render(request, 'dashboard/login.html')


def dashboard_view(request):
    return render(request, 'dashboard/index.html')


def campaign_list_view(request):
    return render(request, 'dashboard/campaigns.html')


def campaign_detail_view(request, campaign_id):
    return render(request, 'dashboard/campaign_detail.html')
