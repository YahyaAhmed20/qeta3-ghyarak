document.addEventListener("DOMContentLoaded", async () => {
    const orderNumber = document.getElementById("order-number");
    const orderStatus = document.getElementById("order-status");
    const orderTotal = document.getElementById("order-total");
    const orderInfo = document.getElementById("order-info");
    const orderError = document.getElementById("order-error");
    const viewOrderBtn = document.getElementById("view-order-btn");

    const pathParts = window.location.pathname
        .split("/")
        .filter(Boolean);

    const orderId =
        pathParts[pathParts.length - 1];

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
        orderError.textContent = message;
        orderError.classList.remove("d-none");
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

    try {
        const token = getToken();

        if (!token) {
            window.location.href = "/login/";
            return;
        }

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
                "فشل تحميل بيانات الطلب."
            );
        }

        orderNumber.textContent =
            data.order_number;

        orderStatus.textContent =
            getStatusLabel(data.status);

        orderTotal.textContent =
            formatMoney(data.total);

        viewOrderBtn.href =
            `/orders/${data.id}/`;

        orderInfo.classList.remove("d-none");

    } catch (error) {
        console.error(
            "Order success error:",
            error
        );

        orderNumber.textContent =
            "تعذر تحميل الطلب";

        showError(error.message);
    }
});