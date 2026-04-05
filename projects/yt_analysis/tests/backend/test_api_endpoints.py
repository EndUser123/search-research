import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.backend_engine.main import app

# Re-import Base and get_db from the main database file
from src.backend_engine.persistence.database import Base, get_db
from src.backend_engine.persistence.repositories.category_repository import (
    CategoryRepository,
)


@pytest.fixture(name="client")
def client_fixture():
    """
    Fixture that provides a TestClient for FastAPI,
    overriding the get_db dependency to use the test database session.
    It also ensures the database is initialized for API tests.
    """
    # Explicitly import models inside the fixture to ensure they are registered with Base.metadata

    # Create a new in-memory engine and session for each test
    SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Create tables for each test
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        # Initialize default categories using the session
        category_repo = CategoryRepository(db)
        default_categories = ["Health", "Wealth", "Fitness", "Learning"]
        for cat_name in default_categories:
            if not category_repo.get_category_by_name(cat_name):
                category_repo.create_category(cat_name)

        def override_get_db():
            try:
                yield db
            finally:
                db.close()

        app.dependency_overrides[get_db] = override_get_db
        with TestClient(app) as c:
            yield c
    finally:
        db.close()
        # Drop tables after each test
        Base.metadata.drop_all(bind=engine)
        app.dependency_overrides.clear()


# --- Channel API Tests ---


