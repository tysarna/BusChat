from django.contrib import admin
from .models import MenuItem, Conversation, Message, Order, OrderItem


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'is_vegetarian', 'is_vegan', 'is_gluten_free', 'is_spicy', 'is_available']
    list_filter = ['category', 'is_vegetarian', 'is_vegan', 'is_gluten_free', 'is_available']
    search_fields = ['name', 'description']
    list_editable = ['is_available', 'price']


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ['pk', 'session_key', 'message_count', 'started_at', 'last_active']
    readonly_fields = ['started_at', 'last_active']


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['pk', 'conversation', 'role', 'intent', 'tokens_used', 'created_at']
    list_filter = ['role', 'intent']
    readonly_fields = ['created_at']


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['line_total']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['pk', 'customer_name', 'customer_phone', 'status', 'item_count', 'created_at']
    list_filter = ['status']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [OrderItemInline]
