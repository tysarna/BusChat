from django.db import models
from decimal import Decimal


class MenuItem(models.Model):
    CATEGORY_CHOICES = [
        ('appetizer', 'Appetizer'),
        ('main', 'Main Course'),
        ('side', 'Side Dish'),
        ('dessert', 'Dessert'),
        ('drink', 'Drink'),
    ]
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    description = models.TextField()
    price = models.DecimalField(max_digits=6, decimal_places=2)
    is_vegetarian = models.BooleanField(default=False)
    is_vegan = models.BooleanField(default=False)
    is_gluten_free = models.BooleanField(default=False)
    is_spicy = models.BooleanField(default=False)
    is_available = models.BooleanField(default=True)
    calories = models.PositiveIntegerField(null=True, blank=True)
    allergens = models.CharField(max_length=300, blank=True)

    class Meta:
        ordering = ['category', 'name']

    def __str__(self):
        return f'{self.name} (${self.price})'

    def dietary_tags(self):
        tags = []
        if self.is_vegan:
            tags.append('Vegan')
        elif self.is_vegetarian:
            tags.append('Vegetarian')
        if self.is_gluten_free:
            tags.append('GF')
        if self.is_spicy:
            tags.append('Spicy')
        return tags


class Conversation(models.Model):
    session_key = models.CharField(max_length=40, db_index=True)
    started_at = models.DateTimeField(auto_now_add=True)
    last_active = models.DateTimeField(auto_now=True)
    message_count = models.PositiveIntegerField(default=0)
    topics_discussed = models.JSONField(default=list)

    def __str__(self):
        return f'Conversation {self.pk} ({self.session_key[:8]}...)'


class Message(models.Model):
    ROLE_CHOICES = [('user', 'User'), ('assistant', 'Assistant')]
    INTENT_CHOICES = [
        ('menu_question', 'Menu Question'),
        ('order_request', 'Order Request'),
        ('recommendation', 'Recommendation'),
        ('hours_question', 'Hours Question'),
        ('location_question', 'Location Question'),
        ('dietary_question', 'Dietary Question'),
        ('general', 'General'),
    ]
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    tokens_used = models.PositiveIntegerField(null=True, blank=True)
    intent = models.CharField(max_length=20, choices=INTENT_CHOICES, default='general')

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'[{self.role}] {self.content[:60]}'


class Order(models.Model):
    STATUS_CHOICES = [
        ('cart', 'In Cart'),
        ('placed', 'Placed'),
        ('confirmed', 'Confirmed'),
        ('ready', 'Ready for Pickup'),
    ]
    conversation = models.ForeignKey(Conversation, on_delete=models.SET_NULL, null=True, blank=True)
    session_key = models.CharField(max_length=40, db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='cart')
    customer_name = models.CharField(max_length=200, blank=True)
    customer_phone = models.CharField(max_length=20, blank=True)
    pickup_time = models.CharField(max_length=100, blank=True)
    special_instructions = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Order {self.pk} [{self.status}] - {self.customer_name or "Guest"}'

    @property
    def subtotal(self):
        return sum(item.line_total for item in self.items.all())

    @property
    def tax(self):
        return round(self.subtotal * Decimal('0.08'), 2)

    @property
    def total(self):
        return self.subtotal + self.tax

    @property
    def item_count(self):
        return sum(item.quantity for item in self.items.all())


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    menu_item = models.ForeignKey(MenuItem, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=6, decimal_places=2)
    special_request = models.CharField(max_length=300, blank=True)

    def __str__(self):
        return f'{self.quantity}x {self.menu_item.name}'

    @property
    def line_total(self):
        return self.unit_price * self.quantity
