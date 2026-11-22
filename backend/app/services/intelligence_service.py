import re
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.category import Category
from app.models.department import Department
from app.models.ticket import TicketPriority
from app.schemas.intelligence import (
    CategorySuggestionResponse,
    PrioritySuggestionResponse,
)


# Domain taxonomy for rule-based campus ticket classification
KEYWORD_RULES = [
    # IT Department
    {
        "dept_code": "IT",
        "category_name": "Internet & Wi-Fi",
        "keywords": ["wifi", "wi-fi", "internet", "ethernet", "lan", "network", "router", "signal", "bandwidth", "disconnect", "connectivity", "ip address"],
    },
    {
        "dept_code": "IT",
        "category_name": "Lab Computers & Workstations",
        "keywords": ["computer", "pc", "laptop", "desktop", "keyboard", "mouse", "monitor", "workstation", "cpu", "boot", "windows", "linux", "screen", "ram", "hard drive"],
    },
    {
        "dept_code": "IT",
        "category_name": "Software & Campus Portal",
        "keywords": ["portal", "login", "password", "erp", "lms", "moodle", "software", "license", "email", "credentials", "account", "reset password", "app"],
    },
    # Estate & Maintenance Department
    {
        "dept_code": "ESTATE",
        "category_name": "Plumbing & Restroom",
        "keywords": ["water", "leak", "pipe", "tap", "faucet", "toilet", "washroom", "restroom", "flush", "basin", "sewage", "drain", "clogged", "overflow", "bathroom"],
    },
    {
        "dept_code": "ESTATE",
        "category_name": "Furniture & Carpentry",
        "keywords": ["desk", "table", "chair", "bench", "door", "lock", "key", "latch", "window", "glass", "wooden", "hinge", "shelf", "cupboard", "furniture"],
    },
    {
        "dept_code": "ESTATE",
        "category_name": "Housekeeping & Cleaning",
        "keywords": ["garbage", "trash", "dust", "dirt", "clean", "housekeeping", "mop", "spill", "odor", "pest", "smell", "sanitation", "broom", "waste"],
    },
    # Electrical & Power Department
    {
        "dept_code": "ELEC",
        "category_name": "Lighting & Electrical Supply",
        "keywords": ["light", "bulb", "tube", "tubelight", "lamp", "switch", "socket", "power", "electricity", "plug", "sparking", "tripping", "mcb", "breaker", "voltage", "fan", "dark"],
    },
    {
        "dept_code": "ELEC",
        "category_name": "Air Conditioning & HVAC",
        "keywords": ["ac", "a/c", "air conditioning", "cooling", "hvac", "chilled", "compressor", "thermostat", "air conditioner"],
    },
    # Academic Affairs Department
    {
        "dept_code": "ACAD",
        "category_name": "Projector & Smart Board",
        "keywords": ["projector", "screen", "smart board", "smartboard", "hdmi", "vga", "display cable", "projection", "whiteboard", "blackboard", "marker", "podium"],
    },
    {
        "dept_code": "ACAD",
        "category_name": "Audio & Microphone",
        "keywords": ["mic", "microphone", "speaker", "sound", "audio", "volume", "amplifier", "acoustic", "lapel", "collar mic", "pa system", "echo"],
    },
]

CRITICAL_KEYWORDS = [
    "fire", "smoke", "spark", "explosion", "gas leak", "electric shock",
    "electrocution", "flood", "flooding", "server down", "blackout",
    "emergency", "hazard", "danger", "life risk", "roof collapse", "short circuit"
]

HIGH_KEYWORDS = [
    "water leak", "power cut", "exam", "test", "presentation", "auditorium",
    "server room", "lab exam", "broken lock", "blocked drain", "overflow",
    "urgent", "severe", "foul smell", "ongoing class"
]

LOW_KEYWORDS = [
    "cosmetic", "paint", "chip", "suggestion", "minor", "request for extra",
    "dusty", "scratch", "aesthetic", "notice board", "general inquiry"
]


