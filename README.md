# Zara's Mediterranean Kitchen — AI Assistant

A live AI-powered restaurant assistant built with Django + Claude, deployed on AWS Elastic Beanstalk.

**[Live Demo →] http://buschat-prod.eba-hrtkkb3w.us-east-1.elasticbeanstalk.com**

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.12, Django 5.1 |
| AI | Anthropic Claude Sonnet 4.6 (streaming + prompt caching) |
| Frontend | Tailwind CSS (Play CDN), HTMX 1.9, Vanilla JS |
| Database | SQLite (dev + prod demo) |
| Static files | WhiteNoise |
| Deployment | AWS Elastic Beanstalk (Python 3.12 platform), t3.micro |

---

## Features

- **Streaming AI chat** — responses stream character-by-character via Server-Sent Events
- **Full menu Q&A** — Claude knows the entire menu with prices, dietary tags, allergens
- **Food recommendations** — personalized suggestions based on preferences
- **Pickup order flow** — collect items, name, phone, pickup time; confirm before placing
- **Browse menu** — filterable menu page with category tabs and Add to Cart
- **Order cart** — HTMX-powered cart with quantity controls and order confirmation
- **Analytics dashboard** — intent tracking (menu questions, orders, recommendations, etc.)
- **Prompt caching** — system prompt cached to reduce API costs ~50% on follow-up messages
- **Mobile-first** — responsive design, 44px touch targets, no iOS zoom issues

---

## Architecture

```
Browser ←→ nginx (AWS EB) ←→ gunicorn ←→ Django
                                              │
                                    Claude API (Anthropic)
                                              │
                                        SQLite (db.sqlite3)
```

**Chat flow:**
1. User submits message → POST `/chat/send/`
2. Django saves user message to DB, builds system prompt from live menu data
3. Opens `client.messages.stream()` with last 12 messages as context
4. Returns `StreamingHttpResponse` (SSE) — each text delta yielded as `data: {...}`
5. Browser JS accumulates chunks, renders live into AI bubble
6. On stream end, JS POSTs complete text to `/chat/save-response/` for DB persistence

**Key files:**
- [`restaurant/ai_service.py`](restaurant/ai_service.py) — Claude integration, system prompt, streaming
- [`restaurant/views.py`](restaurant/views.py) — all 9 view functions
- [`restaurant/templates/restaurant/chat.html`](restaurant/templates/restaurant/chat.html) — chat UI
- [`restaurant/static/restaurant/js/chat.js`](restaurant/static/restaurant/js/chat.js) — SSE stream handler

---

## Local Setup

```bash
# 1. Clone and enter directory
git clone <repo-url>
cd BusChat

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env and set ANTHROPIC_API_KEY=sk-ant-...

# 5. Run migrations and seed menu data
python manage.py migrate
python manage.py seed_data

# 6. Start dev server
python manage.py runserver

# 7. Open http://localhost:8000
```

---

## AWS Deployment (Elastic Beanstalk)

```bash
# Install EB CLI
pip install awsebcli

# Initialize (first time)
eb init buschat-restaurant --region us-east-2 --platform "Python 3.12"

# Create environment
eb create buschat-prod --instance-type t3.micro --single

# Set secrets
eb setenv \
  DJANGO_SECRET_KEY="<50-char-random-string>" \
  ANTHROPIC_API_KEY="sk-ant-..." \
  DJANGO_SETTINGS_MODULE="buschat.settings.production"

# Deploy
eb deploy

# Open live URL
eb open
```

Migrations, static file collection, and menu seeding run automatically on each deploy via `.ebextensions/01_django.config`.

---

## Sample Prompts

| User says | What happens |
|-----------|-------------|
| "What are your vegan options?" | Lists all vegan items with prices |
| "I'd like 2 chicken shawarmas for pickup" | Starts order collection flow |
| "What's your most popular dish?" | Recommends top items with descriptions |
| "Are you open right now?" | Checks current time against restaurant hours |
| "Do you have anything gluten-free under $15?" | Filters menu by dietary + price |
| "What's in the Kunafa?" | Describes ingredients and allergens |

---

## What I'd Improve With More Time


1. **Voice support** — Web Speech API for input + TTS for responses
2. **Image thumbnails** — photo for each menu item via S3
3. **Auth + order history** — phone number–based login to track past orders
4. **Multi-language** — Claude handles Spanish/Arabic natively; just needs a language selector
