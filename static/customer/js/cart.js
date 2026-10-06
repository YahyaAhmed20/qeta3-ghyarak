document.addEventListener("DOMContentLoaded", async () => {
    const loading = document.getElementById("cart-loading");
    const errorBox = document.getElementById("cart-error");
    const empty = document.getElementById("cart-empty");
    const content = document.getElementById("cart-content");

    const itemsContainer = document.getElementById("cart-items");
    const itemsCount = document.getElementById("cart-items-count");
    const subtotal = document.getElementById("cart-subtotal");
    const clearCartBtn = document.getElementById("clear-cart-btn");

    function getToken() {
        return localStorage.getItem(
            "qeta3_customer_access_token"
        );
    }

    function formatMoney(value) {
        return Number(value || 0).toLocaleString("ar-EG", {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
        }) + " ج.م";
    }

    function showError(message) {
        errorBox.textContent = message;
        errorBox.classList.remove("d-none");
    }

    async function apiRequest(url, options = {}) {
        const token = getToken();

        if (!token) {
            window.location.href = "/login/";
            return null;
        }

        const response = await fetch(url, {
            ...options,
            headers: {
                "Authorization": `Bearer ${token}`,
                "Content-Type": "application/json",
                ...(options.headers || {}),
            },
        });

        if (response.status === 401) {
            localStorage.removeItem(
                "qeta3_customer_access_token"
            );

            localStorage.removeItem(
                "qeta3_customer_refresh_token"
            );

            window.location.href = "/login/";
            return null;
        }

        return response;
    }

    async function loadCart() {
        loading.classList.remove("d-none");
        errorBox.classList.add("d-none");
        content.classList.add("d-none");
        empty.classList.add("d-none");

        try {
            const response = await apiRequest(
                "/api/v1/cart/",
                {
                    method: "GET",
                }
            );

            if (!response) {
                return;
            }

            const data = await response.json();

            if (!response.ok) {
                throw new Error(
                    data.detail || "فشل تحميل السلة."
                );
            }

            loading.classList.add("d-none");

            if (
                !data.cart ||
                !data.cart.items ||
                data.cart.items.length === 0
            ) {
                empty.classList.remove("d-none");
                return;
            }

            const cart = data.cart;

            itemsCount.textContent = cart.items_count;
            subtotal.textContent = formatMoney(cart.subtotal);

            itemsContainer.innerHTML = cart.items.map(item => `
                <div
                    class="cart-item"
                    data-item-id="${item.id}"
                >

                    <div class="d-flex justify-content-between align-items-start gap-3">

                        <div>
                            <div class="product-name mb-2">
                                ${item.product_name}
                            </div>

                            <div class="text-muted small">
                                سعر الوحدة:
                                ${formatMoney(item.unit_price)}
                            </div>
                        </div>

                        <strong>
                            ${formatMoney(item.subtotal)}
                        </strong>

                    </div>

                    <div class="d-flex align-items-center justify-content-between mt-3">

                        <div class="d-flex align-items-center gap-2">

                            <button
                                type="button"
                                class="btn btn-outline-dark btn-sm quantity-minus"
                                data-item-id="${item.id}"
                                data-quantity="${item.quantity}"
                            >
                                −
                            </button>

                            <span class="fw-bold px-2">
                                ${item.quantity}
                            </span>

                            <button
                                type="button"
                                class="btn btn-outline-dark btn-sm quantity-plus"
                                data-item-id="${item.id}"
                                data-quantity="${item.quantity}"
                            >
                                +
                            </button>

                        </div>

                        <button
                            type="button"
                            class="btn btn-outline-danger btn-sm remove-cart-item"
                            data-item-id="${item.id}"
                        >
                            حذف
                        </button>

                    </div>

                </div>
            `).join("");

            content.classList.remove("d-none");

        } catch (error) {
            console.error("Cart error:", error);

            loading.classList.add("d-none");
            showError(error.message);
        }
    }

    async function updateQuantity(itemId, quantity) {
        if (quantity < 1) {
            await removeItem(itemId);
            return;
        }

        try {
            const response = await apiRequest(
                `/api/v1/cart/items/${itemId}/`,
                {
                    method: "PATCH",
                    body: JSON.stringify({
                        quantity: quantity,
                    }),
                }
            );

            if (!response) {
                return;
            }

            const data = await response.json();

            if (!response.ok) {
                throw new Error(
                    data.detail || "فشل تعديل الكمية."
                );
            }

            await loadCart();

        } catch (error) {
            console.error(error);
            showError(error.message);
        }
    }

    async function removeItem(itemId) {
        try {
            const response = await apiRequest(
                `/api/v1/cart/items/${itemId}/`,
                {
                    method: "DELETE",
                }
            );

            if (!response) {
                return;
            }

            if (!response.ok && response.status !== 204) {
                const data = await response.json();

                throw new Error(
                    data.detail || "فشل حذف المنتج."
                );
            }

            await loadCart();

        } catch (error) {
            console.error(error);
            showError(error.message);
        }
    }

    itemsContainer.addEventListener("click", async (event) => {

        const plusButton =
            event.target.closest(".quantity-plus");

        const minusButton =
            event.target.closest(".quantity-minus");

        const removeButton =
            event.target.closest(".remove-cart-item");

        if (plusButton) {
            const itemId = plusButton.dataset.itemId;
            const quantity = Number(
                plusButton.dataset.quantity
            );

            await updateQuantity(
                itemId,
                quantity + 1
            );

            return;
        }

        if (minusButton) {
            const itemId = minusButton.dataset.itemId;
            const quantity = Number(
                minusButton.dataset.quantity
            );

            await updateQuantity(
                itemId,
                quantity - 1
            );

            return;
        }

        if (removeButton) {
            const itemId = removeButton.dataset.itemId;

            await removeItem(itemId);
        }
    });

    clearCartBtn.addEventListener("click", async () => {

        try {
            const response = await apiRequest(
                "/api/v1/cart/clear/",
                {
                    method: "DELETE",
                }
            );

            if (!response) {
                return;
            }

            const data =
                response.status === 204
                    ? {}
                    : await response.json();

            if (!response.ok) {
                throw new Error(
                    data.detail || "فشل تفريغ السلة."
                );
            }

            await loadCart();

        } catch (error) {
            console.error(error);
            showError(error.message);
        }
    });

    await loadCart();
});