let allProducts = [];
let editingProductId = null;
let catalogProducts = [];


document.addEventListener("DOMContentLoaded", () => {
    const productsTableBody = document.getElementById("products-table-body");

    if (!productsTableBody) {
        return;
    }

    loadProducts();

    const searchInput = document.getElementById("products-search");
    const statusFilter = document.getElementById("products-status-filter");

    searchInput?.addEventListener("input", renderProducts);
    statusFilter?.addEventListener("change", renderProducts);
    document.addEventListener("click", handleProductActions);
    document.addEventListener("click", handleInventoryMovements);
    document.addEventListener("click", handleCloseInventoryMovementsModal);

    const editForm = document.getElementById("edit-product-form");

    editForm?.addEventListener("submit", handleEditProductSubmit);

    const openAddProductButton = document.getElementById(
        "open-add-product-modal"
    );

    openAddProductButton?.addEventListener(
        "click",
        openAddProductModal
    );

    document.addEventListener("click", function (event) {
        if (event.target.matches("[data-close-add-modal]")) {
            closeAddProductModal();
        }
    });

    const catalogSearchInput = document.getElementById(
        "catalog-product-search"
    );

    catalogSearchInput?.addEventListener(
        "input",
        renderCatalogProducts
    );

    document.addEventListener(
        "click",
        handleCatalogProductSelection
    );

    document
        .getElementById("change-selected-product")
        ?.addEventListener(
            "click",
            changeSelectedCatalogProduct
        );

    const addProductSubmitButton = document.getElementById(
        "add-product-submit"
    );

    addProductSubmitButton?.addEventListener(
        "click",
        handleAddProductSubmit
    );
});


async function loadProducts() {
    const tableBody = document.getElementById("products-table-body");

    try {
        const response = await QETA3_API.get(
            "/api/v1/stores/dashboard/products/"
        );

        if (!response.ok) {
            throw new Error("Failed to load products.");
        }

        allProducts = await response.json();

        renderProducts();

    } catch (error) {
        console.error("Products loading error:", error);

        tableBody.innerHTML = `
            <tr>
                <td colspan="7" class="products-loading">
                    تعذر تحميل المنتجات.
                </td>
            </tr>
        `;
    }
}


