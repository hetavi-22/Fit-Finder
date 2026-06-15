# FitFindr — Starter Kit

This starter kit contains everything you need to begin Project 2.

## What's Included

```
ai201-project2-fitfindr-starter/
├── data/
│   ├── listings.json          # 40 mock secondhand listings
│   └── wardrobe_schema.json   # Wardrobe format + example wardrobe
├── utils/
│   └── data_loader.py         # Helper functions for loading the data
├── planning.md                # Your planning template — fill this out first
└── requirements.txt           # Python dependencies
```

## Setup

```bash
pip install -r requirements.txt
```

Set your Groq API key in a `.env` file (get a free key at [console.groq.com](https://console.groq.com)):
```
GROQ_API_KEY=your_key_here
```

## The Mock Listings Dataset

`data/listings.json` contains 40 mock secondhand listings across categories (tops, bottoms, outerwear, shoes, accessories) and styles (vintage, y2k, grunge, cottagecore, streetwear, and more).

Each listing has: `id`, `title`, `description`, `category`, `style_tags`, `size`, `condition`, `price`, `colors`, `brand`, and `platform`.

Load it with:
```python
from utils.data_loader import load_listings
listings = load_listings()
```

## The Wardrobe Schema

`data/wardrobe_schema.json` defines the format your agent uses to represent a user's existing wardrobe. It includes:

- `schema`: field definitions for a wardrobe item
- `example_wardrobe`: a sample wardrobe with 10 items you can use for testing
- `empty_wardrobe`: a starting template for a new user

Load an example wardrobe with:
```python
from utils.data_loader import get_example_wardrobe
wardrobe = get_example_wardrobe()
```

## Where to Start

1. **Read `planning.md` and fill it out before writing any code.**
2. Verify the data loads correctly by running `python utils/data_loader.py`.
3. Build and test each tool individually before connecting them through your planning loop.

Your implementation files go in this same directory. There's no required file structure for your agent code — organize it however makes sense for your design.

---

# FitFindr Agent Documentation

## Tool Inventory

FitFindr uses three core custom tools implemented in `tools.py`:

1. **`search_listings`**
   * **Signature**: `search_listings(description: str, size: str | None = None, max_price: float | None = None) -> list[dict]`
   * **Purpose**: Queries the dataset for matching items.
   * **Inputs**: `description` (str), `size` (str | None), `max_price` (float | None).
   * **Outputs**: Sorted list of matching listing dicts (sorted by match score, highest first). Returns `[]` if no matches are found.

2. **`suggest_outfit`**
   * **Signature**: `suggest_outfit(new_item: dict, wardrobe: dict) -> str`
   * **Purpose**: Generates outfit recommendations using wardrobe items, or general styling advice if the wardrobe is empty. Uses Groq's `llama-3.3-70b-versatile` model.
   * **Inputs**: `new_item` (dict), `wardrobe` (dict).
   * **Outputs**: Styling suggestion text.

3. **`create_fit_card`**
   * **Signature**: `create_fit_card(outfit: str, new_item: dict) -> str`
   * **Purpose**: Generates a social media caption mentioning the item, price, and platform. Uses Groq's `llama-3.3-70b-versatile` model.
   * **Inputs**: `outfit` (str), `new_item` (dict).
   * **Outputs**: OOTD caption string.

---

## How the Planning Loop Works

The planning loop is managed by `run_agent(query, wardrobe)` in `agent.py`:
1. **Initialize State**: Creates a session state tracking all inputs, intermediate steps, and errors.
2. **Query Parsing**: Calls `llama-3.3-70b-versatile` (temp 0.0) to parse the search query into description, size, and price filters (with a local regex backup parser).
3. **Execution Branching**:
   * Runs `search_listings`. 
   * **If results list is empty**: Halts immediately, records a helpful error in `session["error"]`, and exits without calling styling or copywriting tools.
   * **If listings match**: Picks the top result and continues.
4. **Styling & Copywriting**: Calls `suggest_outfit` followed by `create_fit_card` in sequence, storing all inputs/outputs in the session state.

---

## State Management Approach

A central `session` dictionary tracks inputs and results across all steps:
* `query` (str)
* `parsed` (dict)
* `search_results` (list)
* `selected_item` (dict)
* `wardrobe` (dict)
* `outfit_suggestion` (str)
* `fit_card` (str)
* `error` (str | None)

Each tool takes its required inputs directly from this session dictionary and saves its outputs back to it, passing data downstream cleanly.

---

## Error Handling Strategy

| Tool | Failure Mode | Recovery Strategy | Concrete Testing Example |
|---|---|---|---|
| `search_listings` | No listings match filters | Returns `[]` gracefully. Loop aborts and prints search advice. | Searching for `"designer ballgown under $5"` successfully exits early with error: `"No listings found matching 'designer ballgown' ... Try loosening constraints!"` |
| `suggest_outfit` | Wardrobe is empty | Fallback to requesting the LLM for general styling guidelines for that clothing category. | Searching `"vintage graphic tee"` with an empty wardrobe correctly outputted generalized recommendations like: *"Outfit 1: Casual Chic... Pair your baby tee with high-waisted jeans..."* |
| `create_fit_card` | Outfit styling text is empty | Fallback to writing a standalone social media caption focusing solely on the item details. | Passing an empty outfit string returned: *"just scored the cutest y2k baby tee — butterfly print on depop for $18.0 and i'm obsessed..."* |
| **Global API** | LLM API down or missing key | `try...except` wrapper uses regex-based parser, local category styling tables, and local OOTD template strings. | Tests executed with network simulated outages cleanly generated local fallback text styling and template captions. |

---

## Spec Reflection

* **How the spec helped**: Writing the parameters and types down beforehand in `planning.md` made implementing the scoring and size regex boundary logic easy because the inputs and outputs were strictly bounded.
* **How implementation diverged**: Originally, the spec defined that an empty outfit suggestion passed to `create_fit_card` should return a hard error string in the UI. During implementation, we realized this would be frustrating for a user whose search succeeded. We changed the spec to support a standalone caption fallback instead, making the agent far more resilient.

---

## AI Usage Section

1. **Scored list sorting in `search_listings`**: Provided Claude/Gemini with the spec block from `planning.md` to implement `search_listings`. The generated code used a basic substring check for size. We revised it to use regex word boundaries (`r'\b' + re.escape(query_size) + r'\b'`) so that searching for size `"S"` would not match `"XS"` or `"shoes"`.
2. **Robust query parsing in `agent.py`**: Prompted the AI to write `_parse_query` using the Groq API. Since LLM calls can fail, we revised the code by adding a robust regex-based backup parser in the `except` block to parse price limits and sizes locally using pattern matching, keeping the agent functional even in offline mode.
