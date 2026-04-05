from src.models import Order, User
from tests.factories import OrderFactory, UserFactory


def test_create_user(db_session, test_data_manager):
    # ARRANGE
    email = "test@example.com"
    name = "Test User"

    # ACT
    user = test_data_manager.create(UserFactory, email=email, name=name)
    db_session.commit()

    # ASSERT
    retrieved_user = db_session.query(User).filter_by(email=email).first()
    assert retrieved_user is not None
    assert retrieved_user.email == email
    assert retrieved_user.name == name
    assert retrieved_user.id == user.id


def test_create_order_for_user(db_session, test_data_manager):
    # ARRANGE
    user = test_data_manager.create(UserFactory, email="order_user@example.com")
    amount = 100.50

    # ACT
    order = test_data_manager.create(OrderFactory, user=user, amount=amount)
    db_session.commit()

    # ASSERT
    retrieved_order = db_session.query(Order).filter_by(id=order.id).first()
    assert retrieved_order is not None
    assert retrieved_order.user_id == user.id
    assert (
        float(retrieved_order.amount) == amount
    )  # Convert Decimal to float for comparison
    assert retrieved_order.user.email == user.email


def test_user_profile_relationship(db_session, test_data_manager):
    # ARRANGE
    test_data_manager.create_user_with_profile(email="profile@example.com")
    db_session.commit()

    # ACT
    retrieved_user = (
        db_session.query(User).filter_by(email="profile@example.com").first()
    )

    # ASSERT
    assert retrieved_user.profile is not None
    assert retrieved_user.profile.user_id == retrieved_user.id
    assert retrieved_user.preferences is not None
    assert retrieved_user.preferences.user_id == retrieved_user.id
