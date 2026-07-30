from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.http import JsonResponse
from .forms import RegistrationForm, RatingForm, CheckoutForm, ProfileUpdateForm
from .models import Category, Product, Cart, CartItem, Rating, Order, OrderItem
from django.db.models import Q, Min, Max, Avg
from django.contrib.auth.decorators import login_required
from .sslcommerz import generate_sslcommerz_payment, send_order_confirmation_email
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from .sslcommerz import validate_sslcommerz_payment 
from django.core.paginator import Paginator



# Manual User Authentication
def register_view(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            user = authenticate(
                request,
                username = user.username,
                password = form.cleaned_data['password1']
            )
            login(request, user)
            messages.success(request, "Registration Successful!")
            return redirect('profile')
    else:
        form = RegistrationForm()
    
    return render(request, 'shop/register.html', {'form' : form})



def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, "Logged In Successful!")
            return redirect('profile')
        else:
            messages.error(request, "Invalid username or password") 
    return render(request, 'shop/login.html')




def logout_view(request):
    logout(request)
    return redirect('login')



from django.utils import timezone
from .models import Category, Product, Cart, CartItem, Rating, Order, OrderItem, PromoBanner
def home(request):
    featured_products = Product.objects.filter(available=True).order_by('-created_at')[:8]
    categories = Category.objects.filter(parent=None)
    promo_banners = PromoBanner.objects.filter(is_active=True)

    # Flash Sale products — active, not-yet-ended
    flash_sale_products = Product.objects.filter(
        available=True,
        is_flash_sale=True,
        flash_sale_end__gt=timezone.now()
    ).order_by('flash_sale_end')[:7]

    # Earliest countdown end time — the JS timer counts down to this
    flash_sale_end_time = None
    if flash_sale_products.exists():
        flash_sale_end_time = flash_sale_products.first().flash_sale_end

    # Category-wise product sections (Food, Home & Kitchen, Beauty & Health, etc.)
    category_sections = []
    for cat in categories:
        cat_ids = cat.get_all_children_ids()
        cat_products = Product.objects.filter(
            available=True, category_id__in=cat_ids
        ).order_by('-created_at')[:7]

        if cat_products.exists():
            category_sections.append({
                'category': cat,
                'products': cat_products,
            })

    return render(request, 'shop/home.html', {
        'featured_products': featured_products,
        'categories': categories,
        'promo_banners': promo_banners,
        'category_sections': category_sections,
        'flash_sale_products': flash_sale_products,
        'flash_sale_end_time': flash_sale_end_time,
    })
    











# product list page
# def product_list(request, category_slug = None):
#     category = None 
#     categories = Category.objects.filter(parent=None)  # sidebar-এ top-level দেখাবে
#     products = Product.objects.filter(available=True)
    
#     if category_slug:
#         category = get_object_or_404(Category, slug=category_slug)
#         category_ids = category.get_all_children_ids()   # নিজে + সব সন্তান
#         products = products.filter(category_id__in=category_ids)
        
#     min_price = products.aggregate(Min('price'))['price__min']
#     max_price = products.aggregate(Max('price'))['price__max']
    
#     if request.GET.get('min_price'):
#         products = products.filter(price__gte=request.GET.get('min_price'))
    
#     if request.GET.get('max_price'):
#         products = products.filter(price__lte=request.GET.get('max_price'))
    
#     if request.GET.get('rating'):
#         min_rating = request.GET.get('rating')
#         products = products.annotate(avg_rating = Avg('ratings__rating')).filter(avg_rating__gte=min_rating)
#         # temp variable --> avg_rating
#         # Avg
#         # ratings related_name ke use kore rating model er rating value ke access korlam
#         # avg_rating == user er filter kora rating er sathe
        
    
#     if request.GET.get('search'):
#         query = request.GET.get('search')
#         products = products.filter(
#             Q(name__icontains = query) | 
#             Q(description__icontains = query) | 
#             Q(category__name__icontains = query)  
#         )
    
#     return render(request, 'shop/product_list.html', {
#         'category' : category,
#         'categories' : categories,
#         'products' : products,
#         'min_price' : min_price,
#         'max_price' : max_price
#     })





