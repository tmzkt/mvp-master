from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .models import Product


def products_list(request):
    products = Product.objects.filter(available=True)
    paginator = Paginator(products, 3)
    page = request.GET.get('page')
    try:
        products = paginator.page(page)
    except PageNotAnInteger:
        products = paginator.page(1)
    except EmptyPage:
        products = paginator.page(paginator.num_pages)

    return render(request, 'shop/list.html',
                  {'page': page, 'products': products})


def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)

    return render(request, 'shop/detail.html',
                  {'product': product})


