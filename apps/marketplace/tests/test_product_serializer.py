import pytest

from apps.inventory.models import Inventory
from apps.marketplace.api.serializers import MarketplaceProductSerializer
from apps.stores.models import SellerProduct
from apps.marketplace.api.serializers import (
    MarketplaceCompatibilitySerializer,
    MarketplacePartNumberSerializer,
    MarketplaceProductDetailSerializer,
)

from apps.catalog.models import ProductCompatibility
from apps.catalog.models.compatibility import CompatibilityStatus
from apps.vehicles.models import (
    VehicleEngine,
    VehicleGeneration,
    VehicleMake,
    VehicleModel,
    VehicleVariant,
)
@pytest.mark.django_db
def test_marketplace_product_serializer_returns_product_data(
    active_store,
    active_product,
):
    seller_product = SellerProduct.objects.create(
        store=active_store,
        product=active_product,
        price="250.00",
        sale_price="225.00",
    )

    Inventory.objects.create(
        seller_product=seller_product,
        on_hand=10,
        reserved=2,
    )

    data = MarketplaceProductSerializer(active_product).data

    assert data["id"] == str(active_product.id)
    assert data["name"] == "Bosch Oil Filter"
    assert data["slug"] == "bosch-oil-filter"
    assert data["brand"] == "Bosch"
    assert data["category"] == "Filters"
    assert data["product_type"] == "AFTERMARKET"

    assert len(data["sellers"]) == 1

    seller = data["sellers"][0]

    assert seller["store_name"] == "Alfa Spare Parts"
    assert seller["city"] == "Suez"
    assert seller["price"] == "250.00"
    assert seller["sale_price"] == "225.00"
    assert seller["available"] == 8


@pytest.mark.django_db
def test_marketplace_product_serializer_supports_multiple_sellers(
    active_store,
    active_product,
):
    from apps.accounts.models import User
    from apps.stores.models import Store, StoreStatus

    second_owner = User.objects.create_user(
        phone="+201001234568",
        role="SELLER_OWNER",
    )

    second_store = Store.objects.create(
        owner=second_owner,
        name="Beta Spare Parts",
        slug="beta-spare-parts",
        phone="+201001234568",
        address="Suez",
        city="Suez",
        status=StoreStatus.ACTIVE,
        is_verified=True,
    )

    first_seller_product = SellerProduct.objects.create(
        store=active_store,
        product=active_product,
        price="250.00",
    )

    second_seller_product = SellerProduct.objects.create(
        store=second_store,
        product=active_product,
        price="230.00",
    )

    Inventory.objects.create(
        seller_product=first_seller_product,
        on_hand=10,
        reserved=2,
    )

    Inventory.objects.create(
        seller_product=second_seller_product,
        on_hand=5,
        reserved=1,
    )

    data = MarketplaceProductSerializer(active_product).data

    assert len(data["sellers"]) == 2

    stores = {
        seller["store_name"]
        for seller in data["sellers"]
    }

    assert stores == {
        "Alfa Spare Parts",
        "Beta Spare Parts",
    }
    
    
@pytest.mark.django_db
def test_marketplace_part_number_serializer(
    marketplace_part_number,
):
    serializer = MarketplacePartNumberSerializer(
        marketplace_part_number,
    )

    data = serializer.data

    assert data["id"] == str(marketplace_part_number.id)
    assert data["part_number"] == "90915-YZZD1"
    assert data["number_type"] == "OEM"
    assert data["brand"] == "Bosch"
    
    
@pytest.mark.django_db
def test_marketplace_product_detail_serializer(
    marketplace_seller_product,
):
    product = marketplace_seller_product.product

    serializer = MarketplaceProductDetailSerializer(product)

    data = serializer.data

    assert data["id"] == str(product.id)
    assert data["name"] == product.name
    assert data["slug"] == product.slug
    assert data["brand"] == "Bosch"
    assert data["category"] == "Filters"
    
    
@pytest.mark.django_db
def test_marketplace_product_detail_serializer_contains_seller(
    marketplace_seller_product,
):
    product = marketplace_seller_product.product

    serializer = MarketplaceProductDetailSerializer(product)

    data = serializer.data

    assert len(data["sellers"]) == 1

    seller = data["sellers"][0]

    assert seller["store_name"] == "Alfa Spare Parts"
    assert seller["city"] == "Suez"
    assert seller["price"] == "2300.00"
    assert seller["sale_price"] == "2200.00"
    assert seller["available"] == 10
    
    
@pytest.mark.django_db
def test_marketplace_compatibility_serializer(
    marketplace_seller_product,
):
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
        year_to=2019,
    )

    engine = VehicleEngine.objects.create(
        generation=generation,
        name="1.6 MPI",
        code="CWVA",
        displacement_cc=1598,
        fuel_type="PETROL",
        power_hp=110,
    )

    variant = VehicleVariant.objects.create(
        engine=engine,
        name="1.6 MPI Automatic",
        slug="1-6-mpi-automatic",
        transmission="AUTOMATIC",
        market="EGYPT",
    )

    compatibility = ProductCompatibility.objects.create(
        product=marketplace_seller_product.product,
        vehicle_variant=variant,
        status=CompatibilityStatus.APPROVED,
        notes="Fits this vehicle.",
    )

    serializer = MarketplaceCompatibilitySerializer(
        compatibility,
    )

    data = serializer.data

    assert data["id"] == str(compatibility.id)
    assert data["make"] == "Skoda"
    assert data["model"] == "Octavia"
    assert data["generation"] == "A7"
    assert data["engine"] == "1.6 MPI"
    assert data["variant"] == "1.6 MPI Automatic"
    assert data["transmission"] == "AUTOMATIC"
    assert data["market"] == "EGYPT"
    assert data["notes"] == "Fits this vehicle."
    
@pytest.mark.django_db
def test_marketplace_product_detail_serializer_contains_compatibility(
    marketplace_seller_product,
):
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
    )

    engine = VehicleEngine.objects.create(
        generation=generation,
        name="1.6 MPI",
    )

    variant = VehicleVariant.objects.create(
        engine=engine,
        name="1.6 MPI Automatic",
        slug="1-6-mpi-automatic",
    )

    ProductCompatibility.objects.create(
        product=marketplace_seller_product.product,
        vehicle_variant=variant,
        status=CompatibilityStatus.APPROVED,
        notes="Fits this vehicle.",
    )

    product = marketplace_seller_product.product

    serializer = MarketplaceProductDetailSerializer(product)

    data = serializer.data

    assert len(data["compatibilities"]) == 1

    compatibility = data["compatibilities"][0]

    assert compatibility["make"] == "Skoda"
    assert compatibility["model"] == "Octavia"
    assert compatibility["generation"] == "A7"
    assert compatibility["engine"] == "1.6 MPI"
    assert compatibility["variant"] == "1.6 MPI Automatic"
    assert compatibility["notes"] == "Fits this vehicle."