def suggest_category_and_department(
    title: str,
    description: str,
    db: Session,
) -> CategorySuggestionResponse:
    """
    Analyzes ticket title and description using a rule-based campus ontology.
    Returns the most suitable category and department along with a confidence score.
    Returns safe low-confidence fallback if no high-fidelity match is found.
    """
    combined_text = f"{title.lower()} {description.lower()}"
    words = set(re.findall(r"\b[a-z0-9\-]+\b", combined_text))

    best_match = None
    highest_score = 0
    matched_kws = []

    for rule in KEYWORD_RULES:
        current_matched = []
        score = 0
        for kw in rule["keywords"]:
            if " " in kw:
                if kw in combined_text:
                    current_matched.append(kw)
                    score += 2
            elif kw in words:
                current_matched.append(kw)
                # Words in title have higher relevance weight
                score += 2 if kw in title.lower() else 1

        if score > highest_score:
            highest_score = score
            best_match = rule
            matched_kws = current_matched

    # Low confidence threshold
    if highest_score < 2 or not best_match:
        return CategorySuggestionResponse(
            suggested_department_id=None,
            suggested_department_name=None,
            suggested_category_id=None,
            suggested_category_name=None,
            confidence_score=0.1,
            confidence_level="low",
            matched_keywords=matched_kws,
            is_fallback=True,
        )

    # Resolve database records for matched department and category
    dept = db.scalar(
        select(Department).where(Department.department_code == best_match["dept_code"])
    )
    cat = None
    if dept:
        cat = db.scalar(
            select(Category).where(
                Category.category_name == best_match["category_name"],
                Category.department_id == dept.id,
            )
        )

    # Normalize confidence score
    confidence_score = min(0.95, round(0.5 + (highest_score * 0.1), 2))
    confidence_level = "high" if confidence_score >= 0.75 else "medium"

    return CategorySuggestionResponse(
        suggested_department_id=dept.id if dept else None,
        suggested_department_name=dept.department_name if dept else None,
        suggested_category_id=cat.id if cat else None,
        suggested_category_name=cat.category_name if cat else best_match["category_name"],
        confidence_score=confidence_score,
        confidence_level=confidence_level,
        matched_keywords=matched_kws,
        is_fallback=False,
    )


def suggest_ticket_priority(title: str, description: str) -> PrioritySuggestionResponse:
    """
    Analyzes ticket text for urgency indicators, hazards, and operational impact.
    Suggests Critical, High, Medium, or Low priority with a human-readable explanation.
    """
    text = f"{title.lower()} {description.lower()}"

    # 1. Check Critical Hazards
    critical_matches = [kw for kw in CRITICAL_KEYWORDS if kw in text]
    if critical_matches:
        return PrioritySuggestionResponse(
            suggested_priority=TicketPriority.CRITICAL.value,
            reason=f"Urgent safety risk or severe infrastructure outage detected ({', '.join(critical_matches[:3])}).",
            urgency_factors=critical_matches,
        )

    # 2. Check High Impact / Disruption
    high_matches = [kw for kw in HIGH_KEYWORDS if kw in text]
    if high_matches:
        return PrioritySuggestionResponse(
            suggested_priority=TicketPriority.HIGH.value,
            reason=f"Significant disruption to academic activities or critical facilities ({', '.join(high_matches[:3])}).",
            urgency_factors=high_matches,
        )

    # 3. Check Low Priority / Cosmetic
    low_matches = [kw for kw in LOW_KEYWORDS if kw in text]
    if low_matches:
        return PrioritySuggestionResponse(
            suggested_priority=TicketPriority.LOW.value,
            reason="Non-critical cosmetic maintenance or low-urgency request.",
            urgency_factors=low_matches,
        )

    # 4. Standard Default (Medium)
    return PrioritySuggestionResponse(
        suggested_priority=TicketPriority.MEDIUM.value,
        reason="Standard operational maintenance request with standard SLA.",
        urgency_factors=[],
    )
