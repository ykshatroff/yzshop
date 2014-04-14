import logging
logger = logging.getLogger("default")


from django import http
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.views import redirect_to_login
from django.core.paginator import Paginator, EmptyPage, InvalidPage
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from django.template import RequestContext


from . import settings
from .filters import get_filtering_class
from .models import Category, Product
from .signals import product_viewed
from .utils import group_by_base_products


def catalog_view(request, template_name="catalog/index.html"):
    """
    The catalog index view
    use current catalog from request (see middleware)
    """

    top_categories = Category.get_top_categories()
    response = render_to_response(template_name, RequestContext(request, {
        "categories": top_categories,
    }))
    return response


def category_view(request, slug, page=None, template_name="catalog/category.html"):
    """
    The catalog category view
    """
    try:
        category = Category.objects.get_cached(slug=slug)
    except Category.DoesNotExist:
        raise http.Http404

    request.session['last_category_id'] = category.id

    # identify subcategories
    if settings.CATEGORIES_DISPLAY_HIERARCHY:
        subcategories = category.get_all_subcategories()
    else:
        subcategories = category.get_children()

    context = {
        'category': category,
        'subcategories': subcategories,
    }

    # identify products
    # -> whether any products are to be displayed
    # --> load all matching products (single and variants) from cache
    #       (this set will be required anyway to identify filters' options)
    # --> whether products are subject to filtering and sorting
    # --> if variants enabled, make the set of base products from the result
    # ---> try to load the (filtered and sorted) set from cache

    if settings.CATEGORIES_DISPLAY_ALL_PRODUCTS:
        products = category.get_all_products()
    elif settings.CATEGORIES_DISPLAY_PRODUCTS or not subcategories:
        products = category.get_products()
    else:
        products = None

    if products is not None:
        # products is a list of variants, not suitable for display yet
        try:
            cls = get_filtering_class()
        except ImportError:
            filtering = None
        else:
            filtering = cls(products, data=request.GET)
            products = filtering.apply()
        context['filters'] = filtering

        # sorting = get_sorting(request.GET)
        # context['sorting'] = sorting

        # now products var becomes the list of base products
        # products = Product.objects.find(category, filtering, sorting, deep=deep)

        products = group_by_base_products(products)  # list: [variants*]
        # to get available properties for a base product in template,
        # -> get_available_properties(variants)
        # caching makes no sense for filtered products: too many combinations
        # rather, cache the rendered template block of product-listentry, wrt md5(filters+sort...)

        items_per_page = settings.PRODUCTS_PER_PAGE
        if items_per_page > 0:
            # TODO allow external IPP definition ( e.g. ?items=40 )
            if page is None:
                # fallback to GET argument ?page=PAGE
                page = request.GET.get("page", 1)
            paginator = Paginator(products, items_per_page)
            try:
                page = paginator.page(page)
            except InvalidPage:
                products = None
            else:
                products = page.object_list
                context['page'] = page
                context['paginator'] = paginator
    context['products'] = products
    response = render_to_response(template_name, RequestContext(request, context))
    return response


def product_view(request, slug, template_name="catalog/product.html"):
    """
    The catalog product view
    """
    try:
        product = Product.objects.get_cached(slug=slug)
    except Product.DoesNotExist:
        raise http.Http404

    categories = product.get_categories()
    try:
        current_cat_id = request.session['last_category_id']
    except KeyError:
        current_category = categories[0]
    else:
        for cat in categories:
            if cat.id == current_cat_id:
                current_category = cat
                break
        else:
            current_category = categories[0]

    context = {
        'categories': categories,
        'category': current_category,
        'product': product,

    }

    if settings.VARIANTS_ENABLED:
        # determine the variant displayed by default
        if product.is_variant():
            context['current_variant'] = product
        else:
            context['current_variant'] = product.get_default_variant()
            #context.update(filter_variants(product, request.GET))

    product_viewed.send(product, request=request, context=context)

    response = render_to_response(template_name, RequestContext(request, context))
    return response


def search_view(request, template_name="catalog/search.html"):

    search_term = request.GET.get("q")
    page = None
    if search_term:
        products = Product.objects.search(search_term)
        if products:
            # try to paginate
            items_per_page = settings.PRODUCTS_PER_PAGE
            if items_per_page > 0:
                # allow external IPP definition ( e.g. ?items=40 )
                # fallback to GET argument ?page=PAGE
                page = request.GET.get("page", 1)
                paginator = Paginator(products, items_per_page)
                try:
                    page = paginator.page(page)
                except InvalidPage:
                    products = []
                else:
                    products = page.object_list
    else:
        products = None
    response = render_to_response(template_name, RequestContext(request, {
        'products': products,
        'page': page,
        'search_term': search_term,
    }))
    return response
