import pytest
from sqlalchemy.orm import sessionmaker

from src.database import Base, engine


@pytest.fixture(scope="function")
def db_session():
    """Provides a transactional test database session."""
    connection = engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection)
    session = Session()

    # Ensure all tables are created for the test session
    Base.metadata.create_all(bind=engine)

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def test_data_manager(db_session):
    class TestDataManager:
        def __init__(self, session):
            self.session = session
            self.created_objects = []
            self.cleanup_callbacks = []

        def create(self, factory_class, **kwargs):
            obj = factory_class(session=self.session, **kwargs)
            self.created_objects.append(obj)
            return obj

        def create_user_with_profile(self, **overrides):
            from tests.factories import PreferencesFactory, ProfileFactory, UserFactory

            user = self.create(UserFactory, **overrides)
            self.create(ProfileFactory, user=user)
            self.create(PreferencesFactory, user=user)
            return user

        def create_complete_order(self, user=None, **overrides):
            from tests.factories import (
                OrderFactory,
                OrderItemFactory,
                PaymentFactory,
                ProductFactory,
            )

            if not user:
                user = self.create_user_with_profile()
            products = [self.create(ProductFactory) for _ in range(2)]
            order = self.create(OrderFactory, user=user, **overrides)
            [self.create(OrderItemFactory, order=order, product=p) for p in products]
            self.create(PaymentFactory, order=order)
            return order

        def cleanup(self):
            # Objects created within the session are rolled back by db_session fixture
            pass

    manager = TestDataManager(db_session)
    yield manager
    manager.cleanup()
