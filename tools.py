"""
tools.py

The three required FitFindr tools. Each tool is a standalone function that
can be called and tested independently before being wired into the agent loop.

Complete and test each tool before moving to agent.py.

Tools:
    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)              → str
    create_fit_card(outfit, new_item)               → str
"""

import os
import re

from dotenv import load_dotenv
from groq import Groq

from utils.data_loader import load_listings

load_dotenv()


# ── Groq client ───────────────────────────────────────────────────────────────

def _get_groq_client():
    """Initialize and return a Groq client using GROQ_API_KEY from .env."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY not set. Add it to a .env file in the project root."
        )
    return Groq(api_key=api_key)


# ── Tool 1: search_listings ───────────────────────────────────────────────────

def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search the mock listings dataset for items matching the description,
    optional size, and optional price ceiling.

    Args:
        description: Keywords describing what the user is looking for
                     (e.g., "vintage graphic tee").
        size:        Size string to filter by, or None to skip size filtering.
                     Matching is case-insensitive (e.g., "M" matches "S/M").
        max_price:   Maximum price (inclusive), or None to skip price filtering.

    Returns:
        A list of matching listing dicts, sorted by relevance (best match first).
        Returns an empty list if nothing matches — does NOT raise an exception.

    Each listing dict has the following fields:
        id, title, description, category, style_tags (list), size,
        condition, price (float), colors (list), brand, platform

    TODO:
        1. Load all listings with load_listings().
        2. Filter by max_price and size (if provided).
        3. Score each remaining listing by keyword overlap with `description`.
        4. Drop any listings with a score of 0 (no relevant matches).
        5. Sort by score, highest first, and return the listing dicts.

    Before writing code, fill in the Tool 1 section of planning.md.
    """
    # Replace this with your implementation
    
    listings = load_listings()
    filtered_listings = []
    

    query_size = size.strip().lower() if size else None
    for item in listings:
        # Filter by price
        if max_price is not None:
            if item.get("price", 0.0) > max_price:
                continue
                
        # Filter by size
        if query_size:
            item_size = item.get("size", "")
            if not item_size:
                continue
            ls = item_size.strip().lower()
            
            pattern = r'\b' + re.escape(query_size) + r'\b'
            if not re.search(pattern, ls):
                continue
                
        filtered_listings.append(item)

    scored_listings = []
    query_words = set(re.findall(r'[a-z0-9]+', description.lower()))
    
    if not query_words:
        return []

    for item in filtered_listings:
        title_text = item.get("title", "").lower()
        desc_text = item.get("description", "").lower()
        style_tags = [tag.lower() for tag in item.get("style_tags", [])]
        
        listing_words = set(re.findall(r'[a-z0-9]+', title_text + " " + desc_text))
        listing_words.update(style_tags)
        
        overlap_score = len(query_words.intersection(listing_words))
        
        # Drop any listings with a score of 0
        if overlap_score > 0:
            scored_listings.append((overlap_score, item))

    scored_listings.sort(key=lambda x: x[0], reverse=True)
    return [item for _, item in scored_listings]


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Given a thrifted item and the user's wardrobe, suggest 1–2 complete outfits.

    Args:
        new_item: A listing dict (the item the user is considering buying).
        wardrobe: A wardrobe dict with an 'items' key containing a list of
                  wardrobe item dicts. May be empty — handle this gracefully.

    Returns:
        A non-empty string with outfit suggestions.
        If the wardrobe is empty, offer general styling advice for the item
        rather than raising an exception or returning an empty string.

    TODO:
        1. Check whether wardrobe['items'] is empty.
        2. If empty: call the LLM with a prompt for general styling ideas
           (what kinds of items pair well, what vibe it suits, etc.).
        3. If not empty: format the wardrobe items into a prompt and ask
           the LLM to suggest specific outfit combinations using the new item
           and named pieces from the wardrobe.
        4. Return the LLM's response as a string.

    Before writing code, fill in the Tool 2 section of planning.md.
    """
    # Replace this with your implementation

    item_title = new_item.get("title", "Unknown Item")
    item_category = new_item.get("category", "clothing")
    item_colors = ", ".join(new_item.get("colors", [])) or "unknown colors"
    item_tags = ", ".join(new_item.get("style_tags", [])) or "casual"
    item_desc = new_item.get("description", "")
    item_details = (
        f"Item: {item_title}\n"
        f"Category: {item_category}\n"
        f"Colors: {item_colors}\n"
        f"Style tags: {item_tags}\n"
        f"Description: {item_desc}"
    )
    
    wardrobe_items = wardrobe.get("items", [])
    
    if not wardrobe_items:
        # General styling prompt for empty wardrobe
        prompt = (
            f"The user wants styling advice for this newly found piece:\n\n"
            f"{item_details}\n\n"
            f"The user's wardrobe is currently empty. Please suggest general outfit "
            f"combinations, complementary colors, proportions, and style directions "
            f"that work beautifully for this category of clothing."
        )
    else:
        # Wardrobe has items so format the closet listings
        wardrobe_list = []
        for i, item in enumerate(wardrobe_items, 1):
            w_name = item.get("name", "Unnamed Piece")
            w_cat = item.get("category", "clothing")
            w_colors = ", ".join(item.get("colors", []))
            w_tags = ", ".join(item.get("style_tags", []))
            w_notes = item.get("notes", "")
            notes_str = f" (Notes: {w_notes})" if w_notes else ""
            
            wardrobe_list.append(
                f"{i}. {w_name} [{w_cat}] - Colors: {w_colors} | Tags: {w_tags}{notes_str}"
            )
        
        wardrobe_details = "\n".join(wardrobe_list)
        
        prompt = (
            f"The user is considering buying this item:\n\n"
            f"{item_details}\n\n"
            f"Here is the user's current closet/wardrobe:\n"
            f"{wardrobe_details}\n\n"
            f"Please suggest 1-2 complete, stylized outfits that pair this new item "
            f"with specific items from their wardrobe. Refer to their wardrobe items "
            f"explicitly by name. Explain why these combinations work (e.g. color harmony, "
            f"silhouette, or aesthetic style)."
        )
  
    try:
        client = _get_groq_client()
        response = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are a professional fashion stylist. Give detailed, inspiring outfit suggestions in a helpful tone. Focus on creating stylish outfits.",
                },
                {"role": "user", "content": prompt},
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()

    except Exception as e:
        fallback_msg = (
            f"Styling advice for {item_title} ({item_colors}):\n"
            f"- Since this is a '{item_category}' piece, try pairing it with neutral basics "
            f"such as high-waisted denim or clean tailored trousers.\n"
            f"- For colors, work with contrast or stay monochrome. If it's a statement piece, "
            f"let it be the highlight of the outfit.\n"
            f"- Complete the look with chunky white sneakers or classic black boots, depending on the vibe."
        )
        return fallback_msg


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Generate a short, shareable outfit caption for the thrifted find.

    Args:
        outfit:   The outfit suggestion string from suggest_outfit().
        new_item: The listing dict for the thrifted item.

    Returns:
        A 2–4 sentence string usable as an Instagram/TikTok caption.
        If outfit is empty or missing, return a descriptive error message
        string — do NOT raise an exception.

    The caption should:
    - Feel casual and authentic (like a real OOTD post, not a product description)
    - Mention the item name, price, and platform naturally (once each)
    - Capture the outfit vibe in specific terms
    - Sound different each time for different inputs (use higher LLM temperature)

    TODO:
        1. Guard against an empty or whitespace-only outfit string.
        2. Build a prompt that gives the LLM the item details and the outfit,
           and asks for a caption matching the style guidelines above.
        3. Call the LLM and return the response.

    Before writing code, fill in the Tool 3 section of planning.md.
    """
    # Replace this with your implementation
    
    item_title = new_item.get("title", "thrifted find")
    item_platform = new_item.get("platform", "online")
    item_price = new_item.get("price", 0.0)
    item_colors = ", ".join(new_item.get("colors", []))
    item_tags = ", ".join(new_item.get("style_tags", []))
    
    outfit_str = outfit.strip() if outfit else ""
    
    if not outfit_str:
        # Fallback prompt for standalone item caption
        prompt = (
            f"Write a short, conversational OOTD caption (1-3 sentences) for a newly thrifted item.\n\n"
            f"Details of item:\n"
            f"- Title: {item_title}\n"
            f"- Price: ${item_price}\n"
            f"- Platform: {item_platform}\n"
            f"- Colors: {item_colors}\n"
            f"- Style: {item_tags}\n\n"
            f"Guidelines:\n"
            f"- Mention the exact item name, price, and platform naturally once each.\n"
            f"- Make it sound authentic, casual, and conversational (use lowercase, brief punctuation, and an emoji or hashtag if it fits the vibe).\n"
            f"- Do not sound like a store catalog."
        )
    else:
        prompt = (
            f"Write a short, conversational OOTD caption (1-3 sentences) about styling a newly thrifted item.\n\n"
            f"Details of item:\n"
            f"- Title: {item_title}\n"
            f"- Price: ${item_price}\n"
            f"- Platform: {item_platform}\n"
            f"- Colors: {item_colors}\n"
            f"- Style: {item_tags}\n\n"
            f"Styling idea: {outfit_str}\n\n"
            f"Guidelines:\n"
            f"- Mention the exact item name, price, and platform naturally once each.\n"
            f"- Capture the outfit styling details in a casual and personal way.\n"
            f"- Make it sound authentic and conversational (use lowercase, brief punctuation, and an emoji or hashtag if it fits the vibe).\n"
            f"- Do not sound like a store catalog."
        )

    try:
        client = _get_groq_client()
        response = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are a social media copywriter specializing in Gen-Z fashion and thrift culture. Write authentic OOTD captions.",
                },
                {"role": "user", "content": prompt},
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.85,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        
        return (
            f"secured this {item_title} off {item_platform} for ${item_price} and i'm obsessed! "
            f"styling it with some clean basics today 🖤✨ #thrifted #ootd"
        )

