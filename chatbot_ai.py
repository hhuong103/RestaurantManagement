"""
AI-Powered Ordering Chatbot Engine
Uses Google Gemini to power a conversational ordering agent.
"""
import os
import json
import re
from typing import Optional, Dict, Any, List


def _load_genai():
    """Load and configure the Gemini client."""
    try:
        import google.generativeai as genai
    except ImportError:
        return None, "google-generativeai library not installed."

    api_key = (os.getenv("GEMINI_API_KEY") or "").strip()
    if not api_key:
        return None, "Missing GEMINI_API_KEY in .env"

    genai.configure(api_key=api_key)
    return genai, None


def _pick_model():
    """Return candidate model names in priority order."""
    env_model = (os.getenv("GEMINI_MODEL") or "").strip()
    candidates = []
    if env_model:
        candidates.append(env_model)
    candidates += ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"]
    return candidates


def _build_system_prompt(menu_items: list, tables: list, cart: dict,
                         username: Optional[str] = None) -> str:
    """Build a comprehensive system prompt for the ordering agent."""

    # Format menu catalog
    menu_text = ""
    if menu_items:
        for item in menu_items:
            img_tag = f" [image: {item.get('image', 'none')}]" if item.get('image') else ""
            menu_text += (
                f"  - ID:{item['id']} | {item['name']} | "
                f"{item['price']:,.0f} VND | "
                f"Category: {item.get('category', 'N/A')} | "
                f"Rating: {item.get('rating', 'N/A')}/5{img_tag}\n"
                f"    Description: {item.get('description', 'No description')}\n"
            )
    else:
        menu_text = "  (No menu items available)\n"

    # Format tables
    table_names = [t['name'] if isinstance(t, dict) else t[0] for t in tables] if tables else []
    tables_text = ", ".join(table_names) if table_names else "No tables available"

    # Format current cart
    cart_text = ""
    if cart:
        total = 0
        for k, v in cart.items():
            qty = int(v.get('quantity', 1))
            price = float(v.get('price', 0))
            cart_text += f"  - {v.get('name')} x{qty} — {price:,.0f} VND each\n"
            total += price * qty
        cart_text += f"  Total: {total:,.0f} VND\n"
    else:
        cart_text = "  (Empty)\n"

    greeting_name = f" {username}" if username else ""

    return f"""You are **Aria**, an AI ordering assistant for **GreenBite Vegetarian Restaurant**.

## YOUR PERSONALITY
- Friendly, helpful, concise, and professional
- Use emojis sparingly but effectively (🍜 🔥 ✅ 🛒)
- Speak naturally, not robotically
- Keep responses short — 2-4 sentences max unless showing menu items

## RESTAURANT INFO
- Name: GreenBite Vegetarian Restaurant
- Address: 123 Z15 St, Central Thai Nguyen, VN
- Phone: +84 123 456 789
- Hours: 7:00 - 22:00 daily
- Payment methods: Cash at restaurant, Bank transfer
- Available tables: {tables_text}

## FULL MENU CATALOG
{menu_text}

## CUSTOMER'S CURRENT CART
{cart_text}

## YOUR CAPABILITIES — 6-STAGE ORDERING FLOW

### Stage 1: Greeting & Intent Detection
- Greet the customer{greeting_name} warmly
- Detect intent: ordering, browsing menu, checking order status, asking questions
- If returning customer, acknowledge them

### Stage 2: Product Discovery & Recommendation
- Help customers find items using natural language ("something spicy", "under 50000 VND")
- Show matching items from the menu with name, price, and brief description
- Suggest popular or highly-rated items when asked for recommendations
- Present items in a clear numbered list format

### Stage 3: Order Clarification & Customization
- After customer selects items, confirm the selection
- Ask for quantity
- Accept special requests or modifications ("extra spicy", "no onions")
- Validate items exist in the menu catalog above

### Stage 4: Cart Management
- Add/remove items from cart as requested
- Show cart summary when asked
- Apply any mentioned promo codes (acknowledge them)

### Stage 5: Order Placement
- When customer wants to place order, summarize everything
- Ask for final confirmation
- Tell them to proceed to checkout

### Stage 6: Post-Order Support
- Answer questions about order status
- Provide restaurant information
- Handle complaints empathetically

## CRITICAL RESPONSE FORMAT
You MUST respond in valid JSON format ONLY. No text outside the JSON.
Your response must follow this exact structure:

```json
{{
  "message": "Your conversational reply in HTML. Use <br> for line breaks. Use <b> for bold.",
  "action": null,
  "action_data": null,
  "suggestions": ["suggestion 1", "suggestion 2"],
  "items_to_show": null
}}
```

### Available actions:
- `"add_to_cart"` — action_data: {{"item_id": <int>, "quantity": <int>, "special_requests": "<string or null>"}}
- `"remove_from_cart"` — action_data: {{"item_id": <int>}}
- `"show_cart"` — action_data: null
- `"clear_cart"` — action_data: null
- `"place_order"` — action_data: null (signals the user is ready to checkout)
- `null` — no action, just conversation

### items_to_show format — MANDATORY when recommending or mentioning ANY dishes:
```json
[
  {{"id": 1, "name": "Dish Name", "price": 50000, "description": "Brief desc", "image": "filename.jpg", "category": "Category"}}
]
```

### suggestions: array of 2-4 short clickable button labels

## RULES
1. ALWAYS respond in valid JSON
2. Only reference items that exist in the MENU CATALOG above. Match by name or ID
3. When adding to cart, use the exact item ID from the catalog
4. Keep messages concise and friendly
5. If a customer asks for something not on the menu, suggest similar available items
6. For multi-item orders, add them ONE AT A TIME (one action per response), then ask about the next
7. Use VND currency format with commas (e.g., 50,000 VND)
8. Respond in the same language the customer uses (Vietnamese or English)
9. **CRITICAL: Whenever you mention, recommend, list, or suggest ANY dishes — you MUST populate items_to_show with the full item details including the "image" field from the catalog.** This is how the frontend renders product cards with images. If you skip items_to_show, the user sees only text with no pictures.
10. When a customer says they want to add something, IMMEDIATELY use the add_to_cart action. Do NOT just describe the item — actually add it.
11. After adding items to cart, always suggest: "View my cart", "Add more items", "Proceed to checkout"
12. When the customer wants to place an order or checkout, use the place_order action.
13. **CRITICAL LIMIT: NEVER return more than 5 items in `items_to_show` at one time.** If the user asks for the "full menu", pick the top 5 most popular or relevant items and tell them there are more. A large JSON payload will crash the system.
"""


