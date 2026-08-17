import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import yas_api.models  # noqa: F401
from yas_api.core.security import hash_password
from yas_api.core.storage import StoredObject
from yas_api.db.base import Base
from yas_api.db.session import get_db
from yas_api.main import app
from yas_api.models import AdminUser


class FakeStorage:
    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}

    def upload(self, *, key: str, content: bytes, content_type: str) -> StoredObject:
        self.objects[key] = content
        return StoredObject(key=key, public_url=f"https://fake-cdn.test/{key}")

    def delete(self, *, key: str) -> None:
        self.objects.pop(key, None)

    def public_url(self, key: str) -> str:
        return f"https://fake-cdn.test/{key}"


@pytest.fixture(autouse=True)
def fake_storage(monkeypatch: pytest.MonkeyPatch) -> FakeStorage:
    storage = FakeStorage()
    for module in ("yas_api.api.routes.admin_media", "yas_api.seed", "yas_api.core.storage"):
        monkeypatch.setattr(f"{module}.get_storage", lambda: storage, raising=False)
    return storage


@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    testing_session = sessionmaker(bind=engine, expire_on_commit=False)
    with testing_session() as session:
        yield session
    Base.metadata.drop_all(engine)


@pytest.fixture
def client(db_session: Session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def admin(db_session: Session) -> AdminUser:
    user = AdminUser(
        name="Administrador",
        email="admin@example.com",
        password_hash=hash_password("senha-segura"),
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(client: TestClient, admin: AdminUser) -> dict[str, str]:
    response = client.post(
        "/api/v1/admin/auth/token",
        data={"username": admin.email, "password": "senha-segura"},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}
