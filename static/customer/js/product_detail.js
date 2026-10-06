document.addEventListener("DOMContentLoaded", async () => {
    const loading = document.getElementById("product-loading");
    const errorBox = document.getElementById("product-error");
    const content = document.getElementById("product-content");

    const productId = window.location.pathname
        .split("/")
        .filter(Boolean)
        .pop();

    try {
        const response = await fetch(
            `/api/v1/marketplace/products/${productId}/`
        );

        if (!response.ok) {
            throw new Error("Failed to load product.");
        }

        const product = await response.json();

        document.getElementById("product-category").textContent =
            product.category || "غير محدد";

        document.getElementById("product-name").textContent =
            product.name || "";

        document.getElementById("product-brand").textContent =
            product.brand
                ? `العلامة التجارية: ${product.brand}`
                : "العلامة التجارية غير محددة";

        document.getElementById("product-description").textContent =
            product.description || "لا يوجد وصف للمنتج.";

        document.getElementById("product-type").textContent =
            product.product_type || "غير محدد";

        document.getElementById("product-origin").textContent =
            product.country_of_origin || "غير محدد";

        document.getElementById("product-warranty").textContent =
            product.warranty || "غير محدد";

        document.getElementById("product-price").textContent =
            product.min_price
                ? `${product.min_price} جنيه`
                : "غير متاح";

        renderPartNumbers(product.part_numbers || []);
        renderCompatibilities(product.compatibilities || []);
        renderSellers(product.sellers || []);

        loading.classList.add("d-none");
        content.classList.remove("d-none");

    } catch (error) {
        console.error(error);

        loading.classList.add("d-none");
        errorBox.textContent =
            "حصل خطأ أثناء تحميل بيانات المنتج.";
        errorBox.classList.remove("d-none");
    }
});


function renderPartNumbers(partNumbers) {
    const container = document.getElementById("part-numbers");

    if (!partNumbers.length) {
        container.innerHTML = `
            <div class="empty-info">
                لا توجد أرقام قطعة مسجلة لهذا المنتج.
            </div>
        `;
        return;
    }

    container.innerHTML = partNumbers.map(number => `
        <div class="border rounded p-3 mb-2">
            <strong>${number.part_number}</strong>
            <div class="small text-muted">
                ${number.number_type || ""}
            </div>
        </div>
    `).join("");
}


function renderCompatibilities(compatibilities) {
    const container = document.getElementById("compatibilities");

    if (!compatibilities.length) {
        container.innerHTML = `
            <div class="empty-info">
                لا توجد سيارات متوافقة مسجلة لهذا المنتج حاليًا.
            </div>
        `;
        return;
    }

    container.innerHTML = compatibilities.map(vehicle => `
        <div class="border rounded p-3 mb-2">
            <strong>
                ${vehicle.make} ${vehicle.model}
            </strong>

            <div class="small text-muted">
                ${vehicle.generation || ""}
                ${vehicle.engine ? ` - ${vehicle.engine}` : ""}
            </div>

            <div class="small text-muted">
                ${vehicle.variant || ""}
            </div>

            ${
                vehicle.notes
                    ? `<div class="small mt-2">${vehicle.notes}</div>`
                    : ""
            }
        </div>
    `).join("");
}


function renderSellers(sellers) {
    const container = document.getElementById("sellers");

    if (!sellers.length) {
        container.innerHTML = `
            <div class="empty-info">
                لا توجد عروض متاحة حاليًا.
            </div>
        `;
        return;
    }

    container.innerHTML = sellers.map(seller => {
        const finalPrice =
            seller.sale_price || seller.price;

        return `
            <div class="seller-card">

                <div class="fw-bold mb-1">
                    ${seller.store_name}
                </div>

                <div class="small text-muted mb-3">
                    ${seller.city || ""}
                </div>

                <div class="seller-price mb-2">
                    ${finalPrice} جنيه
                </div>

                ${
                    seller.sale_price
                        ? `
                            <div class="small text-muted text-decoration-line-through">
                                ${seller.price} جنيه
                            </div>
                        `
                        : ""
                }

                <div class="small mb-3">
                    ${
                        seller.available > 0
                            ? `متوفر: ${seller.available}`
                            : "غير متوفر"
                    }
                </div>

                <button
                    type="button"
                    class="btn btn-dark w-100 add-to-cart-btn"
                    data-seller-product-id="${seller.seller_product_id}"
                    ${seller.available <= 0 ? "disabled" : ""}
                >
                    إضافة للسلة
                </button>

            </div>
        `;
    }).join("");
}


function showCartModal(productName) {
    const modal = document.getElementById("cart-success-modal");
    const productElement = document.getElementById(
        "cart-success-product"
    );
    const continueButton = document.getElementById(
        "continue-shopping-modal-btn"
    );

    if (!modal || !productElement || !continueButton) {
        return;
    }

    productElement.textContent = productName;

    modal.classList.add("show");
    modal.setAttribute("aria-hidden", "false");

    continueButton.onclick = () => {
    window.location.href = "/";
};
}


document.addEventListener("click", async (event) => {
    const button = event.target.closest(".add-to-cart-btn");

    if (!button) {
        return;
    }

    const sellerProductId = button.dataset.sellerProductId;

    button.disabled = true;
    button.textContent = "جاري الإضافة...";

    try {
        let customerToken = localStorage.getItem(
            "qeta3_customer_access_token"
        );

        if (!customerToken) {
            window.location.href = "/login/";
            return;
        }

        async function addToCart(token) {
            return fetch("/api/v1/cart/items/", {
                method: "POST",
                headers: {
                    "Authorization": `Bearer ${token}`,
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    seller_product_id: sellerProductId,
                    quantity: 1,
                }),
            });
        }

        let response = await addToCart(customerToken);

        // Access token expired → try refresh
        if (response.status === 401) {
            console.log("🔄 Access token expired - starting refresh...");

            const refreshToken = localStorage.getItem(
                "qeta3_customer_refresh_token"
            );

            console.log("🔑 Refresh token exists:", !!refreshToken);

            if (!refreshToken) {
                localStorage.removeItem("qeta3_customer_access_token");
                window.location.href = "/login/";
                return;
            }

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

            if (!refreshResponse.ok) {
                localStorage.removeItem("qeta3_customer_access_token");
                localStorage.removeItem("qeta3_customer_refresh_token");

                window.location.href = "/login/";
                return;
            }

            const refreshData = await refreshResponse.json();

            customerToken = refreshData.access;

            localStorage.setItem(
                "qeta3_customer_access_token",
                customerToken
            );

            if (refreshData.refresh) {
                localStorage.setItem(
                    "qeta3_customer_refresh_token",
                    refreshData.refresh
                );
            }

            // Retry add to cart with new token
            response = await addToCart(customerToken);
        }

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                data.detail || "فشل إضافة المنتج للسلة."
            );
        }

        button.textContent = "تمت الإضافة ✓";

        const productName =
            document.getElementById("product-name")?.textContent ||
            "المنتج";

        showCartModal(productName);

    } catch (error) {
        console.error(error);

        button.disabled = false;
        button.textContent = "إضافة للسلة";

        alert(error.message);
    }
});