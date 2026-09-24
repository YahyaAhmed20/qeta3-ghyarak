import pytest
from decimal import Decimal

from apps.accounts.models import User
from apps.catalog.models import Category, Product
from apps.stores.models import Store, StoreStatus, SellerProduct
from apps.cart.constants import CartStatus
from apps.cart.models import Cart, CartItem
from apps.cart.services.cart import CartService
from apps.cart.services.cart_item import CartItemService


@pytest.mark.django_db
class TestGetOrCreateActiveCart:

    def test_creates_new_active_cart(
        self,
        customer,
        active_store,
    ):
        cart, created = CartService.get_or_create_active_cart(
            customer=customer,
            store=active_store,
        )

        assert created is True
        assert cart.customer == customer
        assert cart.store == active_store
        assert cart.status == CartStatus.ACTIVE

    def test_returns_existing_active_cart(
        self,
        customer,
        active_store,
    ):
        existing_cart = Cart.objects.create(
            customer=customer,
            store=active_store,
            status=CartStatus.ACTIVE,
        )

        cart, created = CartService.get_or_create_active_cart(
            customer=customer,
            store=active_store,
        )

        assert created is False
        assert cart.id == existing_cart.id

    def test_customer_cannot_have_active_cart_for_another_store(
        self,
        customer,
        active_store,
        active_product,
    ):
        other_owner = User.objects.create_user(
            phone="+201001234571",
            role="SELLER_OWNER",
        )

        other_store = Store.objects.create(
            owner=other_owner,
            name="Other Store Service",
            slug="other-store-service",
            phone="+201001234571",
            address="Suez",
            city="Suez",
            status=StoreStatus.ACTIVE,
            is_verified=True,
        )

        Cart.objects.create(
            customer=customer,
            store=active_store,
            status=CartStatus.ACTIVE,
        )

        with pytest.raises(ValueError, match="another store"):
            CartService.get_or_create_active_cart(
                customer=customer,
                store=other_store,
            )

    def test_non_customer_cannot_create_cart(
        self,
        seller_owner,
        active_store,
    ):
        with pytest.raises(ValueError, match="Only customers"):
            CartService.get_or_create_active_cart(
                customer=seller_owner,
                store=active_store,
            )

    def test_inactive_store_cannot_create_cart(
        self,
        customer,
        inactive_store,
    ):
        with pytest.raises(ValueError, match="active and verified"):
            CartService.get_or_create_active_cart(
                customer=customer,
                store=inactive_store,
            )

    def test_unverified_store_cannot_create_cart(
        self,
        customer,
        unverified_store,
    ):
        with pytest.raises(ValueError, match="active and verified"):
            CartService.get_or_create_active_cart(
                customer=customer,
                store=unverified_store,
            )