def product_list(request, category_slug=None):
    category = None
    categories = Category.objects.filter(parent=None)
    products = Product.objects.filter(available=True)

    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        category_ids = category.get_all_children_ids()
        products = products.filter(category_id__in=category_ids)

    min_price = products.aggregate(Min('price'))['price__min']
    max_price = products.aggregate(Max('price'))['price__max']

    if request.GET.get('min_price'):
        products = products.filter(price__gte=request.GET.get('min_price'))

    if request.GET.get('max_price'):
        products = products.filter(price__lte=request.GET.get('max_price'))

    if request.GET.get('rating'):
        min_rating = request.GET.get('rating')
        products = products.annotate(avg_rating=Avg('ratings__rating')).filter(avg_rating__gte=min_rating)

    if request.GET.get('in_stock'):
        products = products.filter(stock__gt=0)

    if request.GET.get('search'):
        query = request.GET.get('search')
        products = products.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(category__name__icontains=query)
        )

    # ---------- Sorting ----------
    sort = request.GET.get('sort', 'newest')
    sort_map = {
        'newest': '-created_at',
        'price_low': 'price',
        'price_high': '-price',
        'name_asc': 'name',
    }

    needs_avg_rating = request.GET.get('rating') or sort == 'rating'
    if needs_avg_rating:
        products = products.annotate(avg_rating=Avg('ratings__rating'))

    if request.GET.get('rating'):
        min_rating = request.GET.get('rating')
        products = products.filter(avg_rating__gte=min_rating)

    if sort == 'rating':
        products = products.order_by('-avg_rating')
    else:
        products = products.order_by(sort_map.get(sort, '-created_at'))

    # ---------- Pagination ----------
    paginator = Paginator(products, 20)   # প্রতি পেজে ২০টা প্রোডাক্ট
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'shop/product_list.html', {
        'category': category,
        'categories': categories,
        'products': page_obj,
        'page_obj': page_obj,
        'min_price': min_price,
        'max_price': max_price,
        'current_sort': sort,
    })







# product detail page
def product_detail(request, slug):
    product = get_object_or_404(Product.objects.select_related('category'), slug = slug, available = True)
    related_products = Product.objects.filter(category = product.category).exclude(id=product.id)
    
    user_rating = None 
    
    if request.user.is_authenticated:
        try:
            user_rating = Rating.objects.get(product=product, user=request.user)
        except Rating.DoesNotExist:
            pass 
        
    rating_form = RatingForm(instance=user_rating)
    
    return render(request, 'shop/product_detail.html', {
        'product' :product,
        'related_products' : related_products,
        'user_rating' : user_rating,
        'rating_form' : rating_form
    })




def buy_now(request, product_id):
    product = get_object_or_404(Product, id=product_id, available=True)
    cart = get_cart(request)

    if product.stock < 1:
        messages.warning(request, "Out of stock!")
        return redirect('product_detail', slug=product.slug)

    cart_item, created = CartItem.objects.get_or_create(
        cart=cart, product=product, defaults={'quantity': 1}
    )
    if not created and cart_item.quantity < product.stock:
        cart_item.quantity += 1
        cart_item.save()

    return redirect('checkout')





# Rate Product 
# logged in user, Purchase koreche kina
@login_required
def rate_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    ordered_items = OrderItem.objects.filter(
        order__user = request.user,
        product = product,
        order__paid = True
    )
    
    if not ordered_items.exists(): # order kore nai
        messages.warning(request, 'You can only rate products you have purchased!')
        return redirect('product_detail', slug=product.slug)
    
    try:
        rating = Rating.objects.get(product=product, user = request.user)
    except Rating.DoesNotExist:
        rating = None 
    
    # jodi rating age diye thake tail rating form ager rating data diye fill up kora thakbe sekhtre instance = user rating hoye jbe
    # jodi rating na kora thake taile instance = None thakbe and se new rating create korte parbe
    if request.method == 'POST':
        form = RatingForm(request.POST, instance = rating) 
        if form.is_valid():
            rating = form.save(commit=False)
            rating.product = product
            rating.user = request.user 
            rating.save()
            return redirect('product_detail', slug=product.slug)
    else:
        form = RatingForm(instance=rating)
    
    return render(request, 'shop/rate_product.html', {
        'form' : form,
        'product' : product
    })

