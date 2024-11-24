from django.contrib import admin
from .models import (
    Category,
    Product,
    Customer,
    Cart,
    CartProduct,
    ShippingAddress,
    Order,
    OrderItem,
    Payment,
    Wishlist,
    Review,
  

    ProductVariation,
    OrderStatus,
    TransactionHistory,

    Refund,
    User, Coupon # Import your User model
)

# Inline for ProductVariation
class ProductVariationInline(admin.TabularInline):
    model = ProductVariation
    extra = 1  # Number of empty variations to show (optional)

# Customizing Product Admin to include ProductVariation
class ProductAdmin(admin.ModelAdmin):
    inlines = [ProductVariationInline]

# Custom User Admin (optional)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'name', 'is_active', 'is_admin')  # Adjust the fields you want to display
    search_fields = ('email', 'name')  # Add search functionality

# Register your models here
admin.site.register(Category)
admin.site.register(Coupon)
admin.site.register(Product, ProductAdmin)  # Register Product with custom ProductAdmin
admin.site.register(Customer)
admin.site.register(Cart)
admin.site.register(CartProduct)
class ShippingAddressAdmin(admin.ModelAdmin):
    list_display = ('customer', 'order', 'address', 'city', 'postal_code', 'country', 'date_added')
    search_fields = ('customer__user__username', 'order__id', 'address', 'city', 'postal_code', 'country')

    # Add fields for editing shipping address directly in the admin interface
    fields = ['customer', 'order', 'address', 'city', 'postal_code', 'country']
    
    # Optionally, you can make these fields editable directly in the list view using list_editable
    list_editable = ('address', 'city', 'postal_code', 'country')

admin.site.register(ShippingAddress, ShippingAddressAdmin)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(Payment)
admin.site.register(Wishlist)
admin.site.register(Review)

admin.site.register(OrderStatus)
admin.site.register(TransactionHistory)

admin.site.register(Refund)
admin.site.register(User, UserAdmin)  # Register User with custom UserAdmin
