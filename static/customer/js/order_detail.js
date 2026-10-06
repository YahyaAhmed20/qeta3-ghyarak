document.addEventListener("DOMContentLoaded", async () => {
    const loading = document.getElementById("order-loading");
    const errorBox = document.getElementById("order-error");
    const content = document.getElementById("order-content");

    const orderNumber = document.getElementById("order-number");
    const orderStatus = document.getElementById("order-status");

    const orderTracking = document.getElementById(
        "order-tracking"
    );

    const orderItems = document.getElementById(
        "order-items"
    );

    const orderAddress = document.getElementById(
        "order-address"
    );

    const orderSubtotal = document.getElementById(
        "order-subtotal"
    );

    const sellerDiscount = document.getElementById(
        "seller-discount"
    );

    const platformDiscount = document.getElementById(
        "platform-discount"
    );

    const deliveryFee = document.getElementById(
        "delivery-fee"
    );

    const orderTotal = document.getElementById(
        "order-total"
    );

    function getToken() {
        return localStorage.getItem(
            "qeta3_customer_access_token"
        );
    }

    function formatMoney(value) {
        return (
            Number(value || 0).toLocaleString("ar-EG", {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2,
            }) + " ج.م"
        );
    }

    function showError(message) {
        errorBox.textContent = message;
        errorBox.classList.remove("d-none");
    }

    function getOrderId() {
        const parts = window.location.pathname
            .split("/")
            .filter(Boolean);

        return parts[parts.length - 1];
    }

    function getStatusLabel(status) {
        const labels = {
            CREATED: "تم استلام الطلب",
            ACCEPTED: "تم قبول الطلب",
            PREPARING: "جاري تجهيز الطلب",
            READY: "الطلب جاهز",
            OUT_FOR_DELIVERY: "جاري التوصيل",
            DELIVERED: "تم التسليم",
            FAILED_DELIVERY: "تعذر التسليم",
            CANCELLED: "تم إلغاء الطلب",
            REJECTED: "تم رفض الطلب",
            RETURNED: "تم إرجاع الطلب",
            REFUNDED: "تم استرداد المبلغ",
        };

        return labels[status] || status;
    }

    function getTrackingSteps(status) {
        const steps = [
            {
                key: "CREATED",
                label: "تم الطلب",
            },
            {
                key: "ACCEPTED",
                label: "تم القبول",
            },
            {
                key: "PREPARING",
                label: "التجهيز",
            },
            {
                key: "READY",
                label: "جاهز",
            },
            {
                key: "OUT_FOR_DELIVERY",
                label: "التوصيل",
            },
            {
                key: "DELIVERED",
                label: "تم التسليم",
            },
        ];

        const normalFlow = [
            "CREATED",
            "ACCEPTED",
            "PREPARING",
            "READY",
            "OUT_FOR_DELIVERY",
            "DELIVERED",
        ];

        const currentIndex =
            normalFlow.indexOf(status);

        return steps.map((step, index) => {
            const active =
                currentIndex >= 0 &&
                index <= currentIndex;

            return `
                <div class="tracking-step ${
                    active ? "active" : ""
                }">

                    <div class="tracking-dot">
                        ${active ? "✓" : index + 1}
                    </div>

                    <div class="tracking-label">
                        ${step.label}
                    </div>

                </div>
            `;
        }).join("");
    }

    function renderItems(items) {
        if (!items || items.length === 0) {
            orderItems.innerHTML = `
                <div class="text-muted">
                    لا توجد منتجات في الطلب.
                </div>
            `;

            return;
        }

        orderItems.innerHTML = items.map(item => `
            <div class="order-item">

                <div class="d-flex justify-content-between gap-3">

                    <div>

                        <div class="fw-bold mb-1">
                            ${item.product_name}
                        </div>

                        ${
                            item.part_number
                                ? `
                                    <div class="text-muted small mb-1">
                                        رقم القطعة:
                                        ${item.part_number}
                                    </div>
                                `
                                : ""
                        }

                        <div class="text-muted small">
                            الكمية:
                            ${item.quantity}
                        </div>

                    </div>

                    <div class="text-end">

                        <div class="text-muted small">
                            ${formatMoney(item.unit_price)}
                        </div>

                        <strong>
                            ${formatMoney(item.subtotal)}
                        </strong>

                    </div>

                </div>

            </div>
        `).join("");
    }

    function renderAddress(address) {
        if (!address) {
            orderAddress.innerHTML = `
                <div class="text-muted">
                    لا توجد بيانات عنوان.
                </div>
            `;

            return;
        }

        orderAddress.innerHTML = `
            <div class="fw-bold mb-2">
                ${address.label || ""}
            </div>

            <div class="mb-1">
                ${address.recipient_name || ""}
            </div>

            <div class="text-muted small mb-1">
                ${address.phone || ""}
            </div>

            <div class="text-muted small">
                ${address.city || ""}
                ${
                    address.area
                        ? `، ${address.area}`
                        : ""
                }
                ${
                    address.address_line
                        ? `، ${address.address_line}`
                        : ""
                }
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
        `;
    }

    try {
        const token = getToken();

        if (!token) {
            window.location.href = "/login/";
            return;
        }

        const orderId = getOrderId();

        const response = await fetch(
            `/api/v1/orders/${orderId}/`,
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
                "فشل تحميل تفاصيل الطلب."
            );
        }

        orderNumber.textContent =
            data.order_number;

        orderStatus.textContent =
            getStatusLabel(data.status);

        orderTracking.innerHTML =
            getTrackingSteps(data.status);

        renderItems(data.items);

        renderAddress(
            data.address_snapshot
        );

        orderSubtotal.textContent =
            formatMoney(data.subtotal);

        sellerDiscount.textContent =
            formatMoney(data.seller_discount);

        platformDiscount.textContent =
            formatMoney(data.platform_discount);

        deliveryFee.textContent =
            formatMoney(data.delivery_fee);

        orderTotal.textContent =
            formatMoney(data.total);

        loading.classList.add("d-none");
        content.classList.remove("d-none");

    } catch (error) {
        console.error(
            "Order detail error:",
            error
        );

        loading.classList.add("d-none");
        showError(error.message);
    }
});