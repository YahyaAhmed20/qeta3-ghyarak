document.addEventListener("DOMContentLoaded", async () => {
    const addressesLoading = document.getElementById(
        "addresses-loading"
    );

    const addressesContainer = document.getElementById(
        "addresses-container"
    );

    const selectedAddressContainer = document.getElementById(
        "selected-address-container"
    );

    const changeAddressBtn = document.getElementById(
        "change-address-btn"
    );

    const addAddressBtn = document.getElementById(
        "add-address-btn"
    );

    if (addAddressBtn) {
        addAddressBtn.classList.remove("d-none");
    }

    const addAddressModalElement = document.getElementById(
        "add-address-modal"
    );

    const addAddressModal = addAddressModalElement
        ? new bootstrap.Modal(addAddressModalElement)
        : null;

    const addressesEmpty = document.getElementById(
        "addresses-empty"
    );

    const errorBox = document.getElementById(
        "checkout-error"
    );

    const cartLoading = document.getElementById(
        "checkout-cart-loading"
    );

    const cartContent = document.getElementById(
        "checkout-cart-content"
    );

    const cartItemsContainer = document.getElementById(
        "checkout-cart-items"
    );

    const itemsCount = document.getElementById(
        "checkout-items-count"
    );

    const subtotal = document.getElementById(
        "checkout-subtotal"
    );

    const total = document.getElementById(
        "checkout-total"
    );

    changeAddressBtn.addEventListener("click", () => {
        addressesContainer.classList.toggle("d-none");

        if (addressesContainer.classList.contains("d-none")) {
            changeAddressBtn.textContent = "تغيير العنوان";
        } else {
            changeAddressBtn.textContent = "إخفاء العناوين";
        }
    });

    if (addAddressBtn && addAddressModal) {
        addAddressBtn.addEventListener("click", () => {
            addAddressModal.show();
        });
    }

    function getToken() {
        return localStorage.getItem(
            "qeta3_customer_access_token"
        );
    }

    async function apiRequest(url, options = {}) {
        let accessToken = getToken();

        if (!accessToken) {
            window.location.href = "/login/";
            return null;
        }

        async function sendRequest(token) {
            return fetch(url, {
                ...options,
                headers: {
                    "Authorization": `Bearer ${token}`,
                    "Content-Type": "application/json",
                    ...(options.headers || {}),
                },
            });
        }

        let response = await sendRequest(accessToken);

        if (response.status !== 401) {
            return response;
        }

        const refreshToken = localStorage.getItem(
            "qeta3_customer_refresh_token"
        );

        if (!refreshToken) {
            localStorage.removeItem(
                "qeta3_customer_access_token"
            );

            localStorage.removeItem(
                "qeta3_customer_refresh_token"
            );

            window.location.href = "/login/";
            return null;
        }

        try {
            const refreshResponse = await fetch(
                "/api/v1/auth/token/refresh/",
                {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify({
                        refresh: refreshToken,
                    }),
                }
            );

            const refreshData = await refreshResponse.json();

            if (!refreshResponse.ok || !refreshData.access) {
                throw new Error("Refresh token expired.");
            }

            localStorage.setItem(
                "qeta3_customer_access_token",
                refreshData.access
            );

            if (refreshData.refresh) {
                localStorage.setItem(
                    "qeta3_customer_refresh_token",
                    refreshData.refresh
                );
            }

            return await sendRequest(refreshData.access);

        } catch (error) {
            localStorage.removeItem(
                "qeta3_customer_access_token"
            );

            localStorage.removeItem(
                "qeta3_customer_refresh_token"
            );

            window.location.href = "/login/";
            return null;
        }
    }

    function showError(message) {
        errorBox.textContent = message;
        errorBox.classList.remove("d-none");
    }

    function formatMoney(value) {
        return (
            Number(value || 0).toLocaleString("ar-EG", {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2,
            }) + " ج.م"
        );
    }

    function renderAddress(address, selected = false) {
        return `
            <div
                class="address-card ${selected ? "selected" : ""}"
                data-address-id="${address.id}"
            >
                <div class="d-flex align-items-start gap-3">

                    <input
                        type="radio"
                        name="checkout-address"
                        class="address-radio mt-1"
                        value="${address.id}"
                        ${selected ? "checked" : ""}
                    >

                    <div class="flex-grow-1">

                        <div class="d-flex justify-content-between align-items-center mb-2">
                            <div class="d-flex align-items-center gap-2">
                                <strong>
                                    ${address.label}
                                </strong>

                                ${
                                    address.is_default
                                        ? `
                                            <span class="badge bg-dark">
                                                الافتراضي
                                            </span>
                                        `
                                        : ""
                                }
                            </div>

                            <button
                                type="button"
                                class="btn btn-sm btn-outline-danger delete-address-btn"
                                data-address-id="${address.id}"
                            >
                                حذف
                            </button>
                        </div>

                        <div class="fw-semibold mb-1">
                            ${address.recipient_name}
                        </div>

                        <div class="text-muted small mb-1">
                            ${address.phone}
                        </div>

                        <div class="text-muted small">
                            ${address.city}،
                            ${address.area}،
                            ${address.address_line}
                        </div>

                        ${
                            address.building ||
                            address.floor ||
                            address.apartment
                                ? `
                                    <div class="text-muted small mt-1">
                                        ${
                                            address.building
                                                ? `مبنى ${address.building}`
                                                : ""
                                        }
                                        ${
                                            address.floor
                                                ? ` - الدور ${address.floor}`
                                                : ""
                                        }
                                        ${
                                            address.apartment
                                                ? ` - شقة ${address.apartment}`
                                                : ""
                                        }
                                    </div>
                                `
                                : ""
                        }

                        ${
                            address.landmark
                                ? `
                                    <div class="text-muted small mt-1">
                                        علامة مميزة:
                                        ${address.landmark}
                                    </div>
                                `
                                : ""
                        }

                    </div>

                </div>
            </div>
        `;
    }

    async function loadAddresses() {
        try {
            const token = getToken();

            if (!token) {
                window.location.href = "/login/";
                return;
            }

            const response = await fetch(
                "/api/addresses/",
                {
                    method: "GET",
                    headers: {
                        "Authorization": `Bearer ${token}`,
                        "Content-Type": "application/json",
                    },
                }
            );

            const data = await response.json();

            if (response.status === 401) {
                localStorage.removeItem(
                    "qeta3_customer_access_token"
                );

                localStorage.removeItem(
                    "qeta3_customer_refresh_token"
                );

                window.location.href = "/login/";
                return;
            }

            if (!response.ok) {
                throw new Error(
                    data.detail ||
                    "فشل تحميل العناوين."
                );
            }

            addressesLoading.classList.add("d-none");

            if (!data || data.length === 0) {
                addressesEmpty.classList.remove("d-none");
                return;
            }

            const defaultAddress =
                data.find(address => address.is_default) ||
                data[0];

            selectedAddressContainer.innerHTML = renderAddress(
                defaultAddress,
                true
            );

            addressesContainer.innerHTML = data
                .filter(address => address.id !== defaultAddress.id)
                .map(address => renderAddress(address, false))
                .join("");

            addressesContainer
                .querySelectorAll(".address-card")
                .forEach(card => {
                    card.addEventListener(
                        "click",
                        () => {

                            addressesContainer
                                .querySelectorAll(
                                    ".address-card"
                                )
                                .forEach(item => {
                                    item.classList.remove(
                                        "selected"
                                    );
                                });

                            addressesContainer
                                .querySelectorAll(
                                    'input[name="checkout-address"]'
                                )
                                .forEach(radio => {
                                    radio.checked = false;
                                });

                            card.classList.add(
                                "selected"
                            );

                            const radio =
                                card.querySelector(
                                    ".address-radio"
                                );

                            radio.checked = true;
                        }
                    );
                });

            // حذف العنوان
            addressesContainer
                .querySelectorAll(".delete-address-btn")
                .forEach(button => {
                    button.addEventListener("click", async (event) => {
                        event.stopPropagation();

                        const addressId = button.dataset.addressId;

                        const confirmed = confirm(
                            "هل أنت متأكد أنك تريد حذف هذا العنوان؟"
                        );

                        if (!confirmed) {
                            return;
                        }

                        button.disabled = true;
                        button.textContent = "جاري الحذف...";

                        try {
                            const response = await apiRequest(
                                `/api/addresses/${addressId}/`,
                                {
                                    method: "DELETE",
                                }
                            );

                            if (!response) {
                                return;
                            }

                            if (!response.ok) {
                                const data = await response.json().catch(() => ({}));

                                throw new Error(
                                    data.detail || "فشل حذف العنوان."
                                );
                            }

                            await loadAddresses();

                        } catch (error) {
                            console.error("Delete address error:", error);
                            showError(error.message);

                            button.disabled = false;
                            button.textContent = "حذف";
                        }
                    });
                });

        } catch (error) {
            console.error(
                "Checkout addresses error:",
                error
            );

            addressesLoading.classList.add("d-none");

            showError(error.message);
        }
    }

    async function loadCart() {
        try {
            const token = getToken();

            if (!token) {
                window.location.href = "/login/";
                return;
            }

            const response = await fetch(
                "/api/v1/cart/",
                {
                    method: "GET",
                    headers: {
                        "Authorization": `Bearer ${token}`,
                        "Content-Type": "application/json",
                    },
                }
            );

            const data = await response.json();

            if (response.status === 401) {
                localStorage.removeItem(
                    "qeta3_customer_access_token"
                );

                localStorage.removeItem(
                    "qeta3_customer_refresh_token"
                );

                window.location.href = "/login/";
                return;
            }

            if (!response.ok) {
                throw new Error(
                    data.detail ||
                    "فشل تحميل السلة."
                );
            }

            cartLoading.classList.add("d-none");

            if (
                !data.cart ||
                !data.cart.items ||
                data.cart.items.length === 0
            ) {
                throw new Error(
                    "السلة فارغة."
                );
            }

            const cart = data.cart;

            itemsCount.textContent = cart.items_count;

            subtotal.textContent =
                formatMoney(cart.subtotal);

            total.textContent =
                formatMoney(cart.subtotal);

            cartItemsContainer.innerHTML =
                cart.items.map(item => `
                    <div class="mb-3">

                        <div class="d-flex justify-content-between gap-3">

                            <div>
                                <div class="fw-bold">
                                    ${item.product_name}
                                </div>

                                <div class="text-muted small">
                                    الكمية:
                                    ${item.quantity}
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

                    </div>
                `).join("");

            cartContent.classList.remove("d-none");

        } catch (error) {
            console.error(
                "Checkout cart error:",
                error
            );

            cartLoading.classList.add("d-none");

            showError(error.message);
        }
    }

    const confirmOrderBtn = document.getElementById(
        "confirm-order-btn"
    );

    const saveAddressBtn = document.getElementById("save-address-btn");
    const addAddressError = document.getElementById("add-address-error");

    if (saveAddressBtn) {
        saveAddressBtn.addEventListener("click", async () => {
            addAddressError.classList.add("d-none");

            const payload = {
                label: document.getElementById("address-label").value.trim(),
                recipient_name: document.getElementById("address-recipient-name").value.trim(),
                phone: document.getElementById("address-phone").value.trim(),
                city: document.getElementById("address-city").value.trim(),
                area: document.getElementById("address-area").value.trim(),
                address_line: document.getElementById("address-line").value.trim(),
                building: document.getElementById("address-building").value.trim(),
                floor: document.getElementById("address-floor").value.trim(),
                apartment: document.getElementById("address-apartment").value.trim(),
                landmark: document.getElementById("address-landmark").value.trim(),
                is_default: document.getElementById("address-is-default").checked,
            };

            const requiredFields = [
                ["label", "اسم العنوان"],
                ["recipient_name", "اسم المستلم"],
                ["phone", "رقم الهاتف"],
                ["city", "المحافظة / المدينة"],
                ["area", "المنطقة"],
                ["address_line", "العنوان بالتفصيل"],
            ];

            for (const [field, label] of requiredFields) {
                if (!payload[field]) {
                    addAddressError.textContent = `من فضلك أدخل ${label}.`;
                    addAddressError.classList.remove("d-none");
                    return;
                }
            }

            saveAddressBtn.disabled = true;
            saveAddressBtn.textContent = "جاري الحفظ...";

            try {
                const response = await apiRequest("/api/addresses/", {
                    method: "POST",
                    body: JSON.stringify(payload),
                });

                if (!response) {
                    return;
                }

                const data = await response.json();

                if (!response.ok) {
                    throw new Error(
                        data.detail ||
                        "فشل إنشاء العنوان."
                    );
                }

                console.log("ADDRESS CREATED:", data);

                // إعادة تحميل العناوين واختيار العنوان الجديد
                await loadAddresses();

                const newAddressRadio = document.querySelector(
                    `input[name="checkout-address"][value="${data.id}"]`
                );

                if (newAddressRadio) {
                    newAddressRadio.checked = true;

                    const newAddressCard = newAddressRadio.closest(".address-card");

                    if (newAddressCard) {
                        document
                            .querySelectorAll(".address-card")
                            .forEach(card => {
                                card.classList.remove("selected");
                            });

                        newAddressCard.classList.add("selected");
                    }
                }

                // إغلاق الـ Modal
                if (addAddressModal) {
                    addAddressModal.hide();
                }

                // إعادة الزر لحالته الطبيعية
                saveAddressBtn.disabled = false;
                saveAddressBtn.textContent = "حفظ العنوان";

            } catch (error) {
                console.error("Create address error:", error);

                addAddressError.textContent = error.message;
                addAddressError.classList.remove("d-none");

                saveAddressBtn.disabled = false;
                saveAddressBtn.textContent = "حفظ العنوان";
            }
        });
    }

    confirmOrderBtn.addEventListener("click", async () => {
        const selectedAddress =
            document.querySelector(
                'input[name="checkout-address"]:checked'
            );

        if (!selectedAddress) {
            showError("من فضلك اختر عنوان التوصيل.");
            return;
        }

        const notes =
            document.getElementById(
                "checkout-notes"
            ).value.trim();

        confirmOrderBtn.disabled = true;
        confirmOrderBtn.textContent =
            "جاري تنفيذ الطلب...";

        try {
            const token = getToken();

            const response = await fetch(
                "/api/v1/orders/checkout/",
                {
                    method: "POST",
                    headers: {
                        "Authorization": `Bearer ${token}`,
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify({
                        address_id:
                            selectedAddress.value,
                        notes: notes,
                    }),
                }
            );

            const data = await response.json();

            console.log(
                "CHECKOUT STATUS:",
                response.status
            );

            console.log(
                "CHECKOUT DATA:",
                data
            );

            if (!response.ok) {
                throw new Error(
                    data.detail ||
                    "فشل تنفيذ الطلب."
                );
            }

           window.location.href = `/orders/success/${data.id}/`;

        } catch (error) {
            console.error(
                "Checkout error:",
                error
            );

            showError(error.message);

            confirmOrderBtn.disabled = false;
            confirmOrderBtn.textContent =
                "تأكيد الطلب";
        }
    });

    await Promise.all([
        loadAddresses(),
        loadCart(),
    ]);
});