"""
agent.py

The FitFindr planning loop. Orchestrates the three tools in response to a
natural language user query, passing state between them via a session dict.

Complete tools.py and test each tool in isolation before implementing this file.

Usage (once implemented):
    from agent import run_agent
    from utils.data_loader import get_example_wardrobe

    result = run_agent(
        query="vintage graphic tee under $30, size M",
        wardrobe=get_example_wardrobe(),
    )
    print(result["fit_card"])
    print(result["error"])   # None on success
"""

import json
import re
from tools import search_listings, suggest_outfit, create_fit_card, _get_groq_client

def _parse_query(query: str) -> dict:
    """
    Use the Groq LLM to parse a user's natural language search query 
    into structured search parameters (description, size, max_price).
    """
    try:
        client = _get_groq_client()
        prompt = (
            f"Analyze the following clothing search request: \"{query}\"\n\n"
            f"Extract and return a JSON object with these exact keys:\n"
            f"- 'description' (str): keywords describing the clothing item itself (e.g., 'vintage graphic tee'). Always extract keywords.\n"
            f"- 'size' (str or null): the specific size mentioned (e.g., 'M', 'W30', '8'), or null if not specified.\n"
            f"- 'max_price' (float or null): the price ceiling specified (e.g., 30.0 for 'under $30'), or null if not specified.\n\n"
            f"Return ONLY valid JSON. Do not include markdown code fences, backticks, or any conversational text."
        )
        
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a precise JSON parser. Output only valid raw JSON, with no explanation or formatting."},
                {"role": "user", "content": prompt}
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.0,
        )
        content = response.choices[0].message.content.strip()
        
        if content.startswith("```"):
            content = re.sub(r"^```(?:json)?\n", "", content)
            content = re.sub(r"\n```$", "", content)
            
        parsed = json.loads(content.strip())

        extracted_desc = parsed.get("description", "").strip()
        if not extracted_desc:
            extracted_desc = query # fallback to whole query if description is empty
            
        return {
            "description": extracted_desc,
            "size": parsed.get("size"),
            "max_price": float(parsed["max_price"]) if parsed.get("max_price") is not None else None
        }
        
    except Exception as e:
        max_price = None
        price_match = re.search(r'(?:under|\$)\s*(\d+(?:\.\d+)?)', query.lower())
        if price_match:
            max_price = float(price_match.group(1))
            
        size = None
        size_match = re.search(r'\bsize\s+(\w+)\b|\b([SML])\b', query, re.IGNORECASE)
        if size_match:
            size = size_match.group(1) or size_match.group(2)
            if size:
                size = size.upper()
                
        clean_desc = query.lower()
        clean_desc = re.sub(r'under\s*\$?\s*\d+', '', clean_desc)
        clean_desc = re.sub(r'\$?under\s*\d+', '', clean_desc)
        clean_desc = re.sub(r'\$\d+', '', clean_desc)
        clean_desc = re.sub(r'size\s+\w+', '', clean_desc)
        clean_desc = re.sub(r'\b(s|m|l|xl|xxs|xs)\b', '', clean_desc)
        clean_desc = re.sub(r'\s+', ' ', clean_desc).strip()
        
        if not clean_desc:
            clean_desc = query
            
        return {
            "description": clean_desc,
            "size": size,
            "max_price": max_price
        }

# ── session state ─────────────────────────────────────────────────────────────

def _new_session(query: str, wardrobe: dict) -> dict:
    """
    Initialize and return a fresh session dict for one user interaction.

    The session dict is the single source of truth for everything that happens
    during a run — it stores the original query, parsed parameters, tool results,
    and any error that caused early termination.

    You may add fields to this dict as needed for your implementation.
    """
    return {
        "query": query,              # original user query
        "parsed": {},                # extracted description / size / max_price
        "search_results": [],        # list of matching listing dicts
        "selected_item": None,       # top result, passed into suggest_outfit
        "wardrobe": wardrobe,        # user's wardrobe dict
        "outfit_suggestion": None,   # string returned by suggest_outfit
        "fit_card": None,            # string returned by create_fit_card
        "error": None,               # set if the interaction ended early
    }


# ── planning loop ─────────────────────────────────────────────────────────────

def run_agent(query: str, wardrobe: dict) -> dict:
    """
    Main agent entry point. Runs the FitFindr planning loop for a single
    user interaction and returns the completed session dict.

    Args:
        query:    Natural language user request
                  (e.g., "vintage graphic tee under $30, size M")
        wardrobe: User's wardrobe dict — use get_example_wardrobe() or
                  get_empty_wardrobe() from utils/data_loader.py

    Returns:
        The session dict after the interaction completes. Check session["error"]
        first — if it is not None, the interaction ended early and the other
        output fields (outfit_suggestion, fit_card) will be None.

    TODO — implement this function using the planning loop you designed in planning.md:

        Step 1: Initialize the session with _new_session().

        Step 2: Parse the user's query to extract a description, size, and
                max_price. You can use regex, string splitting, or ask the LLM
                to parse it — document your choice in planning.md.
                Store the result in session["parsed"].

        Step 3: Call search_listings() with the parsed parameters.
                Store results in session["search_results"].
                If no results: set session["error"] to a helpful message and
                return the session early. Do NOT proceed to suggest_outfit
                with empty input.

        Step 4: Select the item to use (e.g., the top result).
                Store it in session["selected_item"].

        Step 5: Call suggest_outfit() with the selected item and wardrobe.
                Store the result in session["outfit_suggestion"].

        Step 6: Call create_fit_card() with the outfit suggestion and selected item.
                Store the result in session["fit_card"].

        Step 7: Return the session.

    Before writing code, complete the Planning Loop and State Management sections
    of planning.md — your implementation should match what you described there.
    """
    # TODO: implement the planning loop
    session = _new_session(query, wardrobe)
    
    parsed_params = _parse_query(query)
    session["parsed"] = parsed_params
    
    desc = parsed_params.get("description", "")
    sz = parsed_params.get("size")
    price = parsed_params.get("max_price")
    
    results = search_listings(description=desc, size=sz, max_price=price)
    session["search_results"] = results
    
    if not results:
        session["error"] = (
            f"No listings found matching '{desc}'"
            f"{f' in size {sz}' if sz else ''}"
            f"{f' under ${price}' if price is not None else ''}. "
            f"Try loosening your price constraint or removing the size filter!"
        )
        return session
        
    selected = results[0]
    session["selected_item"] = selected
    
    outfit = suggest_outfit(selected, wardrobe)
    session["outfit_suggestion"] = outfit
    
    fit_card = create_fit_card(outfit, selected)
    session["fit_card"] = fit_card
    
    return session


# ── CLI test ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from utils.data_loader import get_example_wardrobe, get_empty_wardrobe

    print("=== Happy path: graphic tee ===\n")
    session = run_agent(
        query="looking for a vintage graphic tee under $30",
        wardrobe=get_example_wardrobe(),
    )
    if session["error"]:
        print(f"Error: {session['error']}")
    else:
        print(f"Found: {session['selected_item']['title']}")
        print(f"\nOutfit: {session['outfit_suggestion']}")
        print(f"\nFit card: {session['fit_card']}")

    print("\n\n=== No-results path ===\n")
    session2 = run_agent(
        query="designer ballgown size XXS under $5",
        wardrobe=get_example_wardrobe(),
    )
    print(f"Error message: {session2['error']}")