# Everything about cart - feature
# cart detail --> temporary order - ok
# cart e item add - ok
# cart e item remove - ok
# cart e item update - ok
# checkout - ok


def get_cart(request):
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
    else:
        if not request.session.session_key:
            request.session.create()
        cart, _ = Cart.objects.get_or_create(
            session_key=request.session.session_key,
            user=None
        )
    return cart


def cart_detail(request):
    cart = get_cart(request)
    return render(request, 'shop/cart.html', {'cart' : cart})



def cart_add(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = get_cart(request)

    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'

    try:
        cart_item = CartItem.objects.get(cart=cart, product=product)

        if cart_item.quantity + 1 > product.stock:
            if is_ajax:
                return JsonResponse({'success': False, 'message': 'Stock limit reached!'})
            messages.warning(request, "Stock limit reached!")
            return redirect('product_detail', slug=product.slug)

        cart_item.quantity += 1
        cart_item.save()

    except CartItem.DoesNotExist:
        if product.stock < 1:
            if is_ajax:
                return JsonResponse({'success': False, 'message': 'Out of stock!'})
            messages.warning(request, "Out of stock!")
            return redirect('product_detail', slug=product.slug)
        CartItem.objects.create(cart=cart, product=product, quantity=1)

    if is_ajax:
        return JsonResponse({
            'success': True,
            'message': f'{product.name} added to cart!',
            'cart_total_items': cart.get_total_items(),
        })

    messages.success(request, f"{product.name} has been added to your cart!")
    return redirect('product_detail', slug=product.slug)
    


# cart Update
# cart item quantity increase/decrease korte parbo
def cart_update(request, product_id):
    cart = get_cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart_item = get_object_or_404(CartItem, cart=cart, product=product)

    try:
        quantity = int(request.POST.get('quantity', 1))
    except (TypeError, ValueError):
        quantity = 1

    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'

    if quantity > product.stock:
        if not is_ajax:
            messages.warning(request, f'Only {product.stock} units available in stock!')
        quantity = product.stock

    removed = False
    if quantity <= 0:
        cart_item.delete()
        if not is_ajax:
            messages.success(request, f"{product.name} has been removed from your cart!")
        removed = True
    else:
        cart_item.quantity = quantity
        cart_item.save()
        if not is_ajax:
            messages.success(request, "Cart updated successfully!")

    if is_ajax:
        return JsonResponse({
            'success': True,
            'removed': removed,
            'item_quantity': 0 if removed else cart_item.quantity,
            'item_total': 0 if removed else float(cart_item.get_cost()),
            'cart_total_items': cart.get_total_items(),
            'cart_subtotal': float(cart.get_total_price()),
            'grand_total': float(cart.get_total_price()) + 80,
        })

    return redirect('cart_detail')



def cart_remove(request, product_id):
    cart = get_cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart_item = get_object_or_404(CartItem, cart=cart, product=product)

    cart_item.delete()
    messages.success(request, f"{product.name} has been removed from your cart!")
    return redirect("cart_detail")

# 80% --> thinking
# 20% time --> coding



def checkout(request):
    cart = get_cart(request)
    if not cart.items.exists():
        messages.warning(request, 'Your cart is empty!')
        return redirect('cart_detail')

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        payment_method = request.POST.get('payment_method')

        if form.is_valid():
            order = form.save(commit=False)
            order.payment_method = payment_method

            if request.user.is_authenticated:
                order.user = request.user
            else:
                order.session_key = request.session.session_key

            order.status = 'pending'
            order.transaction_id = ''
            order.save()

            for item in cart.items.all():
                if item.quantity > item.product.stock:
                    messages.error(request, "স্টক পর্যাপ্ত নয়")
                    return redirect('cart_detail')

                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    price=item.product.price,
                    quantity=item.quantity
                )

            cart.items.all().delete()  # Empty cart

            if payment_method == 'cod':
                order.status = 'processing'
                order.paid = False
                order.save()
                send_order_confirmation_email(order)
                messages.success(request, "Order placed successfully")
                return redirect('order_confirmation', order_id=order.id)

            request.session['order_id'] = order.id
            return redirect('payment_process')

    else:
        form = CheckoutForm()

    return render(request, 'shop/checkout.html', {'cart': cart, 'form': form})


