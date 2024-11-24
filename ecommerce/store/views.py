from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.contrib.auth import authenticate, login as auth_login
from django.contrib import messages
from django.db.models import Count
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import stripe
from django.db.models import Count, Q
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Count
from .models import Product, OrderItem
from datetime import timedelta
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
# Import your models
from .models import Product, Category, Customer, Cart, CartProduct, Wishlist, Order, OrderItem, Coupon
from .forms import RegistrationForm, LoginForm
from store.serializers import SendPasswordResetEmailSerializer, UserChangePasswordSerializer, UserLoginSerializer, UserPasswordResetSerializer, UserProfileSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from .renderers import UserRenderer 
from rest_framework.response import Response
from rest_framework import status
from .forms import CustomerForm
from django.shortcuts import render, redirect, get_object_or_404
from .forms import CustomerForm
from .models import Customer

from django.shortcuts import render, redirect
from .forms import CustomerForm
from .models import Customer

def get_tokens_for_user(user):
  refresh = RefreshToken.for_user(user)
  return {
      'refresh': str(refresh),
      'access': str(refresh.access_token),
  }

#REGISTER
def register_view(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            refresh = RefreshToken.for_user(user)  # Create Refresh Token
            access = str(refresh.access_token)     # Create Access Token

            # Create the response
            response = redirect('login')
            # Set the cookies for tokens
            response.set_cookie(key='refresh', value=str(refresh), httponly=True, secure=True)
            response.set_cookie(key='access', value=access, httponly=True, secure=True)
            print(response.cookies) 
            return response
    else:
        form = RegistrationForm()

    return render(request, 'register.html', {'form': form})
# LOGIN
def login_view(request):
    if request.method == 'POST':
        form = LoginForm(data=request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            print(f"Form valid: email={email}, password={password}")
            user = authenticate(email=email, password=password)
            
            if user is not None:
                auth_login(request, user)
                return redirect('home')  # Redirect to your home page
            else:
                form.add_error(None, "Invalid email or password.")
                print("Authentication failed: User not found or password incorrect.")
        else:
            print("Form is not valid:")
            print(form.errors)  # Print form errors for debugging

    else:
        form = LoginForm()

    return render(request, 'login.html', {'form': form})









# TRENDING PRODUCT LOGIC
def get_trending_products():
    # Get the date 30 days ago
    last_month = timezone.now() - timedelta(days=30)

    # Get the products with the highest number of sales in the last 30 days
    trending_products = Product.objects.annotate(
        num_sales=Count(
            'orderitem__id',  # Count the related 'OrderItem' records
            filter=Q(orderitem__order__order_date__gte=last_month)  # Filter by last month's orders
        )
    ).filter(num_sales__gt=0).order_by('-num_sales')

    return trending_products
# HOME
def home(request):
    # Fetch all products and categories
    products = Product.objects.all()
    categories = Category.objects.prefetch_related('products').annotate(product_count=Count('products'))
    featured = Product.objects.filter(featured=True)
    user = request.user
    tpr = get_trending_products()

    try:
        if not tpr:
            print("No trending products found.")
        else:
            for tp in tpr:
                print(f"Product: {tp.name}, Sales: {tp.num_sales}")
    except Exception as e:
        print(f"Error fetching trending products: {e}")


    cart_items = []
    cp = 0 
    wishlists = []
    w = 0  

    if user.is_authenticated:

        customer, created = Customer.objects.get_or_create(user=user)
        cart, created = Cart.objects.get_or_create(customer=customer)

        cart_items = CartProduct.objects.filter(cart=cart).prefetch_related('product')
        cp = cart_items.count()
        wishlists = Wishlist.objects.prefetch_related('products').filter(customer=customer)
        for wishlist in wishlists:
            w = wishlist.products.count()

    else:

        customer, created = Customer.objects.get_or_create(user_id=1)
        cart = None 
        wishlists = Wishlist.objects.prefetch_related('products').filter(customer=customer)
    
        for wishlist in wishlists:
            w = wishlist.products.count()

  
    category_counts = {cat.name: cat.product_count for cat in categories}

    context = {
        "products": products,
        "categories": categories,
        'cart_items': cart_items,
        'cart': cart,
        'tpr': tpr,
        'featured': featured,
        'w': w,  # Last wishlist product count (it will overwrite, consider this logic)
        'cp': cp,  # Cart product count
        'category_counts': category_counts  # This will give a dict of categories and their product counts
    }

    return render(request, 'index.html', context)

from django.shortcuts import render, get_object_or_404
# PRODUCT PAGE
def product_detail(request, slug):

    p = get_object_or_404(Product, slug=slug)

    product_quantity = 0

    # Check if the user is authenticated
    if request.user.is_authenticated:
        # Ensure the customer object exists for the user
        customer, created = Customer.objects.get_or_create(user=request.user)
        
        # Get or create the cart associated with the customer
        cart, created = Cart.objects.get_or_create(customer=customer)
        
        # Try to get the cart item for this product
        try:
            cart_item = CartProduct.objects.get(cart=cart, product=p)
            product_quantity = cart_item.quantity
        except CartProduct.DoesNotExist:
            product_quantity = 0  # Set to 0 if product is not in the cart

    # Add product and quantity to the context
    context = {
        'p': p,
        'product_quantity': product_quantity
    }
    
    return render(request, 'product-detail.html', context)


# WISHLIST
def wishlist(request):
    user = request.user
    print(user)  # Debug: print the current user
    
    if not user.is_authenticated:
        return render(request, 'wishlist.html', {'wishlist': None})  # Redirect or show an empty wishlist

    # Get or create customer
    customer, created = Customer.objects.get_or_create(user=user)
    wishlist = Wishlist.objects.prefetch_related('products').filter(customer=customer).first()
    print(user)
    print(customer)
    print(wishlist)
    # If the user doesn't have a wishlist, handle it accordingly
    if not wishlist:
        wishlist = Wishlist.objects.create(customer=customer)

    return render(request, 'wishlist.html', {'wishlist': wishlist})


from django.contrib.auth import logout
# LOGOUT
def logout_view(request):
    logout(request) 
    print('userlogogedout')# Log the user out
    print(request.user)# Log the user out
    
    return redirect(settings.LOGOUT_REDIRECT_URL)





from django.shortcuts import get_list_or_404
# CATEGORIES PAGE
def shop_category(request,slug):
    cat_p=get_list_or_404(Category.objects.prefetch_related('products'),slug=slug)
    
    context={'cat_p':cat_p }
    
    return render(request, 'shop-1600.html',context)
def err404(request):
    return render(request, '404.html')
def coupon(request):
    coupons = Coupon.objects.all()
    


    return render(request, 'coupon.html', {'coupons': coupons})
# ORDER PAGE
def order(request):
    return render(request, 'order.html')

# PROFILE PAGE
def profile_view(request):
    user = request.user

    # Check if the user is authenticated
    if user.is_authenticated:
        # Get or create the Customer instance
        customer, created = Customer.objects.get_or_create(user=user)

        # If the Customer instance was just created, it may not have all fields filled
        if request.method == 'POST':
            form = CustomerForm(request.POST, instance=customer)
            if form.is_valid():
                form.save()
                return redirect('profile')  # Redirect after saving
        else:
            form = CustomerForm(instance=customer)

        # Pass customer data directly from the instance
        return render(request, 'profile.html', {
            'form': form,
            'customer_data': customer  # Pass the customer instance
        })
    else:
        return redirect('login')

# CONTACT
def contact(request):
    return render(request, 'contact.html')

# ALL PRODUCT SHOP PAGE
def shop(request):
    products=Product.objects.all()
    
    return render(request, 'shop.html',{'products':products})


# ADD TO WISHLIST LOGIC
@csrf_exempt
def add_to_wishlist(request, slug):
    print("Received request for slug:", slug)  # Log the slug received

    if request.method == 'POST':
        try:
            # Fetch the product by slug
            product = Product.objects.get(slug=slug)
            print("Product found:", product)
            user=request.user# Log product details
            print(request.user)
           
            # Create or get a guest customer
            # Here we are not associating with a specific user, as we are allowing guest access
            customer, created = Customer.objects.get_or_create(user=user)  # Replace None with a logic if necessary

            # Get or create a wishlist for the customer
            wishlist, created = Wishlist.objects.get_or_create(customer=customer)

            # Add product to wishlist
            wishlist.products.add(product)
                
            print(f"Product added to wishlist: {product}")
            return JsonResponse({'message': 'Product added to wishlist'}, status=200)
        except Product.DoesNotExist:
            print("Product not found")  # Log error
            return JsonResponse({'error': 'Product not found'}, status=404)
        except Exception as e:
            print(f"An error occurred: {e}")  # Log the error for debugging
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=400)


# ADD TO CART LOGIC
@csrf_exempt
def add_to_cart(request, slug):
    if request.method == 'POST':
        # Fetch the product by slug
        product = get_object_or_404(Product, slug=slug)

        user = request.user

        # Create or get a customer
        if user.is_authenticated:
            customer, created = Customer.objects.get_or_create(user=user)
        else:
            # Handle guest users (you might want to create a temporary customer)
            customer, created = Customer.objects.get_or_create(user=None)  # Or however you want to manage guest users

        # Get or create a cart for the customer
        cart, created = Cart.objects.get_or_create(customer=customer)

        # Get or create a cart product entry
        cart_product, created = CartProduct.objects.get_or_create(product=product, cart=cart)

        if not created:
            # If the product was already in the cart, increase the quantity
            cart_product.quantity += 1
        else:
            # If the product is newly added, set its quantity to 1
            cart_product.quantity = 1

        cart_product.save()  # Save the cart product entry

        return JsonResponse({'message': 'Product added to cart', 'quantity': cart_product.quantity}, status=200)

    return JsonResponse({'error': 'Invalid request method'}, status=400)
# CART VIEW LOGIC
def cart_view(request):
    user = request.user
    customer, created = Customer.objects.get_or_create(user=user if user.is_authenticated else None)

   
    cart = get_object_or_404(Cart.objects.prefetch_related('cartproduct_set__product'), customer=customer)
    cart_items = list(cart.cartproduct_set.all())
    discount = 0
    ct = cart.get_cart_total_discounted() 
    final_price = ct
    coupon_code = request.POST.get('coupon_code', None)
    if coupon_code:
        try:
        
            coupon = Coupon.objects.get(code=coupon_code)
            if coupon.is_valid():
                discount = coupon.discount_amount
                discount_amount = (ct * discount) / 100
                final_price = ct - discount_amount
                cart.coupon_flag = True
                c=cart.coupon_flag
                print(c)
                cart.coupon_discounted_amount=final_price
                cart.save()
                print(f"Coupon applied: {coupon_code}, Discount: {discount}%")
            else:
                print("Coupon is not valid.")
               
        except Coupon.DoesNotExist:
            print("Coupon does not exist.")
        
    return render(request, 'cart.html', {
        'cart_items': cart_items,
        'discount': discount, 
        'cart': cart,
        'final_price': final_price 
    })



# INCERAE CART QUANTITY
def increase_cart_quantity(request, slug):
    if request.method == 'POST':
        if request.user.is_authenticated:
            # For authenticated users
            customer = get_object_or_404(Customer, user=request.user)
        else:
            # Handle guest users: Create a temporary customer if none exists
            customer, created = Customer.objects.get_or_create(user=None)

        # Get the cart for the customer (whether authenticated or guest)
        cart, created = Cart.objects.get_or_create(customer=customer)

        # Get the product from the slug
        product = get_object_or_404(Product, slug=slug)

        # Get or create the cart item for the product
        cart_item, created = CartProduct.objects.get_or_create(cart=cart, product=product)

        # Increase the quantity of the cart item
        cart_item.quantity += 1
        cart_item.save()

        # Return the updated quantity as a response
        return JsonResponse({'status': 'success', 'quantity': cart_item.quantity})

    return JsonResponse({'status': 'error'}, status=400)

# DECRRASE QAUNTITY
def decrease_cart_quantity(request, slug):
    if request.method == 'POST':
        if request.user.is_authenticated:
            # For authenticated users
            customer = get_object_or_404(Customer, user=request.user)
        else:
            # Handle guest users: Create a temporary customer if none exists
            customer, created = Customer.objects.get_or_create(user=None)

        # Get or create the cart for the customer (whether authenticated or guest)
        cart, created = Cart.objects.get_or_create(customer=customer)

        # Get the product from the slug
        product = get_object_or_404(Product, slug=slug)

        # Get the cart item for the product
        cart_item = get_object_or_404(CartProduct, cart=cart, product=product)

        # Decrease the quantity of the cart item if it's greater than 0
        if cart_item.quantity > 0:
            cart_item.quantity -= 1
            cart_item.save()

        # Return the updated quantity as a response
        return JsonResponse({'status': 'success', 'quantity': cart_item.quantity})

    return JsonResponse({'status': 'error'}, status=400)

def profile(request):
    
     return render(request, 'profile.html')# Redirect to your cart page

def forgot_password(request):
    
     return render(request, 'forgot.html')

def remove_cart_item(request):
    if request.method == 'POST':
        cart_product_id = request.POST.get('cart_product_id')
        cart_product = get_object_or_404(CartProduct, id=cart_product_id)

        # Debug output
        print(f"User: {request.user.email}, Cart Customer: {cart_product.cart.customer.user.email}")
        print("Is user authenticated:", request.user.is_authenticated)

        # Check ownership using the email attribute
        if cart_product.cart.customer.user.email == request.user.email:
            cart_product.delete()
            return JsonResponse({'success': True, 'message': 'Item removed successfully.'})

        return JsonResponse({'success': False, 'message': 'You do not have permission to remove this item.'})

    return JsonResponse({'success': False, 'message': 'Invalid request.'}, status=400)

# Set your Stripe secret key
stripe.api_key = settings.STRIPE_SECRET_KEY

from django.shortcuts import render, redirect, get_object_or_404
from .forms import ShippingForm  # Import the ShippingForm
from .models import Customer, Cart, CartProduct, ShippingAddress



from django.shortcuts import render, redirect, get_object_or_404
from .models import Customer, ShippingAddress, Cart, CartProduct
from .forms import ShippingForm
from django.contrib.auth.decorators import login_required

@login_required
def checkout(request):
    """Render the checkout page and handle customer details."""
    user = request.user
    if not user.is_authenticated:
        print("User is not authenticated, redirecting to login.")
        return redirect('login')
    coupon_price=[]
    cart_dis=[]
    cart_total=[]
    # Get the customer object for the authenticated user
    customer = get_object_or_404(Customer, user=user)
    print(f"Customer found: {customer.user}")
    cart_dis=[]
    cart = get_object_or_404(Cart, customer=customer)
    print(cart.coupon_discounted_amount)
    if cart.coupon_flag == True:
        coupon_price = cart.coupon_discounted_amount
    elif cart.coupon_flag == False and cart.get_cart_total_discounted():
        cart_dis = cart.get_cart_total_discounted()
    else:
        cart_total = cart.get_cart_total()  # Make sure to call the method


        
         
        

    cart_products = CartProduct.objects.filter(cart=cart).prefetch_related('product')
    print(f"Cart products: {[product.product.name for product in cart_products]}")  # List the product names in the cart

    context = {
         # Pass the empty form to the template
        'cart_products': cart_products,
        'cart': cart,
        ' coupon_price': coupon_price,
        'cart_dis':cart_dis,
        'coupon_price':coupon_price,
        ' cart_total': cart_total,
        
        
        # Ensure this is always passed, even if it's None
    }

    print("Rendering checkout page with context.")
    return render(request, 'checkout.html', context)





@csrf_exempt
def stripe_config(request):
    if request.method == "GET":
        stripe_config = {"publicKey": settings.STRIPE_PUBLISHABLE_KEY}
        return JsonResponse(stripe_config, safe=False)
def decrease_product_quantity(product,quantity):
    
      product=Product.objects.get(name=product)
      if product.stock > quantity:
        product.stock -= quantity
        product.save()
        

from django.shortcuts import get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Customer, Cart, CartProduct, Order, OrderItem
from .forms import ShippingForm
import stripe
from django.conf import settings
@csrf_exempt
def create_checkout_session(request):
    user = request.user.id
    customer = get_object_or_404(Customer, user=user)

    shipping_address = None
    form = ShippingForm()

    if request.method == 'POST':
        print("POST request received, processing form data.")
        
        # Process the shipping form
        form = ShippingForm(request.POST)
        
        if form.is_valid():
            shipping_address = form.save(commit=False)
            shipping_address.customer = customer
            shipping_address.save()

            print(f"Shipping address saved: {shipping_address.address}, {shipping_address.city}, {shipping_address.postal_code}, {shipping_address.country}")

            print("Redirecting to the next checkout step.")
        else:
            print("Form is invalid. Errors:", form.errors)

        # Proceed with creating the checkout session
        try:
            # Get cart and its associated products for this customer
            cart = Cart.objects.get(customer=customer)
            cart_products = CartProduct.objects.filter(cart=cart).prefetch_related('product')
            
            line_items = []
            for cart_product in cart_products:
                product = cart_product.product
                            
                # Determine the product price with the correct prioritization
                if cart.coupon_flag: 
                   
                    pp = cart.coupon_discounted_amount
                    for p in cart_products:
                        q=p.quantity
                    q+=q
                    product_price=pp/q
                    print(product_price)
                elif product.discount_percentage:  # If no coupon, apply product discount
                    product_price = product.discounted_price()
                elif product.price:  # If no coupon and no discount, use the regular price
                    product_price = product.price
                else:
                    product_price = 0  # Fallback if no price is set

                # Add line item for Stripe
                line_items.append({
                    "price_data": {
                        "currency": "usd",
                        "product_data": {
                            "name": product.name,
                        },
                        "unit_amount": int(product_price * 100),  # Convert price to cents
                    },
                    "quantity": cart_product.quantity,
                })
                product=cart_product.product.name
                
                quantity=cart_product.quantity
                decrease_product_quantity(product,quantity)
            # Set up Stripe API key securely
            stripe.api_key = settings.STRIPE_SECRET_KEY
            domain_url = "http://localhost:8000/"

            # Create a checkout session in Stripe
            checkout_session = stripe.checkout.Session.create(
                success_url=domain_url + "success?session_id={CHECKOUT_SESSION_ID}",
                cancel_url=domain_url + "canceled/",
                payment_method_types=["card"],
                mode="payment",
                line_items=line_items,
            )

            # Create an order and associated order items in the database
            order = Order.objects.create(
                customer=customer,
                shipping_address=shipping_address,  # Assuming shipping address is set if valid
                complete=True,
                session_id=checkout_session.id,
            )
            shipping_address.order = order
            shipping_address.save()

            # Create OrderItems for each cart product, ensuring the correct price per product
            for cart_product in cart_products:
                if cart.coupon_flag:
                    product_price = cart.coupon_discounted_amount
                elif cart_product.product.discount_percentage:
                    product_price = cart_product.product.discounted_price()
                elif cart_product.product.price:
                    product_price = cart_product.product.price
                else:
                    product_price = 0  # Fallback if no price is set

                OrderItem.objects.create(
                    order=order,
                    product=cart_product.product,
                    quantity=cart_product.quantity,
                    price=product_price,
                )

            # Redirect the user to the Stripe Checkout page
            return redirect(checkout_session.url)

        except Exception as e:
            # Handle errors gracefully and log them
            print(f"Error during checkout session creation: {e}")
            return JsonResponse({"error": str(e)}, status=500)

    # For GET requests, return a blank form
    else:
        print("GET request received, initializing empty form for shipping address.")
        form = ShippingForm()

    return JsonResponse({"error": "Invalid request method."}, status=400)


from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.core.exceptions import ObjectDoesNotExist
from .models import Customer, Order, OrderItem, Cart, CartProduct
import stripe

# Your stripe secret key setup here
stripe.api_key = "sk_test_your_api_key"

def success(request):
    session_id = request.GET.get("session_id")

    if not session_id:
        return JsonResponse({"error": "Session ID missing"}, status=400)

    user = request.user
    if not user.is_authenticated:
        return redirect('login')  # Adjust to your actual login URL name
    
    try:
        # Get the customer associated with the user
        customer = get_object_or_404(Customer, user=user)

        # Retrieve the Stripe checkout session using the session ID
        checkout_session = stripe.checkout.Session.retrieve(session_id)

        # Retrieve the order that corresponds to the session ID
        order = get_object_or_404(Order, session_id=checkout_session.id)
        order_items = OrderItem.objects.filter(order=order)

        # Calculate the total price from the order
        total = order.get_order_total()

        # Retrieve the cart for the customer
        cart = get_object_or_404(Cart, customer=customer)
        cart_products = CartProduct.objects.filter(cart=cart)

        # Clear the cart after the order is processed
        cart.coupon_flag = False  # Clear the coupon flag after the checkout
        cart_products.delete()  # Delete all cart products
        cart.save()

        # Prepare context to render the success page
        context = {
            'order': order,
            'order_items': order_items,
            'shipping_address': order.shipping_address,
            'checkout_session': checkout_session,
            'total': total
        }

        return render(request, 'success.html', context)

    except stripe.error.StripeError as e:
        # Handle Stripe-specific errors
        return JsonResponse({"error": f"Stripe error: {e}"}, status=500)

    except Order.DoesNotExist:
        # Handle the case when the order does not exist
        return JsonResponse({"error": "Order not found for the given session_id"}, status=404)

    except Cart.DoesNotExist:
        # Handle the case when the cart does not exist for the customer
        return JsonResponse({"error": "Cart not found for the customer"}, status=404)

    except ObjectDoesNotExist as e:
        # Handle any other object not found errors
        return JsonResponse({"error": str(e)}, status=404)

    except Exception as e:
        # Catch any other unexpected exceptions
        return JsonResponse({"error": f"An unexpected error occurred: {e}"}, status=500)

  
class CanceledView(TemplateView):
    template_name = "cancel.html"

@csrf_exempt
def stripe_webhook(request):
    stripe.api_key = settings.STRIPE_SECRET_KEY
    endpoint_secret = 'whsec_bf9a833e26655a5d4b2aba75f48bfee63fa46025ac3ab392183c52157d3e5602'
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE", "")
    event = None

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except ValueError as e:
        return HttpResponse(status=400)  # Invalid payload
    except stripe.error.SignatureVerificationError as e:
        return HttpResponse(status=400)  # Invalid signature

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        session_id = session.get("id")
        customer_id = session.get("client_reference_id")

        try:
            # Retrieve the order using the session_id, not the id
            order = Order.objects.get(session_id=session_id)
            order.complete = True
            order.transaction_id = session_id  # You can also use the session ID as the transaction ID
            order.save()
            print(f"Order {order.id} marked as complete.")
        except Order.DoesNotExist:
            print(f"Order not found for session {session_id}")
            return HttpResponse(status=404)  # Order not found

    return HttpResponse(status=200)

from django.db.models import Q


from django.shortcuts import render
from .models import Product


def search_view(request):
    query = request.GET.get('q', '')
    print(query)# Get the query parameter
    if query:
    
        results = Product.objects.filter(name__icontains=query)
        
        print(results)# Get the query parameter# Search in Product model
    else:
        results = Product.objects.none()  # If no query, return no results

    # Check if the request is AJAX
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render(request, 'search_result.html', {'results': results, 'query': query})
    
    # Regular (non-AJAX) request: render the full page
    return render(request, 'base.html', {'results': results, 'query': query})


from django.shortcuts import redirect
from .models import Product
from .views import add_to_cart  # Assuming add_to_cart is defined elsewhere

def buy_now(request, slug):
    user = request.user
    if not user.is_authenticated:
        # Redirect the user to the login page if they are not authenticated
        return redirect('login')  # Make sure 'login' is the name of your login view
    
    else:
        # Proceed if the user is authenticated
        product = Product.objects.get(slug=slug)
        product_slug = product.slug
        add_to_cart(request, product_slug)  # Add the product to the cart
        return redirect('checkout')  # Redirect to the checkout page



# def search_view(request):
#     query = request.GET.get('q', '')
#     if query:
#         results = Product.objects.filter(
#             Q(name__icontains=query) | Q(description__icontains=query)
#         )
#         print(query)
#     else:
#         results = Product.objects.none()  # If no query, return empty queryset
#     return render(request, 'your_template.html', {'results': results, 'query': query})



# from django.http import JsonResponse

# def create_checkout_session(request):
#     """Create a Stripe Checkout session from the cart."""
#     if request.method == "POST":  # Ensure it's a POST request
#         user = request.user
#         cart = get_object_or_404(Cart, customer__user=user)

#         line_items = []
        
#         # Create line items based on cart products
#         for item in CartProduct.objects.filter(cart=cart):
#             line_items.append({
#                 'price_data': {
#                     'currency': 'usd',
#                     'product_data': {
#                         'name': item.product.name,
#                         'images': [item.product.image.url]  # Ensure this field is valid
#                     },
#                     'unit_amount': int(item.product.price * 100),  # Amount in cents
#                 },
#                 'quantity': item.quantity,
#             })

#         host = request.get_host()
#         success_url = f"http://{host}{reverse('payment-success').rstrip('/')}"
#         cancel_url = f"http://{host}{reverse('payment-cancel').rstrip('/')}"


#         # Log the URLs to verify correctness
#         print(f"Success URL: {success_url}")
#         print(f"Cancel URL: {cancel_url}")

#         try:
#             checkout_session = stripe.checkout.Session.create(
#                 line_items=line_items,
#                 mode='payment',
#                 success_url=success_url,
#                 cancel_url=cancel_url,
#             )
#             return redirect(checkout_session.url, code=303)
#         except Exception as e:
#             print(f"Error creating checkout session: {e}")
#             return JsonResponse({'error': str(e)}, status=400)

#     return JsonResponse({'error': 'Invalid request method.'}, status=400)

# def success_view(request):
#     """Render the success page after payment."""
#     return render(request, 'success.html')

# def cancel_view(request):
#     """Render the cancel page if payment was canceled."""
#     return render(request, 'cancel.html')
# class UserRegistrationView(APIView):
# #   renderer_classes = [UserRenderer]
# #   def post(self, request, format=None):
# #     serializer = UserRegistrationSerializer(data=request.data)
# #     serializer.is_valid(raise_exception=True)
# #     user = serializer.save()
# #     token = get_tokens_for_user(user)
# #     return Response({'token':token, 'msg':'Registration Successful'}, status=status.HTTP_201_CREATED)



class UserLoginView(APIView):
  renderer_classes = [UserRenderer]
  def post(self, request, format=None):
    serializer = UserLoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    email = serializer.data.get('email')
    password = serializer.data.get('password')
    user = authenticate(email=email, password=password)
    if user is not None:
      token = get_tokens_for_user(user)
      return Response({'token':token, 'msg':'Login Success'}, status=status.HTTP_200_OK)
    else:
      return Response({'errors':{'non_field_errors':['Email or Password is not Valid']}}, status=status.HTTP_404_NOT_FOUND)

class UserProfileView(APIView):
  renderer_classes = [UserRenderer]
  permission_classes = [IsAuthenticated]
  def get(self, request, format=None):
    serializer = UserProfileSerializer(request.user)
    return Response(serializer.data, status=status.HTTP_200_OK)

class UserChangePasswordView(APIView):
  renderer_classes = [UserRenderer]
  permission_classes = [IsAuthenticated]
  def post(self, request, format=None):
    serializer = UserChangePasswordSerializer(data=request.data, context={'user':request.user})
    serializer.is_valid(raise_exception=True)
    return Response({'msg':'Password Changed Successfully'}, status=status.HTTP_200_OK)

class SendPasswordResetEmailView(APIView):
  renderer_classes = [UserRenderer]
  def post(self, request, format=None):
    serializer = SendPasswordResetEmailSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    return Response({'msg':'Password Reset link send. Please check your Email'}, status=status.HTTP_200_OK)

class UserPasswordResetView(APIView):
  renderer_classes = [UserRenderer]
  def post(self, request, uid, token, format=None):
    serializer = UserPasswordResetSerializer(data=request.data, context={'uid':uid, 'token':token})
    serializer.is_valid(raise_exception=True)
    return Response({'msg':'Password Reset Successfully'}, status=status.HTTP_200_OK)





