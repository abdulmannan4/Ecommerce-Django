from django.urls import path
from .views import (
    home, product_detail, wishlist, login_view, checkout, 
    forgot_password, register_view, shop_category, err404, 
    coupon, order, profile_view, shop, add_to_wishlist, 
    add_to_cart, cart_view, increase_cart_quantity, 
    decrease_cart_quantity, SendPasswordResetEmailView, 
    UserChangePasswordView, UserPasswordResetView,logout_view,remove_cart_item,contact,buy_now
)
from django.contrib.auth import views as auth_views
from django.views.generic import TemplateView
from . import views
from .views import *
urlpatterns = [
     path('profile/', profile_view, name='profile'),
    path('', home, name='home'),
    path('product/detail/<slug:slug>', product_detail, name='product_detail'),
    path('wishlist/', wishlist, name='wishlist'),
    path('contact/',contact, name='contact'),
    
       path('search/' , search_view,name='search_view'),
   
    path('buy/<slug:slug>', buy_now, name='buy_now'), 
    path('checkout/', checkout, name='checkout'),
    path('shop/category/<slug:slug>/', shop_category, name='shop_category'),
    path('404/', err404, name='err404'), 
    path('coupon/', coupon, name='coupon'), 
    path('order/', order, name='order'), 
    path('add-to-wishlist/<slug:slug>/', add_to_wishlist, name='add_to_wishlist'),
   
    # path('profile/', UserProfileView.as_view(), name='profile'),
    
    path('login/', login_view, name='login'),  
    path('cart-view/', cart_view, name='cart_view'), 
    
    path('forgot-password/', forgot_password, name='forgot_password'),  
    path('shop/', shop, name='shop'),   
    path('add-to-cart/<slug:slug>/', add_to_cart, name='add_to_cart'),
    
    # URL for viewing the cart
    
    path('cart/increase/<slug:slug>/', increase_cart_quantity, name='increase_cart_quantity'),
    path('cart/decrease/<slug:slug>/', decrease_cart_quantity, name='decrease_cart_quantity'),

    path('remove-cart-item/', remove_cart_item, name='remove_cart_item'),
    
    
    path('register/', register_view, name='register'),
    # path('success/', TemplateView.as_view(template_name='success.html'), name='success_page'),  
    # path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', logout_view, name='logout'),
    path('changepassword/', UserChangePasswordView.as_view(), name='changepassword'),
    path('send-reset-password-email/', SendPasswordResetEmailView.as_view(), name='send-reset-password-email'),
   
    path('reset-password/<uid>/<token>/', UserPasswordResetView.as_view(), name='reset-password'),
    path('config/', views.stripe_config),
    path("create-checkout-session/", views.create_checkout_session,name='create_checkout_session'),
    path("success/", views.success,name='success'),
    path("canceled/", views.CanceledView.as_view()),
    path('stripe/webhook/', views.stripe_webhook, name='stripe-webhook'),
]
