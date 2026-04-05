import factory

from src.models import Order, OrderItem, Payment, Preferences, Product, Profile, User

# Assuming a session is passed to the factory or a global session is available
# For testing, it's often better to pass the session via a fixture.


class BaseFactory(factory.Factory):
    class Meta:
        abstract = True

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        session = kwargs.pop("session", None)
        if session is None:
            raise ValueError("Session must be provided to the factory.")
        obj = model_class(*args, **kwargs)
        session.add(obj)
        session.flush()  # Use flush to get IDs for related objects immediately
        return obj


class UserFactory(BaseFactory):
    class Meta:
        model = User

    id = factory.Sequence(lambda n: n + 1)
    email = factory.Faker("email")
    is_premium = False
    name = factory.Faker("name")


class ProfileFactory(BaseFactory):
    class Meta:
        model = Profile

    user = factory.SubFactory(UserFactory)
    bio = factory.Faker("text")
    avatar_url = factory.Faker("url")


class PreferencesFactory(BaseFactory):
    class Meta:
        model = Preferences

    user = factory.SubFactory(UserFactory)
    notification_enabled = True
    theme = factory.Faker("random_element", elements=["light", "dark"])


class ProductFactory(BaseFactory):
    class Meta:
        model = Product

    id = factory.Sequence(lambda n: n + 1)
    name = factory.Faker("word")
    price = factory.Faker("pydecimal", left_digits=2, right_digits=2, positive=True)


class OrderFactory(BaseFactory):
    class Meta:
        model = Order

    user = factory.SubFactory(UserFactory)
    amount = factory.Faker("pydecimal", left_digits=3, right_digits=2, positive=True)


class OrderItemFactory(BaseFactory):
    class Meta:
        model = OrderItem

    order = factory.SubFactory(OrderFactory)
    product = factory.SubFactory(ProductFactory)
    quantity = factory.Faker("random_int", min=1, max=5)


class PaymentFactory(BaseFactory):
    class Meta:
        model = Payment

    order = factory.SubFactory(OrderFactory)
    amount = factory.Faker("pydecimal", left_digits=3, right_digits=2, positive=True)
    status = factory.Faker(
        "random_element", elements=["pending", "completed", "failed"]
    )