def _try_parse_json(text: str) -> Optional[dict]:
    """Robustly parse JSON from Gemini's response."""
    if not text:
        return None

    t = text.strip()

    # Remove markdown code fences
    t = re.sub(r'^```(?:json)?\s*', '', t, flags=re.IGNORECASE | re.MULTILINE)
    t = re.sub(r'\s*```$', '', t, flags=re.MULTILINE)
    t = t.strip()

    # Try direct parse
    try:
        return json.loads(t)
    except Exception:
        pass

    # Try to find first JSON object
    m = re.search(r'\{.*\}', t, flags=re.DOTALL)
    if m:
        try:
            return json.loads(m.group(0))
        except Exception:
            pass

    return None


def _make_fallback_response(message: str, suggestions: list = None) -> dict:
    """Create a fallback response when AI parsing fails."""
    return {
        "message": message,
        "action": None,
        "action_data": None,
        "suggestions": suggestions or ["🍽️ View menu", "🛒 Show cart", "ℹ️ Restaurant info"],
        "items_to_show": None
    }


def chat_with_ai(
    conversation_history: List[Dict[str, str]],
    user_message: str,
    menu_items: list,
    tables: list,
    cart: dict,
    username: Optional[str] = None
) -> dict:
    """
    Send a message to the AI ordering agent and get a structured response.

    Args:
        conversation_history: List of {"role": "user"|"model", "parts": [str]}
        user_message: The new user message
        menu_items: List of menu item dicts from MenuModel
        tables: List of available table dicts/rows
        cart: Current session cart dict
        username: Logged-in username or None

    Returns:
        dict with keys: message, action, action_data, suggestions, items_to_show
    """
    genai, err = _load_genai()
    if err:
        return _make_fallback_response(
            f"⚠️ AI service unavailable: {err}. Please try the manual menu.",
            ["🍽️ Browse menu", "🛒 View cart"]
        )

    system_prompt = _build_system_prompt(menu_items, tables, cart, username)

    # Build history WITHOUT the last user message (send_message will add it)
    # Filter out the last entry if it's the user message we're about to send
    history_for_chat = []
    for entry in conversation_history:
        # Skip entries that don't have proper format
        if not isinstance(entry, dict) or 'role' not in entry:
            continue
        role = entry.get('role', '')
        parts = entry.get('parts', [])
        if isinstance(parts, str):
            parts = [parts]
        if not parts or not parts[0]:
            continue
        history_for_chat.append({
            'role': role,
            'parts': [str(p) for p in parts]
        })

    # Remove the last entry if it's the user message we just added
    if (history_for_chat and
        history_for_chat[-1].get('role') == 'user' and
        history_for_chat[-1].get('parts', [''])[0] == user_message):
        history_for_chat = history_for_chat[:-1]

    # Try each model candidate
    for model_name in _pick_model():
        try:
            model = genai.GenerativeModel(
                model_name,
                system_instruction=system_prompt
            )

            chat = model.start_chat(history=history_for_chat)

            response = chat.send_message(
                user_message,
                generation_config={
                    "temperature": 0.7,
                    "max_output_tokens": 4096,
                    "response_mime_type": "application/json",
                }
            )

            response_text = (getattr(response, 'text', '') or '').strip()

            # Parse the JSON response
            parsed = _try_parse_json(response_text)

            if parsed and "message" in parsed:
                return {
                    "message": parsed.get("message", ""),
                    "action": parsed.get("action"),
                    "action_data": parsed.get("action_data"),
                    "suggestions": parsed.get("suggestions", []),
                    "items_to_show": parsed.get("items_to_show"),
                }

            # If parsing failed but we got text, use it as message
            if response_text:
                return _make_fallback_response(response_text)

        except Exception as e:
            error_str = str(e).lower()
            print(f"[AI Chat] Error with model {model_name}: {e}")
            # If it's a model-not-found error, try next model
            if "404" in error_str or "not found" in error_str:
                continue
            if "api key" in error_str or "401" in error_str:
                return _make_fallback_response(
                    "⚠️ API key issue. Please check the GEMINI_API_KEY configuration.",
                    ["🍽️ Browse menu manually"]
                )
            # For other errors, return user-friendly message
            return _make_fallback_response(
                "I'm having a momentary issue. Please try again! 🙏",
                ["🍽️ View menu", "🛒 Show cart", "🔄 Try again"]
            )

    return _make_fallback_response(
        "AI service is temporarily unavailable. Please try again later.",
        ["🍽️ Browse menu manually"]
    )



def get_greeting_message(username: Optional[str] = None) -> dict:
    """Generate the initial greeting message."""
    name_part = f" {username}" if username else ""
    return {
        "message": (
            f"Hi there{name_part}! 👋 I'm <b>Aria</b>, your ordering assistant at "
            f"<b>GreenBite Restaurant</b>.<br><br>"
            f"I can help you explore our menu, find the perfect dish, "
            f"and place your order — all through this chat!<br><br>"
            f"What would you like to do today? 😊"
        ),
        "action": None,
        "action_data": None,
        "suggestions": [
            "🍽️ Show me the menu",
            "⭐ Top rated dishes",
            "🌶️ Something spicy",
            "ℹ️ Restaurant info"
        ],
        "items_to_show": None
    }
