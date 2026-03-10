import requests
import logging
import os

KEY   = os.environ["TRELLO_API_KEY"]
TOKEN = os.environ["TRELLO_TOKEN"]
BOARD = os.environ["TRELLO_BOARD_ID"]

CATEGORY_COLORS = {
    "FLYER_REQUEST":      "yellow",
    "TOTAL_EXPERT_TASK":  "blue",
    "SOCIAL_CONTENT":     "green",
    "CAMPAIGN_REQUEST":   "purple",
    "GENERAL_MARKETING":  "orange",
}

PRIORITY_COLORS = {
    "HIGH":   "red",
    "MEDIUM": "orange",
    "LOW":    "green",
}


def get_list_id(list_name: str = "Inbox") -> str:
    """Get Trello list ID by name — falls back to first list if not found."""
    lists = requests.get(
        f"https://api.trello.com/1/boards/{BOARD}/lists",
        params={"key": KEY, "token": TOKEN}
    ).json()
    for l in lists:
        if l["name"] == list_name:
            return l["id"]
    return lists[0]["id"]


def build_description(parsed: dict) -> str:
    """
    Build the full Trello card description with 4 clearly separated sections.
    """

    # ── Section 1: Time estimate + summary + steps ──
    steps_text = "\n".join([f"- [ ] {s}" for s in parsed.get("steps", [])])
    assigned = ", ".join(parsed.get("assigned_to", []))

    section_1 = f"""## ⏱ Estimated Time:  {parsed.get("estimated_time", "TBD")}

**Assigned to:** {assigned}
**Priority:** {parsed.get("priority", "MEDIUM")}

### 📋 Task Summary
{parsed.get("task_summary", "")}

### ✅ Steps to Complete
{steps_text}"""

    # ── Section 2: Additional comments ──
    comments = parsed.get("additional_comments")
    if comments:
        section_2 = f"""---

## 💬 Additional Comments
{comments}"""
    else:
        section_2 = ""

    # ── Section 3: Original email ──
    orig = parsed.get("original_email", {})
    section_3 = f"""---

## 📧 Original Email

**Subject:** {orig.get("subject", "N/A")}

{orig.get("body", "N/A")}"""

    # ── Section 4: Draft reply ──
    reply = parsed.get("draft_reply", {})
    tone_label = {
        "confirmatory": "✅ Confirmatory — request is clear, ready to proceed",
        "needs_info":   "❓ Needs Info — missing details before we can start",
        "scoping":      "🔍 Scoping — large or vague request, needs alignment",
    }.get(reply.get("tone", ""), reply.get("tone", ""))

    section_4 = f"""---

## ✉️ Draft Reply
**Tone:** {tone_label}
**Subject:** {reply.get("subject", "")}

---
{reply.get("body", "")}
---"""

    return "\n\n".join(filter(None, [section_1, section_2, section_3, section_4]))


def add_label(card_id: str, name: str, color: str):
    """Add a colored label to a Trello card."""
    requests.post(
        f"https://api.trello.com/1/cards/{card_id}/labels",
        params={"key": KEY, "token": TOKEN, "color": color, "name": name}
    )


def create_trello_card(parsed: dict, email_data: dict) -> dict:
    """Create the Trello card and attach labels. Returns card URL and ID."""

    response = requests.post(
        "https://api.trello.com/1/cards",
        params={
            "key":    KEY,
            "token":  TOKEN,
            "idList": get_list_id("Inbox"),
            "name":   parsed["card_title"],
            "desc":   build_description(parsed),
            "pos":    "top",
        }
    )
    logging.info(f"Trello response status: {response.status_code}")
    logging.info(f"Trello response body: {response.text[:300]}")
    card = response.json()
    card_id = card.get("id")
    logging.info(f"Card ID: {card_id}")

    # Category label
    category = parsed.get("category", "GENERAL_MARKETING")
    cat_color = CATEGORY_COLORS.get(category, "grey")
    add_label(card_id, category.replace("_", " ").title(), cat_color)

    # Priority label
    priority = parsed.get("priority", "MEDIUM")
    pri_color = PRIORITY_COLORS.get(priority, "grey")
    add_label(card_id, f"Priority: {priority}", pri_color)

    return {"url": card.get("shortUrl"), "id": card_id}