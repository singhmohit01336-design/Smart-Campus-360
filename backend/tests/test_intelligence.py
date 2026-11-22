import pytest
from app.core.security import create_access_token
from app.models.user import User, UserRole


@pytest.fixture
def auth_header(db_session):
    user = db_session.query(User).filter(User.role == UserRole.STUDENT.value).first()
    token = create_access_token({"sub": str(user.id), "role": user.role})
    return {"Authorization": f"Bearer {token}"}


def test_categorization_suggestion_high_confidence(client, auth_header):
    payload = {
        "title": "Wi-Fi disconnecting every 5 minutes in hostel",
        "description": "The campus wireless router signal keeps dropping and DNS cannot resolve IP address.",
    }
    response = client.post("/intelligence/suggest-category", json=payload, headers=auth_header)
    assert response.status_code == 200
    data = response.json()
    assert data["suggested_department_name"] == "Information Technology"
    assert "Wi-Fi" in data["suggested_category_name"]
    assert data["confidence_level"] in {"high", "medium"}
    assert data["confidence_score"] >= 0.6
    assert data["is_fallback"] is False
    assert len(data["matched_keywords"]) >= 2


def test_categorization_suggestion_plumbing(client, auth_header):
    payload = {
        "title": "Severe water leak from pipe in washroom",
        "description": "The flush valve and toilet pipe are broken, causing sewage drain overflow on the floor.",
    }
    response = client.post("/intelligence/suggest-category", json=payload, headers=auth_header)
    assert response.status_code == 200
    data = response.json()
    assert data["suggested_department_name"] == "Estate & Maintenance"
    assert "Plumbing" in data["suggested_category_name"]
    assert data["confidence_level"] == "high"


def test_categorization_suggestion_low_confidence_fallback(client, auth_header):
    payload = {
        "title": "Something weird happened today",
        "description": "I have an inquiry regarding general campus timings and blue sky.",
    }
    response = client.post("/intelligence/suggest-category", json=payload, headers=auth_header)
    assert response.status_code == 200
    data = response.json()
    assert data["confidence_level"] == "low"
    assert data["is_fallback"] is True
    assert data["suggested_department_id"] is None
    assert data["suggested_category_id"] is None


def test_priority_suggestion_critical_hazard(client, auth_header):
    payload = {
        "title": "Electric spark and smoke from switchboard in lab",
        "description": "Visible fire spark and severe burning smell near power socket. Immediate danger!",
    }
    response = client.post("/intelligence/suggest-priority", json=payload, headers=auth_header)
    assert response.status_code == 200
    data = response.json()
    assert data["suggested_priority"] == "critical"
    assert "safety risk" in data["reason"].lower() or "hazard" in data["reason"].lower()
    assert any("spark" in f or "smoke" in f or "fire" in f for f in data["urgency_factors"])


def test_priority_suggestion_high_operational_disruption(client, auth_header):
    payload = {
        "title": "Projector not displaying during ongoing semester exam",
        "description": "Smart board projection is blank during lab exam presentation.",
    }
    response = client.post("/intelligence/suggest-priority", json=payload, headers=auth_header)
    assert response.status_code == 200
    data = response.json()
    assert data["suggested_priority"] == "high"
    assert "disruption" in data["reason"].lower()


def test_priority_suggestion_low_cosmetic(client, auth_header):
    payload = {
        "title": "Minor paint chip on classroom wall",
        "description": "Small aesthetic scratch on wall next to notice board. Cosmetic request.",
    }
    response = client.post("/intelligence/suggest-priority", json=payload, headers=auth_header)
    assert response.status_code == 200
    data = response.json()
    assert data["suggested_priority"] == "low"
    assert "cosmetic" in data["reason"].lower() or "minor" in data["reason"].lower()


def test_priority_suggestion_medium_default(client, auth_header):
    payload = {
        "title": "Printer paper tray loose in library",
        "description": "Plastic tray does not snap firmly into place, please adjust it.",
    }
    response = client.post("/intelligence/suggest-priority", json=payload, headers=auth_header)
    assert response.status_code == 200
    data = response.json()
    assert data["suggested_priority"] == "medium"