function renderProducts() {
    const tableBody = document.getElementById("products-table-body");
    const countElement = document.getElementById("products-count");

    const searchValue =
        document.getElementById("products-search")
            ?.value
            .trim()
            .toLowerCase() || "";

    const statusValue =
        document.getElementById("products-status-filter")
            ?.value || "all";


    const filteredProducts = allProducts.filter(product => {

        const matchesSearch =
            !searchValue ||
            product.product_name.toLowerCase().includes(searchValue) ||
            (product.seller_sku || "").toLowerCase().includes(searchValue);


        const matchesStatus =
            statusValue === "all" ||
            (statusValue === "active" && product.is_active) ||
            (statusValue === "inactive" && !product.is_active);


        return matchesSearch && matchesStatus;
    });


    countElement.textContent = filteredProducts.length;


    if (!filteredProducts.length) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="7" class="products-loading">
                    لا توجد منتجات مطابقة.
                </td>
            </tr>
        `;

        return;
    }


    tableBody.innerHTML = filteredProducts
        .map(product => {

            const price =
                Number(product.price).toLocaleString("ar-EG", {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2,
                });

            const salePrice =
                product.sale_price
                    ? Number(product.sale_price).toLocaleString("ar-EG", {
                        minimumFractionDigits: 2,
                        maximumFractionDigits: 2,
                    })
                    : "—";


            const status = product.is_active
                ? `<span class="product-status active">نشط</span>`
                : `<span class="product-status inactive">غير نشط</span>`;


            return `
                <tr>

                    <td>
                        <div class="product-name">
                            <strong>${escapeHtml(product.product_name)}</strong>

                            ${
                                product.brand_name
                                    ? `<small>${escapeHtml(product.brand_name)}</small>`
                                    : ""
                            }
                        </div>
                    </td>

                    <td>
                        ${escapeHtml(product.seller_sku || "—")}
                    </td>

                    <td>
                        ${price} ج.م
                    </td>

                    <td>
                        ${salePrice === "—" ? "—" : `${salePrice} ج.م`}
                    </td>

                    <td>
                        <strong>${product.available_stock}</strong>
                    </td>

                    <td>
                        ${status}
                    </td>

                   <td>
    <div class="product-actions">
        <button
            type="button"
            class="product-action"
            data-product-id="${product.id}"
        >
            تعديل
        </button>

        <button
            type="button"
            class="product-action"
            data-movements-product-id="${product.id}"
        >
            حركات المخزون
        </button>
    </div>
</td>

                </tr>
            `;
        })
        .join("");
}


function escapeHtml(value) {
    const div = document.createElement("div");
    div.textContent = value;
    return div.innerHTML;
}

function handleProductActions(event) {
    const button = event.target.closest(".product-action");

    if (!button) return;

    const productId = button.dataset.productId;

    openEditProductModal(productId);
}

async function handleInventoryMovements(event) {
    const button = event.target.closest(
        "[data-movements-product-id]"
    );

    if (!button) {
        return;
    }

    const productId = button.dataset.movementsProductId;

    const product = allProducts.find(
        item => String(item.id) === String(productId)
    );

    if (!product) {
        console.error("Product not found:", productId);
        return;
    }

    openInventoryMovementsModal(product);
}

function handleCloseInventoryMovementsModal(event) {
    const closeButton = event.target.closest(
        "[data-close-movements-modal]"
    );

    if (!closeButton) {
        return;
    }

    const modal = document.getElementById(
        "inventory-movements-modal"
    );

    if (!modal) {
        return;
    }

    modal.hidden = true;
}

async function openInventoryMovementsModal(product) {
    const modal = document.getElementById(
        "inventory-movements-modal"
    );

    const productName = document.getElementById(
        "inventory-movements-product-name"
    );

    const loading = document.getElementById(
        "inventory-movements-loading"
    );

    const errorElement = document.getElementById(
        "inventory-movements-error"
    );

    const emptyElement = document.getElementById(
        "inventory-movements-empty"
    );

    const list = document.getElementById(
        "inventory-movements-list"
    );

    if (!modal || !list) {
        return;
    }

    productName.textContent = product.product_name || "—";

    errorElement.hidden = true;
    emptyElement.hidden = true;
    list.innerHTML = "";

    loading.hidden = false;
    modal.hidden = false;

    try {
        if (!product.inventory_id) {
            throw new Error(
                "لا يوجد مخزون مرتبط بهذا المنتج."
            );
        }

        const response = await QETA3_API.get(
            `/api/v1/inventory/${product.inventory_id}/movements/`
        );

        if (!response.ok) {
            throw new Error(
                "تعذر تحميل حركات المخزون."
            );
        }

        const movements = await response.json();

        loading.hidden = true;

        if (!movements.length) {
            emptyElement.hidden = false;
            return;
        }

        renderInventoryMovements(movements);

    } catch (error) {
        console.error(
            "Inventory movements loading error:",
            error
        );

        loading.hidden = true;

        errorElement.textContent =
            error.message ||
            "تعذر تحميل حركات المخزون.";

        errorElement.hidden = false;
    }
}

function renderInventoryMovements(movements) {
    const list = document.getElementById(
        "inventory-movements-list"
    );

    if (!list) {
        return;
    }

    list.innerHTML = movements
        .map(movement => {
            const quantity = Number(movement.quantity);

            const formattedDate = movement.created_at
                ? new Date(movement.created_at).toLocaleString(
                    "ar-EG",
                    {
                        dateStyle: "medium",
                        timeStyle: "short",
                    }
                )
                : "—";

            return `
                <div class="inventory-movement-item">
                    <div class="inventory-movement-main">
                       <div class="inventory-movement-type">
    <strong
        class="inventory-movement-type-badge movement-${String(
            movement.movement_type || ""
        ).toLowerCase()}"
    >
        ${escapeHtml(
            movement.movement_type_label || "—"
        )}
    </strong>
