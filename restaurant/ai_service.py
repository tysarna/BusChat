import json
from datetime import datetime
from django.conf import settings
import anthropic


def get_menu_text() -> str:
    from .models import MenuItem
    category_labels = {
        'appetizer': 'APPETIZERS',
        'main': 'MAIN COURSES',
        'side': 'SIDES',
        'dessert': 'DESSERTS',
        'drink': 'DRINKS',
    }
    lines = []
    current_cat = None
    for item in MenuItem.objects.filter(is_available=True).order_by('category', 'name'):
        if item.category != current_cat:
            current_cat = item.category
            lines.append(f'\n{category_labels.get(current_cat, current_cat.upper())}')
        tags = []
        if item.is_vegan:
            tags.append('vegan')
        elif item.is_vegetarian:
            tags.append('vegetarian')
        if item.is_gluten_free:
            tags.append('gluten-free')
        if item.is_spicy:
            tags.append('spicy')
        tag_str = f' ({", ".join(tags)})' if tags else ''
        allergen_str = f' [allergens: {item.allergens}]' if item.allergens else ''
        lines.append(f'- {item.name} ${item.price}{tag_str}: {item.description}{allergen_str}')
    return '\n'.join(lines)


def build_system_prompt() -> str:
    now = datetime.now()
    date_str = now.strftime('%A, %B %d, %Y')
    time_str = now.strftime('%I:%M %p')
    menu_text = get_menu_text()
    return f"""You are Zara, the warm and knowledgeable AI assistant for Zara's Mediterranean Kitchen in Columbus, Ohio.

RESTAURANT INFO:
- Address: 1842 High Street, Columbus, OH 43210
- Phone: (614) 555-0192
- Hours: Mon-Thu 11am-9pm | Fri-Sat 11am-10pm | Sun 12pm-8pm
- Pickup orders only (no delivery). Pickup ready in 15-20 minutes.
- Parking: Street parking on High St, free lot behind building on Chittenden Ave

TODAY: {date_str} at {time_str} (Eastern Time)

YOUR PERSONALITY:
- Warm, knowledgeable, and genuinely enthusiastic about Mediterranean food
- Use the customer's name once you learn it
- Never be pushy; recommend when asked or when it's clearly helpful
- Keep responses concise for mobile: 2-4 sentences max unless you're listing menu items
- Use line breaks to format lists clearly

WHAT YOU CAN HELP WITH:
1. Answer questions about the menu, ingredients, allergens, and dietary restrictions
2. Make personalized food recommendations based on preferences
3. Help customers build and confirm pickup orders
4. Share hours, location, and general restaurant information

FULL MENU:
{menu_text}

ORDERING PROCESS:
- When a customer wants to order, collect: item(s) with quantity, their name, phone number, and pickup time
- Confirm the complete order summary with subtotal before finalizing
- After they confirm, tell them their order is ready and they can review it at the Cart page
- Tax is 8%. Pickup times: ASAP (~15-20 min), or a specific time they prefer

IMPORTANT RULES:
- Do NOT discuss competitors or make price comparisons
- Do NOT make up prices or items not listed in the menu above
- If asked about delivery, explain warmly that we're pickup-only
- If asked whether we're open right now, check the current time ({time_str}) against our hours above
- If you don't know something, say so honestly rather than guessing"""


def get_conversation_history(conversation_id: int) -> list:
    from .models import Message
    messages = Message.objects.filter(
        conversation_id=conversation_id
    ).order_by('-created_at')[:12]
    history = []
    for msg in reversed(list(messages)):
        history.append({'role': msg.role, 'content': msg.content})
    return history


def detect_intent(text: str) -> str:
    text_lower = text.lower()
    if any(w in text_lower for w in ['order', "i'll have", "i'd like", 'give me', 'get me', 'want to order', 'can i get']):
        return 'order_request'
    if any(w in text_lower for w in ['recommend', 'suggest', "what's good", "what's popular", 'popular', 'best', 'favorite', 'what should']):
        return 'recommendation'
    if any(w in text_lower for w in ['hour', 'open', 'close', 'when', 'time', 'schedule']):
        return 'hours_question'
    if any(w in text_lower for w in ['where', 'address', 'location', 'direction', 'find you', 'parking']):
        return 'location_question'
    if any(w in text_lower for w in ['vegan', 'vegetarian', 'gluten', 'allerg', 'dairy', 'nut', 'halal', 'kosher', 'lactose', 'spicy']):
        return 'dietary_question'
    if any(w in text_lower for w in ['menu', 'price', 'cost', 'how much', 'what do you', 'do you have', 'ingredient']):
        return 'menu_question'
    return 'general'


def stream_chat_response(conversation_id: int, user_message: str):
    history = get_conversation_history(conversation_id)
    system_prompt = build_system_prompt()
    api_key = settings.ANTHROPIC_API_KEY
    if not api_key:
        yield 'data: I\'m sorry, the AI service is not configured. Please contact the restaurant directly at (614) 555-0192.\n\n'
        yield 'data: [DONE]\n\n'
        return

    client = anthropic.Anthropic(api_key=api_key)

    # Build messages — history already includes the latest user message from DB
    # We pass the last N-1 turns as history context, then the current message
    messages_for_api = history[:-1] if history else []
    messages_for_api.append({'role': 'user', 'content': user_message})

    try:
        with client.messages.stream(
            model='claude-sonnet-4-6',
            max_tokens=1024,
            system=[
                {
                    'type': 'text',
                    'text': system_prompt,
                    'cache_control': {'type': 'ephemeral'},
                }
            ],
            messages=messages_for_api,
        ) as stream:
            for text_chunk in stream.text_stream:
                escaped = text_chunk.replace('\n', '\\n')
                yield f'data: {json.dumps(text_chunk)}\n\n'
            final_msg = stream.get_final_message()
            total_tokens = final_msg.usage.output_tokens if final_msg.usage else None
            yield f'data: [DONE:{total_tokens}]\n\n'
    except anthropic.APIError as e:
        yield f'data: {json.dumps(f"I apologize, I encountered an issue. Please try again or call us at (614) 555-0192.")}\n\n'
        yield 'data: [DONE]\n\n'


def save_assistant_message(conversation_id: int, content: str, tokens: int = None):
    from .models import Message, Conversation
    from django.db.models import F
    Message.objects.create(
        conversation_id=conversation_id,
        role='assistant',
        content=content,
        tokens_used=tokens,
    )
    Conversation.objects.filter(pk=conversation_id).update(message_count=F('message_count') + 1)
