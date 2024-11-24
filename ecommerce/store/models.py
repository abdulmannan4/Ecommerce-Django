from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
# Category model for grouping products
from django.db import models
from django.contrib.auth.models import BaseUserManager,AbstractBaseUser,PermissionsMixin


from django.conf import settings




import uuid 

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, is_staff=False):
        """
        Creates and saves a User with the given email, username, tc and password.
        """
        if not email:
            raise ValueError('User must have an email address')

        user = self.model(
            email=self.normalize_email(email),
           
        )

        user.set_password(password)
        user.is_staff = is_staff  # Set is_staff when creating the user
        user.save(using=self._db)
        return user

    def create_superuser(self, email,  password=None):
        """
        Creates and saves a superuser with the given email, username, tc and password.
        """
        user = self.create_user(
            email,
            password=password,
            
            is_staff=True,  # Set is_staff to True for superuser
        )
        user.is_admin = True
        user.save(using=self._db)
        return user

# Custom User Model
class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(
        verbose_name='Email',
        max_length=255,
        unique=True,
    )
    username = models.CharField(max_length=150, unique=True, null=True, blank=True)
    name = models.CharField(max_length=200)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    tc = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []  # Include 'username' and any other fields needed

    def __str__(self):
        return self.email

    def has_perm(self, perm, obj=None):
        return self.is_admin

    def has_module_perms(self, app_label):
        return True
class Customer(models.Model):
    first_name = models.CharField(max_length=30,default="Unknown", blank=True)
    last_name = models.CharField(max_length=30, default="Unknown", blank=True)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,null=True)
    phone_number = models.CharField(max_length=15)
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=50)

    def __str__(self):
        return self.user.email if self.user else "No User"
class Category(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    slug = models.SlugField(unique=True,blank=True)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    
    def __str__(self):
        return self.name
    def save(self, *args, **kwargs):
      
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    class Meta:
        verbose_name_plural = "Categories"
# Product model for items available in the store
class Product(models.Model):
    category = models.ForeignKey(Category, related_name='products', on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField(default=0)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    slug = models.SlugField(unique=True,blank=True)
    date_added = models.DateTimeField(auto_now_add=True)
    featured = models.BooleanField(default=False)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)  # Discount in percentage
    def __str__(self):
        return self.name
    def discounted_price(self):
        """Calculate the discounted price."""
        return self.price - (self.price * self.discount_percentage / 100)
    def get_price(self):
        return self.price
    
    def in_stock(self):
        return self.stock > 0
    def save(self, *args, **kwargs):
      
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)




# Cart model to manage products added to the cart
class Cart(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True)
    products = models.ManyToManyField(Product, through='CartProduct')  # Use a through model for extra fields if necessary
    date_created = models.DateTimeField(auto_now_add=True)
    complete = models.BooleanField(default=False)
    coupon_flag=models.BooleanField(default=False)
    coupon_discounted_amount=models.FloatField(null=True,blank=True)
    
 
    def __str__(self):
        return f"Cart {self.id} for {self.customer.user}" if self.customer else f"Cart {self.id} for No Customer"

    

    def get_cart_total(self):
        return sum(item.get_total() for item in self.cartproduct_set.all())

    def get_cart_total_discounted(self):
        return sum(item.get_total_discounted() for item in self.cartproduct_set.all())

    def get_cart_items(self):
        return self.cartproduct_set.count()  # Counts the number of products in the cart
class CartProduct(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    
    
    class Meta:
        unique_together = ('cart', 'product')
    def get_total(self):
        return self.product.price * self.quantity
    
    def get_total_discounted(self):
        return self.product.discounted_price() * self.quantity
    def __str__(self):
        return f"{self.quantity} of {self.product.name} in cart {self.cart.id}"




# OrderItem model for individual items within an order


class ShippingAddress(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True)
    order = models.ForeignKey('Order', on_delete=models.SET_NULL, null=True, related_name='shipping_addresses')  # Adjusted related_name
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=50)
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Shipping Address for {self.customer} "

class Order(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True)
    order_date = models.DateTimeField(auto_now_add=True)
    complete = models.BooleanField(default=False)
    transaction_id = models.CharField(max_length=100, null=True)
    shipping_address = models.ForeignKey('ShippingAddress', related_name='orders', on_delete=models.SET_NULL, blank=True, null=True)  # Adjusted related_name
    session_id = models.CharField(max_length=255, null=True, blank=True)  # Add this line to store the Stripe session ID
    def __str__(self):
        return f"Order {self.id} by {self.customer}"

    def get_order_total(self):
        return sum(item.get_total() for item in self.orderitem_set.all())

    def get_order_items(self):
        return self.orderitem_set.all()