</div>

                        <span class="inventory-movement-quantity">
                            ${quantity}
                        </span>
                    </div>

                    <div class="inventory-movement-meta">
    <span class="inventory-movement-date">
        ${formattedDate}
    </span>

    ${
        movement.created_by_phone
            ? `
                <span class="inventory-movement-user">
                    بواسطة
                    <bdi dir="ltr">${escapeHtml(
                        movement.created_by_phone
                    )}</bdi>
                </span>
            `
            : ""
    }
</div>

                    ${
                        movement.note
                            ? `
                                <div class="inventory-movement-note">
                                    ${escapeHtml(movement.note)}
                                </div>
                            `
                            : ""
                    }
                </div>
            `;
        })
        .join("");
}

function openEditProductModal(productId) {
    const product = allProducts.find(
        item => String(item.id) === String(productId)
    );

    if (!product) {
        console.error("Product not found:", productId);
        return;
    }

    editingProductId = product.id;

    const modal = document.getElementById("edit-product-modal");

    document.getElementById("edit-product-name").textContent =
        product.product_name || "—";

    document.getElementById("edit-seller-sku").value =
        product.seller_sku ?? "";

    document.getElementById("edit-price").value =
        product.price ?? "";

    document.getElementById("edit-sale-price").value =
        product.sale_price ?? "";

    document.getElementById("edit-status").value =
        product.is_active ? "true" : "false";

    document.getElementById("edit-product-error").hidden = true;

    modal.hidden = false;
}

document.addEventListener("click", function (event) {
    if (!event.target.matches("[data-close-modal]")) {
        return;
    }

    closeEditProductModal();
});

function closeEditProductModal() {
    const modal = document.getElementById("edit-product-modal");

    if (modal) {
        modal.hidden = true;
    }
}

async function handleEditProductSubmit(event) {
    event.preventDefault();

    if (!editingProductId) {
        return;
    }

    const saveButton = document.getElementById("save-product-btn");
    const errorElement = document.getElementById("edit-product-error");

    const sellerSku = document
        .getElementById("edit-seller-sku")
        .value
        .trim();

    const price = document
        .getElementById("edit-price")
        .value;

    const salePrice = document
        .getElementById("edit-sale-price")
        .value;

    const isActive =
        document.getElementById("edit-status").value === "true";

    const currentProduct = allProducts.find(
        product => String(product.id) === String(editingProductId)
    );

    if (!currentProduct) {
        return;
    }

    const statusChanged = currentProduct.is_active !== isActive;

    // تأكيد قبل تعطيل المنتج
    if (statusChanged && !isActive) {
        const confirmed = confirm(
            "هل أنت متأكد من تعطيل هذا المنتج؟\n\nلن يظهر للعملاء كمنتج متاح من متجرك."
        );

        if (!confirmed) {
            document.getElementById("edit-status").value =
                currentProduct.is_active ? "true" : "false";

            return;
        }
    }

    errorElement.hidden = true;

    saveButton.disabled = true;
    saveButton.textContent = "جاري الحفظ...";

    try {
        // =========================
        // 1. تحديث بيانات المنتج
        // =========================

        const response = await QETA3_API.patch(
            `/api/v1/stores/products/${editingProductId}/`,
            {
                seller_sku: sellerSku,
                price: price,
                sale_price: salePrice || null,
            }
        );

        if (!response.ok) {
            let message = "تعذر حفظ بيانات المنتج.";

            try {
                const data = await response.json();

                if (data.detail) {
                    message = data.detail;
                } else if (typeof data === "object") {
                    message = Object.values(data)
                        .flat()
                        .join(" ");
                }
            } catch (_) {
                // Ignore invalid JSON response.
            }

            throw new Error(message);
        }

        const updatedProduct = await response.json();

        // =========================
        // 2. تغيير حالة المنتج
        // =========================

        if (statusChanged) {
            const statusEndpoint = isActive
                ? `/api/v1/stores/products/${editingProductId}/activate/`
                : `/api/v1/stores/products/${editingProductId}/deactivate/`;

            const statusResponse = await QETA3_API.patch(
                statusEndpoint
            );

            if (!statusResponse.ok) {
                let message = "تم تحديث بيانات المنتج، لكن تعذر تغيير حالته.";

                try {
                    const data = await statusResponse.json();

                    if (data.detail) {
                        message = data.detail;
                    } else if (typeof data === "object") {
                        message = Object.values(data)
                            .flat()
                            .join(" ");
                    }
                } catch (_) {
                    // Ignore invalid JSON response.
                }

                throw new Error(message);
            }
        }

        // =========================
        // 3. تحديث البيانات المحلية
        // =========================

        const index = allProducts.findIndex(
            product => String(product.id) === String(editingProductId)
        );

        if (index !== -1) {
            allProducts[index] = {
                ...allProducts[index],
                ...updatedProduct,
                seller_sku: sellerSku,
                price: price,
                sale_price: salePrice || null,
                is_active: isActive,
            };
        }

        // =========================
        // 4. إغلاق وتحديث الجدول
        // =========================

        closeEditProductModal();
        renderProducts();

    } catch (error) {
        console.error("Product update error:", error);

        errorElement.textContent =
            error.message || "تعذر حفظ التعديلات.";

        errorElement.hidden = false;

    } finally {
        saveButton.disabled = false;
        saveButton.textContent = "حفظ التعديلات";
    }
}

async function openAddProductModal() {
    const modal = document.getElementById("add-product-modal");

    if (!modal) {
        return;
    }

    modal.hidden = false;

    await loadCatalogProducts();
}

function closeAddProductModal() {
    const modal = document.getElementById("add-product-modal");

    if (!modal) {
        return;
    }

    modal.hidden = true;
}

async function loadCatalogProducts() {
    const list = document.getElementById("catalog-products-list");
    const count = document.getElementById("catalog-products-count");

    if (!list || !count) {
        return;
    }

    list.innerHTML = `
        <div class="catalog-products-loading">
            جاري تحميل المنتجات...
        </div>
    `;

    try {
        const response = await QETA3_API.get(
            "/api/v1/catalog/products/"
        );

        if (!response.ok) {
            throw new Error("Failed to load catalog products.");
        }

        const data = await response.json();

        const existingProductIds = new Set(
            allProducts.map(product => String(product.product))
        );

        catalogProducts = (data.results || []).filter(
            product => !existingProductIds.has(String(product.id))
        );

        count.textContent = catalogProducts.length;

        renderCatalogProducts();

    } catch (error) {
        console.error("Catalog products loading error:", error);

        list.innerHTML = `
            <div class="catalog-products-empty">
                تعذر تحميل منتجات الكتالوج.
            </div>
        `;

        count.textContent = "0";
    }
}

function renderCatalogProducts() {
    const list = document.getElementById(
        "catalog-products-list"
    );

    const count = document.getElementById(
        "catalog-products-count"
    );

    const searchInput = document.getElementById(
        "catalog-product-search"
    );

    if (!list || !count) {
        return;
    }

    const searchValue =
        searchInput?.value.trim().toLowerCase() || "";

    const filteredProducts = catalogProducts.filter(product => {
        const name =
            (product.name || "").toLowerCase();

        const slug =
            (product.slug || "").toLowerCase();

        return (
            !searchValue ||
            name.includes(searchValue) ||
            slug.includes(searchValue)
        );
    });

    count.textContent = filteredProducts.length;

    if (!filteredProducts.length) {
        list.innerHTML = `
            <div class="catalog-products-empty">
                لا توجد منتجات مطابقة.
            </div>
        `;

        return;
    }

    list.innerHTML = filteredProducts.map(product => `
        <button
            type="button"
            class="catalog-product-item"
            data-catalog-product-id="${product.id}"
        >
            <strong>
                ${escapeHtml(product.name)}
            </strong>

            <small>
                ${escapeHtml(product.brand_name || "")}
                ${product.category_name
                    ? ` • ${escapeHtml(product.category_name)}`
                    : ""}
            </small>
        </button>
    `).join("");
}

function handleCatalogProductSelection(event) {
    const productButton = event.target.closest(
        ".catalog-product-item"
    );

    if (!productButton) {
        return;
    }

    const productId = productButton.dataset.catalogProductId;

    const product = catalogProducts.find(
        item => String(item.id) === String(productId)
    );

    if (!product) {
        console.error("Catalog product not found:", productId);
        return;
    }

    selectCatalogProduct(product);
}

function selectCatalogProduct(product) {
    const selectedProduct = document.getElementById(
        "selected-catalog-product"
    );

    const productName = document.getElementById(
        "selected-product-name"
    );

    const productMeta = document.getElementById(
        "selected-product-meta"
    );

    const productList = document.getElementById(
        "catalog-products-list"
    );

    const searchInput = document.getElementById(
        "catalog-product-search"
    );

    const submitButton = document.getElementById(
        "add-product-submit"
    );

    if (!selectedProduct) {
        return;
    }

    productName.textContent = product.name;

    productMeta.textContent =
        `${product.brand_name || ""}` +
        `${product.category_name ? ` • ${product.category_name}` : ""}`;

    selectedProduct.hidden = false;

    productList.style.display = "none";

    searchInput.value = "";

    submitButton.disabled = false;

    selectedProduct.dataset.productId = product.id;
}

function changeSelectedCatalogProduct() {
    const selectedProduct = document.getElementById(
        "selected-catalog-product"
    );

    const productList = document.getElementById(
        "catalog-products-list"
    );

    const searchInput = document.getElementById(
        "catalog-product-search"
    );

    const submitButton = document.getElementById(
        "add-product-submit"
    );

    selectedProduct.hidden = true;

    productList.style.display = "";

    submitButton.disabled = true;

    searchInput.focus();
}

async function handleAddProductSubmit() {
    const selectedProduct = document.getElementById(
        "selected-catalog-product"
    );

    const submitButton = document.getElementById(
        "add-product-submit"
    );

    const errorElement = document.getElementById(
        "add-product-error"
    );

    if (!selectedProduct || !submitButton) {
        return;
    }

    const productId = selectedProduct.dataset.productId;

    const sellerSku = document
        .getElementById("add-seller-sku")
        ?.value
        .trim();

    const stockValue = document
        .getElementById("add-stock")
        ?.value;

    const price = document
        .getElementById("add-price")
        ?.value;

    const salePrice = document
        .getElementById("add-sale-price")
        ?.value;

    if (!productId) {
        return;
    }

    if (!price || Number(price) <= 0) {
        errorElement.textContent =
            "يرجى إدخال سعر أساسي صحيح.";

        errorElement.hidden = false;
        return;
    }

    if (salePrice && Number(salePrice) <= 0) {
        errorElement.textContent =
            "سعر البيع يجب أن يكون أكبر من صفر.";

        errorElement.hidden = false;
        return;
    }

    if (
        salePrice &&
        Number(salePrice) > Number(price)
    ) {
        errorElement.textContent =
            "سعر البيع لا يمكن أن يكون أكبر من السعر الأساسي.";

        errorElement.hidden = false;
        return;
    }

    const initialStock = stockValue
        ? Number(stockValue)
        : 0;

    if (
        !Number.isInteger(initialStock) ||
        initialStock < 0
    ) {
        errorElement.textContent =
            "الكمية الابتدائية يجب أن تكون رقمًا صحيحًا أكبر من أو يساوي صفر.";

        errorElement.hidden = false;
        return;
    }

    errorElement.hidden = true;

    submitButton.disabled = true;
    submitButton.textContent = "جاري إضافة المنتج...";

    try {
        const response = await QETA3_API.post(
            "/api/v1/stores/products/",
            {
                product: productId,
                seller_sku: sellerSku,
                price: price,
                sale_price: salePrice || null,
                initial_stock: initialStock,
            }
        );

        if (!response.ok) {
            let message = "تعذر إضافة المنتج.";

            try {
                const data = await response.json();

                if (data.detail) {
                    message = data.detail;
                } else if (typeof data === "object") {
                    message = Object.values(data)
                        .flat()
                        .join(" ");
                }
            } catch (_) {
                // Ignore invalid JSON response.
            }

            throw new Error(message);
        }

        const createdProduct = await response.json();

        console.log(
            "Product created successfully:",
            createdProduct
        );

        closeAddProductModal();

        await loadProducts();

    } catch (error) {
        console.error(
            "Product creation error:",
            error
        );

        errorElement.textContent =
            error.message ||
            "تعذر إضافة المنتج.";

        errorElement.hidden = false;

    } finally {
        submitButton.disabled = false;
        submitButton.textContent = "إضافة المنتج";
    }
}