@pytest.mark.django_db
class TestAddCartItem:

    def test_add_new_item(
        self,
        cart,
        seller_product,
    ):
        item, created = CartItemService.add_item(
            cart=cart,
            seller_product=seller_product,
            quantity=2,
        )

        assert created is True
        assert item.cart == cart
        assert item.seller_product == seller_product
        assert item.quantity == 2
        assert item.unit_price == Decimal("250.00")

    def test_add_existing_item_increases_quantity(
        self,
        cart,
        seller_product,
    ):
        first_item, created = CartItemService.add_item(
            cart=cart,
            seller_product=seller_product,
            quantity=2,
        )

        second_item, created = CartItemService.add_item(
            cart=cart,
            seller_product=seller_product,
            quantity=3,
        )

        assert first_item.id == second_item.id
        assert created is False
        assert second_item.quantity == 5

    def test_sale_price_is_used(
        self,
        cart,
        seller_product,
    ):
        seller_product.sale_price = Decimal("200.00")
        seller_product.save(update_fields=["sale_price"])

        item, created = CartItemService.add_item(
            cart=cart,
            seller_product=seller_product,
            quantity=1,
        )

        assert created is True
        assert item.unit_price == Decimal("200.00")

    def test_inactive_product_cannot_be_added(
        self,
        cart,
        seller_product,
    ):
        seller_product.is_active = False
        seller_product.save(update_fields=["is_active"])

        with pytest.raises(ValueError, match="must be active"):
            CartItemService.add_item(
                cart=cart,
                seller_product=seller_product,
                quantity=1,
            )

    def test_product_from_another_store_cannot_be_added(
        self,
        cart,
        active_product,
    ):
        other_owner = User.objects.create_user(
            phone="+201001234572",
            role="SELLER_OWNER",
        )

        other_store = Store.objects.create(
            owner=other_owner,
            name="Another Store",
            slug="another-store-service",
            phone="+201001234572",
            address="Suez",
            city="Suez",
            status=StoreStatus.ACTIVE,
            is_verified=True,
        )

        other_seller_product = SellerProduct.objects.create(
            store=other_store,
            product=active_product,
            price="300.00",
            is_active=True,
        )

        with pytest.raises(
            ValueError,
            match="same store as the cart",
        ):
            CartItemService.add_item(
                cart=cart,
                seller_product=other_seller_product,
                quantity=1,
            )

    def test_quantity_must_be_positive(
        self,
        cart,
        seller_product,
    ):
        with pytest.raises(
            ValueError,
            match="greater than zero",
        ):
            CartItemService.add_item(
                cart=cart,
                seller_product=seller_product,
                quantity=0,
            )

    def test_inactive_cart_cannot_be_modified(
        self,
        cart,
        seller_product,
    ):
        cart.status = CartStatus.CONVERTED
        cart.save(update_fields=["status"])

        with pytest.raises(
            ValueError,
            match="Only active carts",
        ):
            CartItemService.add_item(
                cart=cart,
                seller_product=seller_product,
                quantity=1,
            )


@pytest.mark.django_db
class TestUpdateCartItemQuantity:

    def test_updates_quantity(
        self,
        cart,
        seller_product,
    ):
        item, _ = CartItemService.add_item(
            cart=cart,
            seller_product=seller_product,
            quantity=2,
        )

        updated_item = CartItemService.update_quantity(
            cart=cart,
            item_id=item.id,
            quantity=5,
        )

        assert updated_item.id == item.id
        assert updated_item.quantity == 5
        assert updated_item.unit_price == Decimal("250.00")

    def test_quantity_must_be_positive(
        self,
        cart,
        seller_product,
    ):
        item, _ = CartItemService.add_item(
            cart=cart,
            seller_product=seller_product,
            quantity=2,
        )

        with pytest.raises(
            ValueError,
            match="greater than zero",
        ):
            CartItemService.update_quantity(
                cart=cart,
                item_id=item.id,
                quantity=0,
            )

    def test_item_must_belong_to_cart(
        self,
        customer,
        active_store,
        seller_product,
    ):
        from apps.cart.models import Cart

        another_cart = Cart.objects.create(
            customer=customer,
            store=active_store,
        )

        item, _ = CartItemService.add_item(
            cart=another_cart,
            seller_product=seller_product,
            quantity=2,
        )

        other_customer = User.objects.create_user(
            phone="+201001234573",
            role="CUSTOMER",
        )

        another_customer_cart = Cart.objects.create(
            customer=other_customer,
            store=active_store,
        )

        with pytest.raises(
            ValueError,
            match="Cart item not found",
        ):
            CartItemService.update_quantity(
                cart=another_customer_cart,
                item_id=item.id,
                quantity=5,
            )

    def test_cannot_update_inactive_cart(
        self,
        cart,
        seller_product,
    ):
        item, _ = CartItemService.add_item(
            cart=cart,
            seller_product=seller_product,
            quantity=2,
        )

        cart.status = CartStatus.CONVERTED
        cart.save(update_fields=["status"])

        with pytest.raises(
            ValueError,
            match="Only active carts",
        ):
            CartItemService.update_quantity(
                cart=cart,
                item_id=item.id,
                quantity=5,
            )

    def test_cannot_update_item_of_inactive_product(
        self,
        cart,
        seller_product,
    ):
        item, _ = CartItemService.add_item(
            cart=cart,
            seller_product=seller_product,
            quantity=2,
        )

        seller_product.is_active = False
        seller_product.save(update_fields=["is_active"])

        with pytest.raises(
            ValueError,
            match="Seller product must be active",
        ):
            CartItemService.update_quantity(
                cart=cart,
                item_id=item.id,
                quantity=5,
            )


