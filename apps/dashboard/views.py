from django.shortcuts import render


def seller_dashboard_view(request):
    return render(
        request,
        "dashboard/seller/overview.html",
    )