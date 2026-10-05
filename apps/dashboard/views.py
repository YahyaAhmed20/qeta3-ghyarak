from django.shortcuts import render


def seller_dashboard_view(request):
    return render(
        request,
        "dashboard/seller/overview.html",
    )


def seller_login_view(request):
    return render(
        request,
        "auth/seller_login.html",
    )
    
    
def seller_products_view(request):
    return render(
        request,
        "dashboard/seller/products.html",
    )