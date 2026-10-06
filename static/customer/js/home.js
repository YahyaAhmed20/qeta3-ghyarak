document.addEventListener("DOMContentLoaded", () => {
    const searchInput = document.querySelector("#marketplace-search");
    const searchButton = document.querySelector("#marketplace-search-btn");
    const productsContainer = document.querySelector("#marketplace-products");
    const loading = document.querySelector("#marketplace-loading");
    const emptyState = document.querySelector("#marketplace-empty");

    async function searchProducts() {
        const search = searchInput.value.trim();

        loading.classList.remove("d-none");
        emptyState.classList.add("d-none");
        productsContainer.innerHTML = "";

        try {
            const url = new URL(
                "/api/v1/marketplace/products/",
                window.location.origin
            );

            if (search) {
                url.searchParams.set("search", search);
            }

            const response = await fetch(url);

            if (!response.ok) {
                throw new Error("Failed to load products.");
            }

            const data = await response.json();

            const products = data.results || data;

            if (!products.length) {
                emptyState.classList.remove("d-none");
                return;
            }

            products.forEach(product => {
                const seller = product.sellers?.[0];

                const price = seller
                    ? (seller.sale_price || seller.price)
                    : product.min_price;

                const card = document.createElement("div");

                card.className = "col-md-6 col-lg-4";

                card.innerHTML = `
                    <div class="card h-100 border-0 shadow-sm">
                        <div class="card-body">

                            <div class="small text-muted mb-2">
                                ${product.category || ""}
                            </div>

                            <h5 class="fw-bold">
                                ${product.name}
                            </h5>

                            <p class="text-muted small">
                                ${product.brand || ""}
                            </p>

                            <p class="text-muted">
                                ${product.description || ""}
                            </p>

                            <div class="fw-bold fs-5 mb-2">
                                ${price ? `${price} جنيه` : "السعر غير متاح"}
                            </div>

                            ${
                                seller
                                    ? `
                                        <div class="small text-muted mb-3">
                                            ${seller.store_name}
                                            ${seller.city ? ` - ${seller.city}` : ""}
                                        </div>
                                    `
                                    : ""
                            }

                            <a
                                href="/marketplace/products/${product.id}/"
                                class="btn btn-dark w-100"
                            >
                                عرض التفاصيل
                            </a>

                        </div>
                    </div>
                `;

                productsContainer.appendChild(card);
            });

        } catch (error) {
            console.error(error);

            emptyState.textContent =
                "حصل خطأ أثناء تحميل المنتجات.";

            emptyState.classList.remove("d-none");

        } finally {
            loading.classList.add("d-none");
        }
    }

    searchButton.addEventListener("click", searchProducts);

    searchInput.addEventListener("keydown", event => {
        if (event.key === "Enter") {
            searchProducts();
        }
    });
});