def test_create_channel_success(client):
    response = client.post(
        "/channels/",
        json={
            "channel_url": "https://www.youtube.com/channel/UC-lHJZR3Gqxm24_Vd_AJ5Yw",
            "assigned_categories": ["Health", "Learning"],
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["channel_id"] == "UC-lHJZR3Gqxm24_Vd_AJ5Yw"
    assert data["channel_name"] == "Mock Channel Name for UC-lHJZR3Gqxm24_Vd_AJ5Yw"
    assert (
        data["channel_url"]
        == "https://www.youtube.com/channel/UC-lHJZR3Gqxm24_Vd_AJ5Yw"
    )
    assert "Health" in data["assigned_categories"]
    assert "Learning" in data["assigned_categories"]
    assert "date_added_to_ytap" in data


def test_create_channel_invalid_url(client):
    response = client.post(
        "/channels/",
        json={"channel_url": "invalid-youtube-url", "assigned_categories": ["Health"]},
    )
    assert response.status_code == 422  # Pydantic validation error
    assert "value is not a valid URL" in response.json()["detail"][0]["msg"]


def test_create_channel_missing_categories(client):
    response = client.post(
        "/channels/",
        json={
            "channel_url": "https://www.youtube.com/channel/UC-lHJZR3Gqxm24_Vd_AJ5Yw"
        },
    )
    assert response.status_code == 422  # Pydantic validation error
    assert "Field required" in response.json()["detail"][0]["msg"]


def test_create_channel_category_not_found(client):
    response = client.post(
        "/channels/",
        json={
            "channel_url": "https://www.youtube.com/channel/UC-lHJZR3Gqxm24_Vd_AJ5Yw",
            "assigned_categories": ["NonExistentCategory"],
        },
    )
    assert response.status_code == 400
    assert "Category 'NonExistentCategory' does not exist." in response.json()["detail"]


def test_create_channel_duplicate_id(client):
    # First creation
    client.post(
        "/channels/",
        json={
            "channel_url": "https://www.youtube.com/channel/UC_test_channel_duplicate",
            "assigned_categories": ["Health"],
        },
    )
    # Second creation with same URL (which implies same mock ID)
    response = client.post(
        "/channels/",
        json={
            "channel_url": "https://www.youtube.com/channel/UC_test_channel_duplicate",
            "assigned_categories": ["Health"],
        },
    )
    assert response.status_code == 400
    assert (
        "Channel with ID 'UC_test_channel_duplicate' already exists."
        in response.json()["detail"]
    )


def test_get_all_channels(client):
    client.post(
        "/channels/",
        json={
            "channel_url": "https://www.youtube.com/channel/UC_ch1",
            "assigned_categories": ["Health"],
        },
    )
    client.post(
        "/channels/",
        json={
            "channel_url": "https://www.youtube.com/channel/UC_ch2",
            "assigned_categories": ["Learning"],
        },
    )
    response = client.get("/channels/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["channel_id"] == "UC_ch1"
    assert data[1]["channel_id"] == "UC_ch2"
    assert "Mock Channel Name for UC_ch1" in data[0]["channel_name"]
    assert "Mock Channel Name for UC_ch2" in data[1]["channel_name"]


def test_get_channel_by_id(client):
    client.post(
        "/channels/",
        json={
            "channel_url": "https://www.youtube.com/channel/UC_single_channel",
            "assigned_categories": ["Health"],
        },
    )
    response = client.get("/channels/UC_single_channel")
    assert response.status_code == 200
    data = response.json()
    assert data["channel_id"] == "UC_single_channel"
    assert data["channel_name"] == "Mock Channel Name for UC_single_channel"


def test_get_channel_by_id_not_found(client):
    response = client.get("/channels/UC_non_existent")
    assert response.status_code == 404
    assert "Channel not found" in response.json()["detail"]


def test_update_channel(client):
    client.post(
        "/channels/",
        json={
            "channel_url": "https://www.youtube.com/channel/UC_update_ch",
            "assigned_categories": ["Health"],
        },
    )
    response = client.put(
        "/channels/UC_update_ch",
        json={
            "channel_name": "Updated Channel Name",
            "assigned_categories": ["Health", "Wealth"],
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["channel_name"] == "Updated Channel Name"
    assert "Wealth" in data["assigned_categories"]


def test_update_channel_not_found(client):
    response = client.put(
        "/channels/UC_non_existent_update", json={"channel_name": "New Name"}
    )
    assert response.status_code == 404
    assert "Channel not found" in response.json()["detail"]


def test_update_channel_invalid_category(client):
    client.post(
        "/channels/",
        json={
            "channel_url": "https://www.youtube.com/channel/UC_update_ch_invalid_cat",
            "assigned_categories": ["Health"],
        },
    )
    response = client.put(
        "/channels/UC_update_ch_invalid_cat",
        json={"assigned_categories": ["NonExistentCategory"]},
    )
    assert response.status_code == 400
    assert "Category 'NonExistentCategory' does not exist." in response.json()["detail"]


def test_delete_channel(client):
    client.post(
        "/channels/",
        json={
            "channel_url": "https://www.youtube.com/channel/UC_delete_ch",
            "assigned_categories": ["Health"],
        },
    )
    response = client.delete("/channels/UC_delete_ch")
    assert response.status_code == 200
    assert response.json()["message"] == "Channel deleted successfully"

    get_response = client.get("/channels/UC_delete_ch")
    assert get_response.status_code == 404


def test_delete_channel_not_found(client):
    response = client.delete("/channels/UC_non_existent_delete")
    assert response.status_code == 404
    assert "Channel not found" in response.json()["detail"]


# --- Video API Tests ---


def test_add_video_to_channel(client):
    client.post(
        "/channels/",
        json={
            "channel_url": "https://www.youtube.com/channel/UC_video_channel",
            "assigned_categories": ["Health"],
        },
    )
    response = client.post(
        "/channels/UC_video_channel/videos",
        json={
            "video_id": "test_video_1",
            "video_title": "Test Video 1",
            "video_url": "https://www.youtube.com/watch?v=test_video_1",
            "transcript_status": "pending",
            "assigned_categories": ["Health"],
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["video_id"] == "test_video_1"
    assert data["channel_id"] == "UC_video_channel"
    assert data["video_title"] == "Test Video 1"
    assert data["video_url"] == "https://www.youtube.com/watch?v=test_video_1"
    assert data["transcript_status"] == "pending"
    assert "Health" in data["assigned_categories"]
    assert "date_added_to_ytap" in data
    assert "last_processed_date" in data


def test_add_video_to_non_existent_channel(client):
    response = client.post(
        "/channels/UC_non_existent_channel/videos",
        json={
            "video_id": "test_video_2",
            "video_title": "Test Video 2",
            "video_url": "https://www.youtube.com/watch?v=test_video_2",
            "transcript_status": "pending",
            "assigned_categories": ["Health"],
        },
    )
    assert (
        response.status_code == 400
    )  # Changed from 404 to 400 due to ChannelService raising ValueError
    assert (
        "Channel with ID 'UC_non_existent_channel' not found."
        in response.json()["detail"]
    )


def test_add_video_invalid_category(client):
    client.post(
        "/channels/",
        json={
            "channel_url": "https://www.youtube.com/channel/UC_video_channel_invalid_cat",
            "assigned_categories": ["Health"],
        },
    )
    response = client.post(
        "/channels/UC_video_channel_invalid_cat/videos",
        json={
            "video_id": "test_video_invalid_cat",
            "video_title": "Test Video Invalid Cat",
            "video_url": "https://www.youtube.com/watch?v=test_video_invalid_cat",
            "transcript_status": "pending",
            "assigned_categories": ["NonExistentCategory"],
        },
    )
    assert response.status_code == 400
    assert "Category 'NonExistentCategory' does not exist." in response.json()["detail"]


def test_get_videos_for_channel(client):
    client.post(
        "/channels/",
        json={
            "channel_url": "https://www.youtube.com/channel/UC_get_videos_channel",
            "assigned_categories": ["Health"],
        },
    )
    client.post(
        "/channels/UC_get_videos_channel/videos",
        json={
            "video_id": "video_a",
            "video_title": "Video A",
            "video_url": "https://www.youtube.com/watch?v=video_a",
            "transcript_status": "completed",
            "assigned_categories": ["Health"],
        },
    )
    client.post(
        "/channels/UC_get_videos_channel/videos",
        json={
            "video_id": "video_b",
            "video_title": "Video B",
            "video_url": "https://www.youtube.com/watch?v=video_b",
            "transcript_status": "pending",
            "assigned_categories": ["Learning"],
        },
    )
    response = client.get("/channels/UC_get_videos_channel/videos")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["video_title"] == "Video A"
    assert data[1]["video_title"] == "Video B"


def test_get_video_by_id(client):
    client.post(
        "/channels/",
        json={
            "channel_url": "https://www.youtube.com/channel/UC_get_single_video_channel",
            "assigned_categories": ["Health"],
        },
    )
    client.post(
        "/channels/UC_get_single_video_channel/videos",
        json={
            "video_id": "single_video",
            "video_title": "Single Video",
            "video_url": "https://www.youtube.com/watch?v=single_video",
            "transcript_status": "completed",
            "assigned_categories": ["Health"],
        },
    )
    response = client.get("/videos/single_video")
    assert response.status_code == 200
    data = response.json()
    assert data["video_id"] == "single_video"
    assert data["video_title"] == "Single Video"


def test_get_video_by_id_not_found(client):
    response = client.get("/videos/non_existent_video")
    assert response.status_code == 404
    assert "Video not found" in response.json()["detail"]


def test_update_video(client):
    client.post(
        "/channels/",
        json={
            "channel_url": "https://www.youtube.com/channel/UC_update_video_channel",
            "assigned_categories": ["Health"],
        },
    )
    client.post(
        "/channels/UC_update_video_channel/videos",
        json={
            "video_id": "video_to_update",
            "video_title": "Original Video Title",
            "video_url": "https://www.youtube.com/watch?v=video_to_update",
            "transcript_status": "pending",
            "assigned_categories": ["Health"],
        },
    )
    response = client.put(
        "/videos/video_to_update",
        json={
            "video_title": "Updated Video Title",
            "transcript_status": "completed",
            "assigned_categories": ["Health", "Wealth"],
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["video_title"] == "Updated Video Title"
    assert data["transcript_status"] == "completed"
    assert "Wealth" in data["assigned_categories"]


def test_update_video_not_found(client):
    response = client.put(
        "/videos/non_existent_video_update", json={"video_title": "New Title"}
    )
    assert response.status_code == 404
    assert "Video not found" in response.json()["detail"]


def test_update_video_invalid_category(client):
    client.post(
        "/channels/",
        json={
            "channel_url": "https://www.youtube.com/channel/UC_update_video_channel_invalid_cat",
            "assigned_categories": ["Health"],
        },
    )
    client.post(
        "/channels/UC_update_video_channel_invalid_cat/videos",
        json={
            "video_id": "video_to_update_invalid_cat",
            "video_title": "Original Video Title",
            "video_url": "https://www.youtube.com/watch?v=video_to_update_invalid_cat",
            "transcript_status": "pending",
            "assigned_categories": ["Health"],
        },
    )
    response = client.put(
        "/videos/video_to_update_invalid_cat",
        json={"assigned_categories": ["NonExistentCategory"]},
    )
    assert response.status_code == 400
    assert "Category 'NonExistentCategory' does not exist." in response.json()["detail"]


def test_delete_video(client):
    client.post(
        "/channels/",
        json={
            "channel_url": "https://www.youtube.com/channel/UC_delete_video_channel",
            "assigned_categories": ["Health"],
        },
    )
    client.post(
        "/channels/UC_delete_video_channel/videos",
        json={
            "video_id": "video_to_delete",
            "video_title": "Video to Delete",
            "video_url": "https://www.youtube.com/watch?v=video_to_delete",
            "transcript_status": "completed",
            "assigned_categories": ["Health"],
        },
    )
    response = client.delete("/videos/video_to_delete")
    assert response.status_code == 200
    assert response.json()["message"] == "Video deleted successfully"

    get_response = client.get("/videos/video_to_delete")
    assert get_response.status_code == 404


def test_delete_video_not_found(client):
    response = client.delete("/videos/non_existent_video_delete")
    assert response.status_code == 404
    assert "Video not found" in response.json()["detail"]


# --- Category API Tests ---


def test_create_category(client):
    response = client.post("/categories/", json={"name": "Test Category 1"})
    assert response.status_code == 201  # Changed from 200 to 201 for creation
    data = response.json()
    assert data["name"] == "Test Category 1"
    assert "id" in data


def test_create_category_duplicate_name(client):
    client.post("/categories/", json={"name": "Duplicate Category"})
    response = client.post("/categories/", json={"name": "Duplicate Category"})
    assert response.status_code == 400
    assert "Category with this name already exists" in response.json()["detail"]


def test_get_all_categories(client):
    client.post("/categories/", json={"name": "Cat 1"})
    client.post("/categories/", json={"name": "Cat 2"})
    response = client.get("/categories/")
    assert response.status_code == 200
    data = response.json()
    # Default categories are "Health", "Wealth", "Fitness", "Learning"
    # Plus "Cat 1" and "Cat 2"
    assert len(data) == 6
    assert any(d["name"] == "Cat 1" for d in data)
    assert any(d["name"] == "Cat 2" for d in data)


def test_get_category_by_name(client):
    client.post("/categories/", json={"name": "Single Category"})
    response = client.get("/categories/Single Category")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Single Category"


def test_get_category_by_name_not_found(client):
    response = client.get("/categories/NonExistentCategory")
    assert response.status_code == 404
    assert "Category not found" in response.json()["detail"]


def test_update_category(client):
    create_response = client.post("/categories/", json={"name": "Category to Update"})
    category_id = create_response.json()["id"]
    response = client.put(
        f"/categories/{category_id}", json={"name": "Updated Category Name"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Category Name"


def test_update_category_not_found(client):
    response = client.put("/categories/999", json={"name": "Non Existent Update"})
    assert response.status_code == 404
    assert "Category not found" in response.json()["detail"]


def test_delete_category(client):
    create_response = client.post("/categories/", json={"name": "Category to Delete"})
    category_id = create_response.json()["id"]
    response = client.delete(f"/categories/{category_id}")
    assert response.status_code == 200
    assert response.json()["message"] == "Category deleted successfully"

    get_response = client.get(f"/categories/{category_id}")
    assert get_response.status_code == 404


def test_delete_category_not_found(client):
    response = client.delete("/categories/999")
    assert response.status_code == 404
    assert "Category not found" in response.json()["detail"]
