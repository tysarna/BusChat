from django.shortcuts import render, get_object_or_404, redirect
from django.http import StreamingHttpResponse, JsonResponse, HttpResponse
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Count
import json

from .models import Conversation, Message, MenuItem, Order, OrderItem
from . import ai_service


def _get_or_create_conversation(request):
    if not request.session.session_key:
        request.session.create()
    session_key = request.session.session_key
    conversation, _ = Conversation.objects.get_or_create(session_key=session_key)
    return conversation


def _get_or_create_cart(request):
    if not request.session.session_key:
        request.session.create()
    session_key = request.session.session_key
    order, _ = Order.objects.get_or_create(session_key=session_key, status='cart')
    return order


def chat_view(request):
    conversation = _get_or_create_conversation(request)
    messages = conversation.messages.all()
    cart = Order.objects.filter(session_key=request.session.session_key, status='cart').first()
    cart_count = cart.item_count if cart else 0
    return render(request, 'restaurant/chat.html', {
        'messages': messages,
        'cart_count': cart_count,
    })


@require_POST
def chat_send(request):
    conversation = _get_or_create_conversation(request)
    user_message = request.POST.get('message', '').strip()
    if not user_message:
        return HttpResponse(status=400)

    intent = ai_service.detect_intent(user_message)
    Message.objects.create(
        conversation=conversation,
        role='user',
        content=user_message,
        intent=intent,
    )
    conversation.message_count += 1
    conversation.save(update_fields=['message_count', 'last_active'])

    def event_stream():
        for chunk in ai_service.stream_chat_response(conversation.pk, user_message):
            yield chunk

    response = StreamingHttpResponse(event_stream(), content_type='text/event-stream')
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'
    return response


@require_POST
def chat_save_response(request):
    conversation = _get_or_create_conversation(request)
    data = json.loads(request.body)
    content = data.get('content', '')
    tokens = data.get('tokens', None)
    if content:
        Message.objects.create(
            conversation=conversation,
            role='assistant',
            content=content,
            tokens_used=tokens,
        )
        conversation.message_count += 1
        conversation.save(update_fields=['message_count', 'last_active'])
    return JsonResponse({'status': 'ok'})


def menu_view(request):
    items_by_category = {}
    category_order = ['appetizer', 'main', 'side', 'dessert', 'drink']
    category_labels = dict(MenuItem.CATEGORY_CHOICES)
    for cat in category_order:
        items = MenuItem.objects.filter(category=cat, is_available=True)
        if items.exists():
            items_by_category[cat] = {
                'label': category_labels[cat],
                'items': items,
            }
    cart = Order.objects.filter(session_key=request.session.session_key or '', status='cart').first()
    cart_count = cart.item_count if cart else 0
    return render(request, 'restaurant/menu.html', {
        'items_by_category': items_by_category,
        'cart_count': cart_count,
    })


def cart_view(request):
    if not request.session.session_key:
        request.session.create()
    cart = Order.objects.filter(session_key=request.session.session_key, status='cart').prefetch_related('items__menu_item').first()
    return render(request, 'restaurant/cart.html', {
        'cart': cart,
        'cart_count': cart.item_count if cart else 0,
    })


@require_POST
def cart_add(request):
    item_id = request.POST.get('item_id')
    menu_item = get_object_or_404(MenuItem, pk=item_id, is_available=True)
    cart = _get_or_create_cart(request)
    order_item, created = OrderItem.objects.get_or_create(
        order=cart,
        menu_item=menu_item,
        defaults={'unit_price': menu_item.price, 'quantity': 1},
    )
    if not created:
        order_item.quantity += 1
        order_item.save(update_fields=['quantity'])
    cart_count = cart.item_count
    if request.headers.get('HX-Request'):
        hidden = 'hidden' if cart_count == 0 else 'inline-flex'
        return HttpResponse(
            f'<span id="cart-badge" class="{hidden} absolute -top-1 -right-1 bg-terracotta text-white text-xs '
            f'w-5 h-5 rounded-full items-center justify-center font-bold">{cart_count}</span>'
        )
    return redirect('cart')


@require_POST
def cart_update(request):
    item_id = request.POST.get('item_id')
    action = request.POST.get('action')
    cart = Order.objects.filter(session_key=request.session.session_key or '', status='cart').first()
    if not cart:
        return redirect('cart')
    try:
        order_item = cart.items.get(pk=item_id)
        if action == 'increase':
            order_item.quantity += 1
            order_item.save(update_fields=['quantity'])
        elif action == 'decrease':
            if order_item.quantity > 1:
                order_item.quantity -= 1
                order_item.save(update_fields=['quantity'])
            else:
                order_item.delete()
        elif action == 'remove':
            order_item.delete()
    except OrderItem.DoesNotExist:
        pass
    cart.refresh_from_db()
    return render(request, 'restaurant/partials/cart_summary.html', {'cart': cart})


@require_POST
def cart_place_order(request):
    cart = Order.objects.filter(session_key=request.session.session_key or '', status='cart').first()
    if not cart or not cart.items.exists():
        return redirect('cart')
    cart.customer_name = request.POST.get('customer_name', '')
    cart.customer_phone = request.POST.get('customer_phone', '')
    cart.pickup_time = request.POST.get('pickup_time', 'ASAP')
    cart.special_instructions = request.POST.get('special_instructions', '')
    cart.status = 'placed'
    cart.save()
    return render(request, 'restaurant/order_confirmed.html', {'order': cart})


def analytics_view(request):
    intent_counts = (
        Message.objects
        .filter(role='user')
        .values('intent')
        .annotate(count=Count('id'))
        .order_by('-count')
    )
    total_conversations = Conversation.objects.count()
    total_messages = Message.objects.count()
    total_orders = Order.objects.exclude(status='cart').count()
    cart = Order.objects.filter(session_key=request.session.session_key or '', status='cart').first()
    cart_count = cart.item_count if cart else 0
    return render(request, 'restaurant/analytics.html', {
        'intent_counts': intent_counts,
        'total_conversations': total_conversations,
        'total_messages': total_messages,
        'total_orders': total_orders,
        'cart_count': cart_count,
    })
