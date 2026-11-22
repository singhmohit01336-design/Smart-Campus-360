import math
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_active_user, require_roles
from app.models.category import Category
from app.models.knowledge_base import KnowledgeBase
from app.models.user import User, UserRole
from app.schemas.knowledge_base import (
    KnowledgeBaseCreate,
    KnowledgeBasePublishRequest,
    KnowledgeBaseResponse,
    KnowledgeBaseUpdate,
    PaginatedKnowledgeBaseResponse,
)


router = APIRouter(
    prefix="/knowledge-base",
    tags=["Knowledge Base & FAQs"],
)


def to_kb_response(article: KnowledgeBase) -> KnowledgeBaseResponse:
    cat_name = article.category.category_name if article.category else None
    auth_name = article.author.full_name if article.author else None
    return KnowledgeBaseResponse(
        id=article.id,
        title=article.title,
        content=article.content,
        category_id=article.category_id,
        category_name=cat_name,
        created_by_id=article.created_by_id,
        author_name=auth_name,
        is_published=article.is_published,
        created_at=article.created_at,
        updated_at=article.updated_at,
    )


@router.post(
    "/",
    response_model=KnowledgeBaseResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_article(
    payload: KnowledgeBaseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.SUPERADMIN])),
):
    """
    Create a new knowledge base or FAQ article.
    Restricted to Admins and Superadmins.
    """
    if payload.category_id:
        cat = db.get(Category, payload.category_id)
        if not cat:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Category not found.",
            )

    article = KnowledgeBase(
        title=payload.title.strip(),
        content=payload.content.strip(),
        category_id=payload.category_id,
        created_by_id=current_user.id,
        is_published=payload.is_published,
    )
    db.add(article)
    db.commit()
    db.refresh(article)

    return to_kb_response(article)


@router.get(
    "/",
    response_model=PaginatedKnowledgeBaseResponse,
)
def list_articles(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    search: str | None = Query(default=None, description="Search title or content"),
    category_id: int | None = Query(default=None, description="Filter by category ID"),
    is_published: bool | None = Query(default=None, description="Admin-only publish filter"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    List knowledge base articles with search and category filtering.
    - Students, Faculty, and Technicians see ONLY published articles.
    - Admins and Superadmins can inspect draft and published articles.
    """
    user_role = (
        current_user.role.value
        if isinstance(current_user.role, UserRole)
        else str(current_user.role).lower()
    )

    query = select(KnowledgeBase)

    # Role visibility guard
    if user_role not in {UserRole.ADMIN.value, UserRole.SUPERADMIN.value}:
        query = query.where(KnowledgeBase.is_published == True)
    elif is_published is not None:
        query = query.where(KnowledgeBase.is_published == is_published)

    # Search filter
    if search:
        pattern = f"%{search.strip()}%"
        query = query.where(
            or_(
                KnowledgeBase.title.ilike(pattern),
                KnowledgeBase.content.ilike(pattern),
            )
        )

    # Category filter
    if category_id:
        query = query.where(KnowledgeBase.category_id == category_id)

    # Pagination
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    total_pages = max(1, math.ceil(total / page_size))
    offset = (page - 1) * page_size

    query = query.order_by(KnowledgeBase.created_at.desc()).offset(offset).limit(page_size)
    articles = db.scalars(query).all()

    return PaginatedKnowledgeBaseResponse(
        items=[to_kb_response(a) for a in articles],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get(
    "/{article_id}",
    response_model=KnowledgeBaseResponse,
)
def get_article_details(
    article_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Retrieve single knowledge base article.
    Draft articles are hidden from non-admin users.
    """
    article = db.get(KnowledgeBase, article_id)
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found.",
        )

    user_role = (
        current_user.role.value
        if isinstance(current_user.role, UserRole)
        else str(current_user.role).lower()
    )

    if not article.is_published and user_role not in {UserRole.ADMIN.value, UserRole.SUPERADMIN.value}:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found.",
        )

    return to_kb_response(article)


@router.patch(
    "/{article_id}",
    response_model=KnowledgeBaseResponse,
)
def update_article(
    article_id: int,
    payload: KnowledgeBaseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.SUPERADMIN])),
):
    """
    Update article content, title, or category.
    Restricted to Admins and Superadmins.
    """
    article = db.get(KnowledgeBase, article_id)
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found.",
        )

    if payload.title is not None:
        article.title = payload.title.strip()
    if payload.content is not None:
        article.content = payload.content.strip()
    if payload.category_id is not None:
        cat = db.get(Category, payload.category_id)
        if not cat:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Category not found.",
            )
        article.category_id = payload.category_id
    if payload.is_published is not None:
        article.is_published = payload.is_published

    db.commit()
    db.refresh(article)
    return to_kb_response(article)


@router.patch(
    "/{article_id}/publish",
    response_model=KnowledgeBaseResponse,
)
def toggle_publish_status(
    article_id: int,
    payload: KnowledgeBasePublishRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.SUPERADMIN])),
):
    """
    Publish or unpublish an article.
    Restricted to Admins and Superadmins.
    """
    article = db.get(KnowledgeBase, article_id)
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found.",
        )

    article.is_published = payload.is_published
    db.commit()
    db.refresh(article)
    return to_kb_response(article)


@router.delete(
    "/{article_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_article(
    article_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.SUPERADMIN])),
):
    """
    Permanently delete an article.
    Restricted to Admins and Superadmins.
    """
    article = db.get(KnowledgeBase, article_id)
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found.",
        )

    db.delete(article)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
