from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from yas_api.models import Category, Product, ProductBlock
from yas_api.seed import seed_database


def test_health(client: TestClient):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_admin_route_requires_login(client: TestClient):
    response = client.get("/api/v1/admin/products")
    assert response.status_code == 401


def test_admin_can_upload_use_and_delete_banner_image(
    client: TestClient, auth_headers: dict[str, str]
):
    upload_response = client.post(
        "/api/v1/admin/media",
        headers=auth_headers,
        files={"file": ("banner.gif", b"GIF89a", "image/gif")},
        data={"alt_text": "Banner principal"},
    )
    assert upload_response.status_code == 201
    media = upload_response.json()

    banner_response = client.post(
        "/api/v1/admin/banners",
        headers=auth_headers,
        json={"title": "Embalagens que valorizam sua marca", "image_id": media["id"]},
    )
    assert banner_response.status_code == 201

    in_use_response = client.delete(f"/api/v1/admin/media/{media['id']}", headers=auth_headers)
    assert in_use_response.status_code == 409

    banner_id = banner_response.json()["id"]
    assert (
        client.delete(f"/api/v1/admin/banners/{banner_id}", headers=auth_headers).status_code == 204
    )
    assert (
        client.delete(f"/api/v1/admin/media/{media['id']}", headers=auth_headers).status_code == 204
    )


def test_catalog_storefront_and_order_quote(client: TestClient, auth_headers: dict[str, str]):
    category_response = client.post(
        "/api/v1/admin/categories",
        headers=auth_headers,
        json={"name": "Caixas Personalizadas", "is_featured": True},
    )
    assert category_response.status_code == 201
    category = category_response.json()
    assert category["slug"] == "caixas-personalizadas"

    product_response = client.post(
        "/api/v1/admin/products",
        headers=auth_headers,
        json={
            "category_id": category["id"],
            "name": "Caixa Sedex",
            "price_from": "2.50",
            "minimum_quantity": 25,
            "delivery_days": 2,
            "tone": "brand",
            "unit_label": "unidades",
        },
    )
    assert product_response.status_code == 201
    product = product_response.json()
    assert product["delivery_days"] == 2
    assert product["tone"] == "brand"

    block_response = client.post(
        "/api/v1/admin/blocks",
        headers=auth_headers,
        json={"title": "Mais vendidos", "product_ids": [product["id"]]},
    )
    assert block_response.status_code == 201
    assert block_response.json()["products"][0]["name"] == "Caixa Sedex"

    settings_response = client.patch(
        "/api/v1/admin/settings",
        headers=auth_headers,
        json={"whatsapp_phone": "5511999999999", "order_email": "vendas@example.com"},
    )
    assert settings_response.status_code == 200

    storefront_response = client.get("/api/v1/public/storefront")
    assert storefront_response.status_code == 200
    storefront = storefront_response.json()
    assert storefront["categories"][0]["name"] == "Caixas Personalizadas"
    assert storefront["blocks"][0]["products"][0]["slug"] == "caixa-sedex"

    quote_response = client.post(
        "/api/v1/public/quote",
        json={
            "customer_name": "Maria",
            "customer_whatsapp": "11999999999",
            "items": [{"product_id": product["id"], "package_count": 2}],
        },
    )
    assert quote_response.status_code == 200
    quote = quote_response.json()
    assert Decimal(quote["estimated_total"]) == Decimal("5.00")
    assert quote["whatsapp_url"].startswith("https://wa.me/5511999999999?text=")
    assert quote["email_url"].startswith("mailto:vendas@example.com?subject=")
    assert "11999999999" in quote["message"]


def test_quote_enforces_package_count(client: TestClient, auth_headers: dict[str, str]):
    category = client.post(
        "/api/v1/admin/categories", headers=auth_headers, json={"name": "Sacolas"}
    ).json()
    product = client.post(
        "/api/v1/admin/products",
        headers=auth_headers,
        json={"category_id": category["id"], "name": "Sacola Kraft", "minimum_quantity": 50},
    ).json()
    client.patch(
        "/api/v1/admin/settings",
        headers=auth_headers,
        json={"whatsapp_phone": "5511999999999"},
    )

    response = client.post(
        "/api/v1/public/quote",
        json={
            "customer_name": "Joao",
            "customer_whatsapp": "11988888888",
            "items": [{"product_id": product["id"], "package_count": 0}],
        },
    )
    assert response.status_code == 422


def test_seed_is_idempotent(db_session: Session):
    seed_database(db_session, include_assets=False)
    seed_database(db_session, include_assets=False)
    db_session.commit()

    assert db_session.scalar(select(func.count(Category.id))) == 13
    assert db_session.scalar(select(func.count(Product.id))) == 28
    assert db_session.scalar(select(func.count(ProductBlock.id))) == 5
