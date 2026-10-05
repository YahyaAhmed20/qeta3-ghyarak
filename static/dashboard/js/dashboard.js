document.addEventListener("DOMContentLoaded", () => {
    const dashboardContent = document.getElementById("dashboard-content");

    if (!dashboardContent) {
        return;
    }

    loadDashboardOverview();
});


async function loadDashboardOverview() {
    const loading = document.getElementById("dashboard-loading");
    const content = document.getElementById("dashboard-content");
    const error = document.getElementById("dashboard-error");

    try {
        const response = await QETA3_API.get(
            "/api/v1/dashboard/overview/"
        );

        if (response.status === 401) {
            showDashboardError(
                "يجب تسجيل الدخول للوصول إلى لوحة تحكم المتجر."
            );
            return;
        }

        if (response.status === 403) {
            showDashboardError(
                "ليس لديك صلاحية للوصول إلى لوحة تحكم المتجر."
            );
            return;
        }

        if (!response.ok) {
            throw new Error(
                `Dashboard request failed: ${response.status}`
            );
        }

        const data = await response.json();

        renderDashboard(data);

        loading.classList.add("d-none");
        content.classList.remove("d-none");

    } catch (error) {
        console.error("Dashboard error:", error);

        showDashboardError(
            "حدث خطأ أثناء تحميل بيانات لوحة التحكم."
        );
    }
}

function renderDashboard(data) {

    const orders = data.orders || {};
    const sales = data.sales || {};
    const inventory = data.inventory || {};
    const settlements = data.settlements || {};
    const store = data.store || {};


    // Orders
    setText(
        "stat-total-orders",
        orders.total ?? 0
    );

    setText(
        "stat-today-orders",
        orders.today ?? 0
    );

    setText(
        "stat-pending-orders",
        orders.pending ?? 0
    );

    setText(
        "stat-delivered-orders",
        orders.delivered ?? 0
    );


    // Sales
    setText(
        "stat-today-sales",
        formatMoney(sales.today)
    );

    setText(
        "stat-total-sales",
        formatMoney(sales.total)
    );


    // Inventory
    setText(
        "stat-total-products",
        inventory.total_products ?? 0
    );

    setText(
        "stat-out-of-stock",
        inventory.out_of_stock ?? 0
    );


    // Settlements
    setText(
        "settlement-pending",
        formatMoney(settlements.pending)
    );

    setText(
        "settlement-ready",
        formatMoney(settlements.ready)
    );

    setText(
        "settlement-processing",
        formatMoney(settlements.processing)
    );

    setText(
        "settlement-paid",
        formatMoney(settlements.paid)
    );


    // Store
    setText(
        "store-name",
        store.name || "—"
    );

    setText(
        "store-status",
        translateStoreStatus(store.status)
    );

    setText(
        "store-verification",
        store.is_verified
            ? "موثّق"
            : "غير موثّق"
    );
}


function setText(elementId, value) {
    const element = document.getElementById(elementId);

    if (element) {
        element.textContent = value;
    }
}


function formatMoney(value) {
    const number = Number(value || 0);

    return number.toLocaleString("ar-EG", {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
    });
}


function translateStoreStatus(status) {

    const statuses = {
        PENDING: "قيد المراجعة",
        ACTIVE: "نشط",
        SUSPENDED: "موقوف",
        REJECTED: "مرفوض",
    };

    return statuses[status] || status || "—";
}


function showDashboardError(message) {

    const loading = document.getElementById("dashboard-loading");
    const error = document.getElementById("dashboard-error");
    const content = document.getElementById("dashboard-content");

    if (loading) {
        loading.classList.add("d-none");
    }

    if (content) {
        content.classList.add("d-none");
    }

    if (error) {
        error.textContent = message;
        error.classList.remove("d-none");
    }
}