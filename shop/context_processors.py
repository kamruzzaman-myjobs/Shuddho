from .models import Cart
from .models import Category
from django.conf import settings


def cart_items_count(request):
    count = 0

    try:
        if request.user.is_authenticated:
            cart = Cart.objects.filter(user=request.user).first()
        else:
            session_key = request.session.session_key
            if not session_key:
                request.session.create()
                session_key = request.session.session_key
            cart = Cart.objects.filter(session_key=session_key).first()

        if cart:
            count = cart.items.count()
    except Exception:
        count = 0

    return {
        'cart_items_count': count
    }




def category_menu(request):
    top_categories = Category.objects.filter(parent=None).prefetch_related(
        'children__children'
    )
    return {'menu_categories': top_categories}




def meta_pixel(request):
    return {'META_PIXEL_ID': settings.META_PIXEL_ID}