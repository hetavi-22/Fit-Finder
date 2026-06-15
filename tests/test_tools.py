import pytest
from tools import search_listings, suggest_outfit, create_fit_card
from utils.data_loader import get_example_wardrobe, get_empty_wardrobe


def test_search_returns_results():
    """Verify that a standard query returns matching results."""
    results = search_listings("vintage graphic tee", size=None, max_price=50)
    assert isinstance(results, list)
    assert len(results) > 0
    assert "title" in results[0]
    assert "price" in results[0]

def test_search_empty_results():
    """Verify that an impossible search returns an empty list without crashing."""
    results = search_listings("designer ballgown", size="XXS", max_price=5)
    assert results == [] 

def test_search_price_filter():
    """Verify that listings are strictly filtered by the maximum price constraint."""
    max_p = 25.0
    results = search_listings("jacket", size=None, max_price=max_p)
    for item in results:
        assert item["price"] <= max_p

def test_search_size_filter():
    """Verify that listings are strictly filtered by size, guarding against partial matches."""
    # Searching for "S" should return smalls (or S/M) but not extra smalls (XS)
    results = search_listings("jeans", size="S", max_price=None)
    for item in results:
        size_str = item["size"].strip().lower()
        assert "s" in size_str
        assert "xs" not in size_str or "/" in size_str or "s" in size_str.split('/')



def test_suggest_outfit_happy_path():
    """Verify outfit suggestions are generated when a wardrobe has items."""
    new_item = {
        "title": "Vintage Graphic Tee — 2003 Tour Bootleg Style",
        "category": "tops",
        "colors": ["black"],
        "style_tags": ["vintage", "graphic tee"],
        "description": "Faded black tee."
    }
    wardrobe = get_example_wardrobe()
    suggestion = suggest_outfit(new_item, wardrobe)
    assert isinstance(suggestion, str)
    assert len(suggestion.strip()) > 0

def test_suggest_outfit_empty_wardrobe():
    """Verify styling suggestions fall back to general advice when the wardrobe is empty."""
    new_item = {
        "title": "Vintage Graphic Tee",
        "category": "tops",
        "colors": ["black"],
        "style_tags": ["vintage"],
        "description": "Faded black tee."
    }
    wardrobe = get_empty_wardrobe()
    suggestion = suggest_outfit(new_item, wardrobe)
    assert isinstance(suggestion, str)
    assert len(suggestion.strip()) > 0
    assert "style" in suggestion.lower() or "pair" in suggestion.lower() or "tops" in suggestion.lower() or "denim" in suggestion.lower() or "sneakers" in suggestion.lower()



def test_create_fit_card_happy_path():
    """Verify fit card generates a conversational caption using outfit details."""
    new_item = {
        "title": "Graphic Tee",
        "price": 24.0,
        "platform": "depop",
        "colors": ["black"],
        "style_tags": ["vintage"]
    }
    outfit = "Pair this with dark wash baggy straight-leg jeans and white sneakers."
    caption = create_fit_card(outfit, new_item)
    assert isinstance(caption, str)
    assert len(caption.strip()) > 0
    assert "depop" in caption.lower()
    assert "24" in caption

def test_create_fit_card_empty_outfit_fallback():
    """Verify fit card falls back to a standalone caption if outfit suggestion is empty."""
    new_item = {
        "title": "Graphic Tee",
        "price": 24.0,
        "platform": "depop",
        "colors": ["black"],
        "style_tags": ["vintage"]
    }
    # Pass an empty outfit suggestion
    caption = create_fit_card("", new_item)
    assert isinstance(caption, str)
    assert len(caption.strip()) > 0
    assert "depop" in caption.lower()
    assert "24" in caption
