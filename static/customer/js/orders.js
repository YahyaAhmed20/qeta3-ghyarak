document.addEventListener("DOMContentLoaded", async () => {
    const loading = document.getElementById("orders-loading");
    const errorBox = document.getElementById("orders-error");
    const empty = document.getElementById("orders-empty");
    const content = document.getElementById("orders-content");
    const ordersList = document.getElementById("orders-list");

    const accessToken = localStorage.getItem("qeta3_customer_access_token");

    if (!accessToken) {
        window.location.href = "/login/";
        return;
    }

    function formatMoney(value) {
        return Number(value || 0).toLocaleString("ar-EG", {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
        }) + " ج.م";
    }

    function getStatusLabel(status) {
        const labels = {
            CREATED: "تم استلام الطلب",
            ACCEPTED: "تم قبول الطلب",
            PREPARING: "جاري التجهيز",
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

    function getStatusClass(status) {
        if (status === "DELIVERED") {
            return "bg-success";
        }

        if (
            status === "CANCELLED" ||
            status === "REJECTED" ||
            status === "FAILED_DELIVERY"
        ) {
            return "bg-danger";
        }

        if (status === "OUT_FOR_DELIVERY") {
            return "bg-primary";
        }

        return "bg-warning text-dark";
    }

    function renderOrder(order) {
        const card = document.createElement("div");
        card.className = "col-12";

        card.innerHTML = `
            <div class="card border-0 shadow-sm">
                <div class="card-body">

                    <div class="d-flex justify-content-between align-items-start gap-3">

                        <div>
                            <div class="text-muted small mb-1">
                                رقم الطلب
                            </div>

                            <h5 class="fw-bold mb-2">
                                ${order.order_number}
                            </h5>

                            <span class="badge ${getStatusClass(order.status)}">
                                ${getStatusLabel(order.status)}
                            </span>
                        </div>

                        <div class="text-end">
                            <div class="text-muted small mb-1">
                                الإجمالي
                            </div>

                            <div class="fw-bold fs-5">
                                ${formatMoney(order.total)}
                            </div>
                        </div>

                    </div>

                    <hr>

                    <div class="d-flex justify-content-between align-items-center">

                        <div class="text-muted small">
                            ${new Date(order.created_at).toLocaleDateString("ar-EG")}
                        </div>

                        <a
                            href="/orders/${order.id}/"
                            class="btn btn-dark btn-sm"
                        >
                            عرض الطلب
                        </a>

                    </div>

                </div>
            </div>
        `;

        ordersList.appendChild(card);
    }

    try {
        const response = await fetch("/api/v1/orders/", {
            method: "GET",
            headers: {
                "Authorization": `Bearer ${accessToken}`,
                "Content-Type": "application/json",
            },
        });

        if (response.status === 401) {
            localStorage.removeItem("qeta3_customer_access_token");
            localStorage.removeItem("qeta3_customer_refresh_token");

            window.location.href = "/login/";
            return;
        }

        if (!response.ok) {
            throw new Error("فشل تحميل الطلبات");
        }

        const data = await response.json();

        loading.classList.add("d-none");

        const orders = data.results || [];

        if (orders.length === 0) {
            empty.classList.remove("d-none");
            return;
        }

        orders.forEach(renderOrder);

        content.classList.remove("d-none");

    } catch (error) {
        console.error(error);

        loading.classList.add("d-none");

        errorBox.textContent =
            "حدث خطأ أثناء تحميل الطلبات. حاول مرة أخرى.";

        errorBox.classList.remove("d-none");
    }
});