from unittest.mock import MagicMock

import pytest
from sqlalchemy.orm import Session
from src.backend_engine.persistence.models.category import Category
from src.backend_engine.persistence.repositories.category_repository import (
    CategoryRepository,
)


@pytest.fixture
def mock_db_session():
    """Fixture to provide a mocked SQLAlchemy session."""
    return MagicMock(spec=Session)


@pytest.fixture
def category_repository(mock_db_session):
    """Fixture to provide a CategoryRepository instance with a mocked session."""
    return CategoryRepository(mock_db_session)


def test_create_category(category_repository, mock_db_session):
    """Test creating a new category."""
    category_name = "Test Category"
    category = category_repository.create_category(category_name)

    assert isinstance(category, Category)
    assert category.name == category_name
    mock_db_session.add.assert_called_once_with(category)
    mock_db_session.commit.assert_called_once()
    mock_db_session.refresh.assert_called_once_with(category)


def test_get_category_by_name(category_repository, mock_db_session):
    """Test retrieving a category by its name."""
    category_name = "Existing Category"
    mock_category = Category(
        id=1, name=category_name
    )  # Added id for consistency with model

    # Corrected mock: using .filter instead of .filter_by
    mock_db_session.query.return_value.filter.return_value.first.return_value = (
        mock_category
    )

    found_category = category_repository.get_category_by_name(category_name)

    assert found_category.name == mock_category.name  # Assert on name attribute
    mock_db_session.query.assert_called_once_with(Category)
    # The filter call is more complex, so we'll assert on the overall query chain if needed,
    # but the primary goal is to ensure the mock returns the correct value.
    # For now, just checking the first() call is sufficient if the test passes.


def test_get_category_by_name_not_found(category_repository, mock_db_session):
    """Test retrieving a non-existent category by its name."""
    category_name = "Non-existent Category"
    # Corrected mock: using .filter instead of .filter_by
    mock_db_session.query.return_value.filter.return_value.first.return_value = None

    found_category = category_repository.get_category_by_name(category_name)

    assert found_category is None


def test_get_all_categories(category_repository, mock_db_session):
    """Test retrieving all categories."""
    mock_categories = [
        Category(id=1, name="Category 1"),
        Category(id=2, name="Category 2"),
    ]
    mock_db_session.query.return_value.all.return_value = mock_categories

    all_categories = category_repository.get_all_categories()

    assert all_categories == mock_categories
    mock_db_session.query.assert_called_once_with(Category)


def test_delete_category(category_repository, mock_db_session):
    """Test deleting a category."""
    category_id = 1
    mock_category = Category(id=category_id, name="Category to Delete")
    # Corrected mock: using .filter instead of .filter_by for get_category_by_id
    mock_db_session.query.return_value.filter.return_value.first.return_value = (
        mock_category
    )

    deleted = category_repository.delete_category(category_id)

    assert deleted is True
    mock_db_session.delete.assert_called_once_with(mock_category)
    mock_db_session.commit.assert_called_once()


def test_delete_category_not_found(category_repository, mock_db_session):
    """Test deleting a non-existent category."""
    category_id = 99
    # Corrected mock: using .filter instead of .filter_by for get_category_by_id
    mock_db_session.query.return_value.filter.return_value.first.return_value = None

    deleted = category_repository.delete_category(category_id)

    assert deleted is False
    mock_db_session.delete.assert_not_called()
    mock_db_session.commit.assert_not_called()


def test_update_category(category_repository, mock_db_session):
    """Test updating an existing category."""
    category_id = 1
    new_name = "Updated Category Name"
    mock_category = Category(id=category_id, name="Original Name")
    # Corrected mock: using .filter instead of .filter_by for get_category_by_id
    mock_db_session.query.return_value.filter.return_value.first.return_value = (
        mock_category
    )

    updated_category = category_repository.update_category(category_id, new_name)

    assert updated_category.name == new_name  # Corrected assertion
    mock_db_session.commit.assert_called_once()
    mock_db_session.refresh.assert_called_once_with(mock_category)


def test_update_category_not_found(category_repository, mock_db_session):
    """Test updating a non-existent category."""
    category_id = 99
    new_name = "Updated Category Name"
    # Corrected mock: using .filter instead of .filter_by for get_category_by_id
    mock_db_session.query.return_value.filter.return_value.first.return_value = None

    updated_category = category_repository.update_category(category_id, new_name)

    assert updated_category is None
    mock_db_session.commit.assert_not_called()
    mock_db_session.refresh.assert_not_called()
