import pytest
from app.core.security import create_access_token
from app.models.category import Category
from app.models.knowledge_base import KnowledgeBase
from app.models.user import User, UserRole


@pytest.fixture
def kb_test_context(db_session):
    admin = db_session.query(User).filter(User.role == UserRole.ADMIN.value).first()
    student = db_session.query(User).filter(User.role == UserRole.STUDENT.value).first()
    cat = db_session.query(Category).first()

    def token_for(user: User):
        token = create_access_token({"sub": str(user.id), "role": user.role})
        return {"Authorization": f"Bearer {token}"}

    return {
        "admin": admin,
        "student": student,
        "cat": cat,
        "h_admin": token_for(admin),
        "h_student": token_for(student),
    }


def test_knowledge_base_crud_and_role_permissions(client, kb_test_context, db_session):
    ctx = kb_test_context

    # 1. Student cannot create article -> 403 Forbidden
    create_payload = {
        "title": "How to configure campus VPN client",
        "content": "Follow these steps to connect using WireGuard or OpenVPN protocols.",
        "category_id": ctx["cat"].id,
        "is_published": True,
    }
    assert client.post("/knowledge-base/", json=create_payload, headers=ctx["h_student"]).status_code == 403

    # 2. Admin creates published article -> 201 Created
    create_resp = client.post("/knowledge-base/", json=create_payload, headers=ctx["h_admin"])
    assert create_resp.status_code == 201
    article_id = create_resp.json()["id"]

    try:
        # 3. Student can view published article -> 200 OK
        view_resp = client.get(f"/knowledge-base/{article_id}", headers=ctx["h_student"])
        assert view_resp.status_code == 200
        assert view_resp.json()["title"] == create_payload["title"]

        # 4. Student cannot update article -> 403
        assert client.patch(
            f"/knowledge-base/{article_id}",
            json={"title": "Hacked Title"},
            headers=ctx["h_student"],
        ).status_code == 403

        # 5. Admin updates article -> 200
        up_resp = client.patch(
            f"/knowledge-base/{article_id}",
            json={"title": "Configuring Campus VPN (Updated 2026)"},
            headers=ctx["h_admin"],
        )
        assert up_resp.status_code == 200
        assert up_resp.json()["title"] == "Configuring Campus VPN (Updated 2026)"

    finally:
        # Cleanup
        client.delete(f"/knowledge-base/{article_id}", headers=ctx["h_admin"])


def test_draft_article_visibility_and_publishing(client, kb_test_context):
    ctx = kb_test_context

    # 1. Admin creates draft article (is_published=False)
    draft_payload = {
        "title": "Upcoming Campus Network Maintenance Draft",
        "content": "Confidential maintenance window schedule and router firmware rollouts.",
        "is_published": False,
    }
    resp = client.post("/knowledge-base/", json=draft_payload, headers=ctx["h_admin"])
    assert resp.status_code == 201
    article_id = resp.json()["id"]

    try:
        # 2. Student cannot view draft article -> 404
        assert client.get(f"/knowledge-base/{article_id}", headers=ctx["h_student"]).status_code == 404

        # 3. Admin can view draft article -> 200
        admin_view = client.get(f"/knowledge-base/{article_id}", headers=ctx["h_admin"])
        assert admin_view.status_code == 200
        assert admin_view.json()["is_published"] is False

        # 4. Admin publishes article -> 200
        pub_resp = client.patch(
            f"/knowledge-base/{article_id}/publish",
            json={"is_published": True},
            headers=ctx["h_admin"],
        )
        assert pub_resp.status_code == 200
        assert pub_resp.json()["is_published"] is True

        # 5. Student can now view published article -> 200
        assert client.get(f"/knowledge-base/{article_id}", headers=ctx["h_student"]).status_code == 200

    finally:
        client.delete(f"/knowledge-base/{article_id}", headers=ctx["h_admin"])


def test_knowledge_base_search_and_category_filter(client, kb_test_context):
    ctx = kb_test_context

    # Create distinct article for searching
    create_resp = client.post(
        "/knowledge-base/",
        json={
            "title": "Troubleshooting eduroam certificate expiry",
            "content": "If your phone cannot connect, download the renewed Root CA certificate.",
            "category_id": ctx["cat"].id,
            "is_published": True,
        },
        headers=ctx["h_admin"],
    )
    article_id = create_resp.json()["id"]

    try:
        # Search by keyword
        search_resp = client.get("/knowledge-base/?search=eduroam", headers=ctx["h_student"])
        assert search_resp.status_code == 200
        items = search_resp.json()["items"]
        assert any("eduroam" in a["title"].lower() for a in items)

        # Filter by category
        cat_resp = client.get(f"/knowledge-base/?category_id={ctx['cat'].id}", headers=ctx["h_student"])
        assert cat_resp.status_code == 200
        assert all(a["category_id"] == ctx["cat"].id for a in cat_resp.json()["items"])

    finally:
        client.delete(f"/knowledge-base/{article_id}", headers=ctx["h_admin"])
