from django.contrib import admin
from . import models 
# Register your models here.

@admin.register(models.Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'parent']
    list_filter = ['parent']
    prepopulated_fields = {'slug': ('name',)}
    autocomplete_fields = ['parent']
    search_fields = ['name']

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "parent":
            # URL থেকে current object-এর id বের করে নিজেকে বাদ দাও
            obj_id = request.resolver_match.kwargs.get('object_id')
            if obj_id:
                kwargs["queryset"] = models.Category.objects.exclude(pk=obj_id)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
        


@admin.register(models.Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'price', 'discount_price', 'is_flash_sale', 'flash_sale_end', 'stock', 'available', 'created_at', 'updated_at']
    list_filter = ['available', 'category', 'is_flash_sale']
    list_editable = ['is_flash_sale', 'discount_price', 'flash_sale_end']
    search_fields = ['name']
    prepopulated_fields = {'slug' : ('name', )}



# Fixed: Indentation error corrected
admin.site.register(models.Rating)
admin.site.register(models.Cart)
admin.site.register(models.CartItem)



# admin.site.register(models.Order)
# admin.site.register(models.OrderItem)

class OrderItemInline(admin.TabularInline):
    model = models.OrderItem
    extra = 0
    readonly_fields = ['product', 'quantity', 'price']
    can_delete = False


@admin.register(models.Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'username', 'phone', 'get_customer', 'status', 'payment_method', 'paid', 'get_total_display', 'created_at']
    list_filter = ['status', 'payment_method', 'paid', 'created_at']
    search_fields = ['username', 'phone', 'address', 'transaction_id', 'user__username', 'user__email']
    readonly_fields = ['user', 'session_key', 'transaction_id', 'created_at', 'updated_at']
    inlines = [OrderItemInline]

    fieldsets = (
        ('Customer Info', {
            'fields': ('user', 'username', 'phone', 'address', 'note')
        }),
        ('Order Status', {
            'fields': ('status', 'payment_method', 'paid', 'transaction_id')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )

    def get_customer(self, obj):
        if obj.user:
            return f"{obj.user.username} ({obj.user.email})"
        return "Guest"
    get_customer.short_description = "Customer"

    def get_total_display(self, obj):
        return f"৳{obj.get_total_cost()}"
    get_total_display.short_description = "Total"





@admin.register(models.PromoBanner)
class PromoBannerAdmin(admin.ModelAdmin):
    list_display = ['title', 'image', 'order', 'is_active', 'created_at']
    list_editable = ['order', 'is_active']
    list_filter = ['is_active']