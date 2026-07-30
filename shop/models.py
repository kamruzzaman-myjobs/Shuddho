from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
# from cloudinary.models import CloudinaryField
from django.core.exceptions import ValidationError

class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    parent = models.ForeignKey(
        'self', on_delete=models.CASCADE,
        null=True, blank=True, related_name='children'
    )

    class Meta:
        verbose_name_plural = 'Categories'

    def clean(self):
        # শুধু already-saved object (pk আছে) এর ক্ষেত্রে চেক করো, নতুন object এ না
        if self.pk is not None and self.parent_id == self.pk:
            raise ValidationError("A category cannot be its own parent.")

        # circular reference আটকাও (A -> B -> A)
        p = self.parent
        depth = 0
        while p:
            if self.pk is not None and p.id == self.pk:
                raise ValidationError("Circular category reference detected — this creates an infinite loop.")
            p = p.parent
            depth += 1
            if depth > 20:
                raise ValidationError("Category hierarchy is too deep or circular.")

    def save(self, *args, **kwargs):
        self.full_clean()   # save করার আগে সবসময় validation চালাও
        super().save(*args, **kwargs)

    def __str__(self):
        full = self.name
        p = self.parent
        seen = {self.id}
        while p:
            if p.id in seen:   # সেফটি নেট — loop হলেও crash করবে না
                break
            seen.add(p.id)
            full = f"{p.name} > {full}"
            p = p.parent
        return full

    def get_all_children_ids(self):
        ids = [self.id]
        for child in self.children.all():
            if child.id != self.id:   # সেফটি চেক
                ids.extend(child.get_all_children_ids())
        return ids


        

class Product(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=200, unique=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2) 
    stock = models.PositiveBigIntegerField(default=1)
    available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    image = models.ImageField(upload_to='products/%Y/%m/%d', blank=True, null=True) # products/25/10/2025
    # image = CloudinaryField('image', blank=True, null=True)

    # Flash Sale fields
    is_flash_sale = models.BooleanField(default=False, help_text="Show this product in the Flash Sale section")
    discount_price = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        help_text="Sale price during flash sale (must be lower than regular price)"
    )
    flash_sale_end = models.DateTimeField(
        null=True, blank=True,
        help_text="Flash sale countdown ends at this date/time"
    )

    def get_display_price(self):
        """Return discounted price if an active flash sale exists, else regular price."""
        from django.utils import timezone
        if self.is_flash_sale and self.discount_price and self.flash_sale_end and self.flash_sale_end > timezone.now():
            return self.discount_price
        return self.price

    def get_discount_percent(self):
        if self.is_flash_sale and self.discount_price and self.price:
            return round((1 - (self.discount_price / self.price)) * 100)
        return 0

    
    class Meta:
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['available']),
        ]

    def __str__(self):
        return self.name 
    
    # Get average rating for the product
    def average_ratings(self):
        """Calculate and return average rating for the product."""
        ratings = self.ratings.all()
        if ratings.count() > 0:
            # Fixed: Method name typo (average_ratins -> average_ratings)
            return round(sum([i.rating for i in ratings]) / ratings.count(), 2)
        return 0  # Return 0 if no ratings exist




class Rating(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='ratings')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ('product', 'user')  # Prevent multiple ratings from same user per product
    
    def __str__(self):
        return f"{self.user.username} - {self.product.name} - {self.rating}"
    


    
class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    session_key = models.CharField(max_length=40, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['session_key']),
        ]
        
    # total price
    def get_total_price(self):
        return sum(item.get_cost() for item in self.items.all()) # 100
    # total koita item
    def get_total_items(self):
        return sum(item.quantity for item in self.items.all()) 
    


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE) 
    quantity = models.PositiveBigIntegerField(default=1)

    class Meta:
       unique_together = ('cart', 'product')
    
    def __str__(self):
        return f"{self.quantity} X {self.product.name}" # 4 X Shirt
   
    def get_cost(self):
        return self.quantity*self.product.price         # 20
        # return self.quantity * self.price   # self.price ব্যবহার করো
    


    
class Order(models.Model):
    STATUS = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('canceled', 'Canceled'),
    ]
    PAYMENT_METHODS = (
        ('cod', 'Cash On Delivery'),
        ('sslcommerz', 'SSLCommerz'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    session_key = models.CharField(max_length=40, null=True, blank=True)
    username = models.CharField(max_length=100)
    address = models.TextField()
    phone = models.CharField(max_length=12)
    note = models.TextField(blank=True)
    paid = models.BooleanField(default=False)
    transaction_id = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=10, choices=STATUS, default='pending')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)


    def __str__(self):
        return f"Order #{self.id}" # Order #2
    
    # order item er sum lagbe
    def get_total_cost(self):
        return sum(item.get_cost() for item in self.order_items.all()) # 100
    

    

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveBigIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    
    def get_cost(self):
        return self.quantity*self.price  # 20
        




class PromoBanner(models.Model):
    title = models.CharField(
        max_length=150, blank=True,
        help_text="Internal name only — not shown on the website"
    )
    image = models.ImageField(upload_to='banners/')
    link = models.URLField(
        blank=True,
        help_text="Optional — where visitors go if they click the banner"
    )
    order = models.PositiveIntegerField(
        default=0,
        help_text="Smaller number shows first (0, 1, 2 ...)"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', '-created_at']

    def __str__(self):
        return self.title or f"Banner #{self.id}"