@pytest.mark.django_db
class TestRemoveCartItem:

    def test_removes_item(
        self,
        cart,
        seller_product,
    ):
        item, _ = CartItemService.add_item(
            cart=cart,
            seller_product=seller_product,
            quantity=2,
        )

        result = CartItemService.remove_item(
            cart=cart,
            item_id=item.id,
        )

        assert result is True
        assert not CartItem.objects.filter(id=item.id).exists()

    def test_cannot_remove_item_from_inactive_cart(
        self,
        cart,
        seller_product,
    ):
        item, _ = CartItemService.add_item(
            cart=cart,
            seller_product=seller_product,
            quantity=2,
        )

        cart.status = CartStatus.CONVERTED
        cart.save(update_fields=["status"])

        with pytest.raises(
            ValueError,
            match="Only active carts",
        ):
            CartItemService.remove_item(
                cart=cart,
                item_id=item.id,
            )

    def test_cannot_remove_nonexistent_item(
        self,
        cart,
    ):
        import uuid

        with pytest.raises(
            ValueError,
            match="Cart item not found",
        ):
            CartItemService.remove_item(
                cart=cart,
                item_id=uuid.uuid4(),
            )

    def test_cannot_remove_item_from_another_cart(
        self,
        customer,
        active_store,
        seller_product,
    ):
        from apps.cart.models import Cart

        first_cart = Cart.objects.create(
            customer=customer,
            store=active_store,
        )

        item, _ = CartItemService.add_item(
            cart=first_cart,
            seller_product=seller_product,
            quantity=2,
        )

        other_customer = User.objects.create_user(
            phone="+201001234574",
            role="CUSTOMER",
        )

        second_cart = Cart.objects.create(
            customer=other_customer,
            store=active_store,
        )

        with pytest.raises(
            ValueError,
            match="Cart item not found",
        ):
            CartItemService.remove_item(
                cart=second_cart,
                item_id=item.id,
            )

        assert CartItem.objects.filter(id=item.id).exists()


@pytest.mark.django_db
class TestClearCart:

    def test_clears_all_cart_items(
        self,
        cart,
        seller_product,
    ):
        second_product = Product.objects.create(
            category=Category.objects.create(
                name="Brakes",
                slug="brakes-cart",
            ),
            name="Brake Pad",
            slug="brake-pad-cart",
            product_type="AFTERMARKET",
            is_active=True,
        )

        second_seller_product = SellerProduct.objects.create(
            store=cart.store,
            product=second_product,
            price="500.00",
            is_active=True,
        )

        CartItemService.add_item(
            cart=cart,
            seller_product=seller_product,
            quantity=2,
        )

        CartItemService.add_item(
            cart=cart,
            seller_product=second_seller_product,
            quantity=1,
        )

        assert CartItem.objects.filter(cart=cart).count() == 2

        deleted_count = CartItemService.clear_cart(cart=cart)

        assert deleted_count == 2
        assert not CartItem.objects.filter(cart=cart).exists()

    def test_clear_empty_cart_returns_zero(
        self,
        cart,
    ):
        deleted_count = CartItemService.clear_cart(
            cart=cart,
        )

        assert deleted_count == 0

    def test_cannot_clear_inactive_cart(
        self,
        cart,
        seller_product,
    ):
        CartItemService.add_item(
            cart=cart,
            seller_product=seller_product,
            quantity=2,
        )

        cart.status = CartStatus.CONVERTED
        cart.save(update_fields=["status"])

        with pytest.raises(
            ValueError,
            match="Only active carts",
        ):
            CartItemService.clear_cart(cart=cart)

        assert CartItem.objects.filter(cart=cart).count() == 1