class OrderItem(models.Model):
    order = models.ForeignKey('Order', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    quantity = models.IntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantity} of {self.product.name}"

   
    def get_total(self):
        # Get the related cart for the customer of this order
        cart = self.order.customer.cart_set.first()  # Access the cart through the customer
        
        # Step 1: Check if the cart exists and if a coupon is applied
        if cart and cart.coupon_flag:
            t_price = cart.coupon_discounted_amount  # Use coupon discounted amount from the cart
        # Step 2: If no coupon, apply the product discount if it exists
        elif self.product.discount_percentage:
            t_price = self.product.discounted_price()  # Apply product discount
        # Step 3: If no discounts, use the regular product price
        else:
            t_price = self.product.price  # No discounts, use regular price

        # Return the total price for this order item (quantity * price)
        return self.quantity * t_price
# Payment model to handle payment transactions
class Payment(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)
    success = models.BooleanField(default=False)
    transaction_id = models.CharField(max_length=100)

    def __str__(self):
        return f"Payment {self.transaction_id} for {self.order}"


# Wishlist model to manage customer wishlists
class Wishlist(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    products = models.ManyToManyField(Product)

    def __str__(self):
        return f"Wishlist for {self.customer}"


# Review model for product reviews by customers
class Review(models.Model):
    product = models.ForeignKey(Product, related_name='reviews', on_delete=models.CASCADE)
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True)
    review_text = models.TextField(blank=True, null=True)
    rating = models.IntegerField(default=1)  # Rating from 1 to 5
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review by {self.customer} on {self.product.name}"






# ProductVariation model for different product options like size or color
class ProductVariation(models.Model):
    product = models.ForeignKey(Product, related_name='variations', on_delete=models.CASCADE)
    name = models.CharField(max_length=50)  # e.g., "Size", "Color"
    value = models.CharField(max_length=50)  # e.g., "Medium", "Red"
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)

    def __str__(self):
        return f"{self.product.name} - {self.name}: {self.value}"


# OrderStatus model for tracking the current status of an order
class OrderStatus(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE)
    status = models.CharField(max_length=50, choices=[
        ('Pending', 'Pending'),
        ('Processing', 'Processing'),
        ('Shipped', 'Shipped'),
        ('Delivered', 'Delivered'),
        ('Cancelled', 'Cancelled'),
    ], default='Pending')
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order {self.order.id} - {self.status}"


# TransactionHistory model for recording transaction details
class TransactionHistory(models.Model):
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50, choices=[
        ('Success', 'Success'),
        ('Failed', 'Failed'),
        ('Pending', 'Pending')
    ], default='Pending')
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Transaction for {self.payment.order.id} - {self.status}"




# Refund model to handle refund requests
class Refund(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE)
    reason = models.TextField()
    accepted = models.BooleanField(default=False)
    date_requested = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Refund for {self.order.id} - {'Accepted' if self.accepted else 'Pending'}"
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=User)
def create_customer_profile(sender, instance, created, **kwargs):
    if created:
        Customer.objects.create(user=instance)
from django.utils import timezone

class Coupon(models.Model):
    code = models.CharField(max_length=50, unique=True)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2)
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.code
    def save(self, *args, **kwargs):
        # Ensure the start_date and end_date are timezone-aware and in UTC
        if self.start_date and self.start_date.tzinfo is None:
            self.start_date = timezone.make_aware(self.start_date, timezone.utc)
        if self.end_date and self.end_date.tzinfo is None:
            self.end_date = timezone.make_aware(self.end_date, timezone.utc)
        super().save(*args, **kwargs)

    def is_valid(self):
        """
        Returns whether the coupon is valid.
        A coupon is valid if it is active, and the current time is between the start and end dates (in UTC).
        """
        # Get the current UTC time (timezone-aware)
        now = timezone.now()

        # Ensure start_date and end_date are in UTC
        if self.start_date.tzinfo is None:
            self.start_date = timezone.make_aware(self.start_date, timezone.utc)
        if self.end_date.tzinfo is None:
            self.end_date = timezone.make_aware(self.end_date, timezone.utc)

        # Now compare the coupon's time range with the current UTC time
        if self.is_active and self.start_date <= now <= self.end_date:
            return True
        return False
