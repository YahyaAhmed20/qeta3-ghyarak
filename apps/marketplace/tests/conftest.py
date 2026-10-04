import pytest
from apps.catalog.models import ProductCompatibility, CompatibilityStatus

from apps.vehicles.models import (
    VehicleMake,
    VehicleModel,
    VehicleGeneration,
    VehicleEngine,
    VehicleVariant,
)
from apps.accounts.models import User
from apps.catalog.models import Brand, Category, Product
from apps.stores.models import Store, StoreStatus
from apps.inventory.models import Inventory
from apps.stores.models import SellerProduct
from apps.catalog.models import (
    Brand,
    Category,
    Product,
    ProductPartNumber,
)
@pytest.fixture
def seller_owner():
    return User.objects.create_user(
        phone="+201001234567",
        role="SELLER_OWNER",
    )


@pytest.fixture
def active_store(seller_owner):
    return Store.objects.create(
        owner=seller_owner,
        name="Alfa Spare Parts",
        slug="alfa-spare-parts",
        phone="+201001234567",
        address="Suez",
        city="Suez",
        status=StoreStatus.ACTIVE,
        is_verified=True,
    )


@pytest.fixture
def category():
    return Category.objects.create(
        name="Filters",
        slug="filters",
    )


@pytest.fixture
def brand():
    return Brand.objects.create(
        name="Bosch",
        slug="bosch",
    )


@pytest.fixture
def active_product(category, brand):
    return Product.objects.create(
        category=category,
        brand=brand,
        name="Bosch Oil Filter",
        slug="bosch-oil-filter",
        product_type="AFTERMARKET",
        is_active=True,
    )


@pytest.fixture
def inactive_product(category, brand):
    return Product.objects.create(
        category=category,
        brand=brand,
        name="Inactive Filter",
        slug="inactive-filter",
        product_type="AFTERMARKET",
        is_active=False,
    )
    
@pytest.fixture
def marketplace_seller_product(active_store, active_product):
    seller_product = SellerProduct.objects.create(
        store=active_store,
        product=active_product,
        price="2300.00",
        sale_price="2200.00",
        is_active=True,
    )

    Inventory.objects.create(
        seller_product=seller_product,
        on_hand=10,
        reserved=0,
    )

    return seller_product


@pytest.fixture
def marketplace_part_number(marketplace_seller_product):
    return ProductPartNumber.objects.create(
        product=marketplace_seller_product.product,
        part_number="90915-YZZD1",
        number_type="OEM",
        brand=marketplace_seller_product.product.brand,
    )
    
@pytest.fixture
def other_category():
    return Category.objects.create(
        name="Brakes",
        slug="brakes",
    )
    
    
@pytest.fixture
def vehicle_variant():
    make = VehicleMake.objects.create(
        name="Skoda",
        slug="skoda",
    )

    model = VehicleModel.objects.create(
        make=make,
        name="Octavia",
        slug="octavia",
    )

    generation = VehicleGeneration.objects.create(
        model=model,
        name="A7",
        slug="a7",
        year_from=2013,
        year_to=2020,
    )

    engine = VehicleEngine.objects.create(
        generation=generation,
        name="1.6 MPI",
        code="CWVA",
        displacement_cc=1598,
        fuel_type="PETROL",
        power_hp=110,
    )

    return VehicleVariant.objects.create(
        engine=engine,
        name="1.6 MPI Automatic",
        slug="1-6-mpi-automatic",
        transmission="AUTOMATIC",
        market="EGYPT",
    )


@pytest.fixture
def product_compatibility(
    marketplace_seller_product,
    vehicle_variant,
):
    return ProductCompatibility.objects.create(
        product=marketplace_seller_product.product,
        vehicle_variant=vehicle_variant,
        status=CompatibilityStatus.APPROVED,
    )
    
    
@pytest.fixture
def paginated_marketplace_products(active_store, category, brand):
    products = []

    for index in range(21):
        product = Product.objects.create(
            category=category,
            brand=brand,
            name=f"Pagination Product {index}",
            slug=f"pagination-product-{index}",
            product_type="AFTERMARKET",
            is_active=True,
        )

        seller_product = SellerProduct.objects.create(
            store=active_store,
            product=product,
            price="100.00",
            is_active=True,
        )

        Inventory.objects.create(
            seller_product=seller_product,
            on_hand=10,
            reserved=0,
        )

        products.append(product)

    return products