# Payment Related Khela
# 0. Payment Process --> SSL Commerz er Window dekhabe, email confirmation pathano
# 1. Payment Success
# 2. Payment Fail
# 3. Payment Cancel

# 0. Payment Process

def payment_process(request):
    order_id = request.session.get('order_id')
    if not order_id:
        return redirect('home')

    order = get_object_or_404(Order, id=order_id)
    payment_data = generate_sslcommerz_payment(request, order)

    if payment_data.get('status') == 'SUCCESS':
        return redirect(payment_data['GatewayPageURL'])
    else:
        messages.error(request, 'Payment gateway error. Please try again.')
        return redirect('checkout')



# 1. Payment Success
@csrf_exempt
def payment_success(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    val_id = request.POST.get('val_id')
    if not val_id:
        messages.error(request, "Invalid payment data.")
        return redirect('home')

    validation_data = validate_sslcommerz_payment(val_id)
    if not validation_data or validation_data.get('status') != 'VALID':
        messages.error(request, "Payment validation failed.")
        return redirect('home')

    if validation_data.get('amount') != str(order.get_total_cost()):
        messages.error(request, "Amount mismatch.")
        return redirect('home')

    if order.paid:
        return render(request, 'shop/payment_success.html', {'order': order})

    order.paid = True
    order.status = 'processing'
    order.transaction_id = validation_data.get('tran_id')
    order.save()

    for item in order.order_items.all():
        product = item.product
        product.stock = max(0, product.stock - item.quantity)
        product.save()

    send_order_confirmation_email(order)

    if 'order_id' in request.session:
        del request.session['order_id']

    messages.success(request, "Payment successful")
    return render(request, 'shop/payment_success.html', {'order': order})




@csrf_exempt
def payment_fail(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    order.status = 'canceled'
    order.save()
    messages.error(request, "Payment failed!")
    return redirect('checkout')


@csrf_exempt
def payment_cancel(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    order.status = 'canceled'
    order.save()
    messages.info(request, "Payment canceled!")
    return redirect('cart_detail')




# profile page
@login_required
def profile(request):
    tab = request.GET.get('tab')

    orders = Order.objects.filter(user=request.user)
    completed_orders = orders.filter(status='delivered')
    total_spent = sum(order.get_total_cost() for order in orders)

    order_history_active = (tab == 'orders')
    edit_profile_active = (tab == 'edit')

    if request.method == 'POST' and edit_profile_active:
        form = ProfileUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
    else:
        form = ProfileUpdateForm(instance=request.user)

    return render(request, 'shop/profile.html', {
        'user': request.user,
        'orders': orders,
        'completed_orders': completed_orders,
        'total_spent': total_spent,
        'order_history_active': order_history_active,
        'edit_profile_active': edit_profile_active,
        'form': form
    })




@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            # Keep the user logged in after password change
            update_session_auth_hash(request, user)
            messages.success(request, 'Password changed successfully!')
            return redirect('profile') 
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PasswordChangeForm(user=request.user)

    return render(request, 'shop/password_change.html', {'form': form})




# ================= Policy Views =================

def terms_view(request):
    return render(request, 'shop/policies/terms.html')

def privacy_view(request):
    return render(request, 'shop/policies/privacy.html')

def return_refund_view(request):
    return render(request, 'shop/policies/return_refund.html')



def order_confirmation(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    # security check
    if order.user:
        if request.user != order.user:
            return redirect('home')
    else:
        if order.session_key != request.session.session_key:
            return redirect('home')

    return render(request, 'shop/email/order_confirmation.html', {
        'order': order,
        'show_print_button': True,   # শুধু পেজ-ভিউতে True, ইমেইলে থাকবে না
    })


def cart_count_view(request):
    cart = get_cart(request)
    return JsonResponse({'count': cart.get_total_items()})