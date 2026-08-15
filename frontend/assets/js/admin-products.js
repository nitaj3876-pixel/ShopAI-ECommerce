// Product-management UI for the existing ShopAI admin dashboard.
(() => {
  const root = document.getElementById("product-management-root");
  if (!root) return;

  let categories = [];
  let products = [];
  let editingProduct = null;

  const escapeHtml = (value = "") => String(value).replace(/[&<>'"]/g, (character) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;",
  })[character]);

  const categoryOptions = (selectedId) => [
    '<option value="">Choose a category</option>',
    ...categories.map((category) => `<option value="${category.id}" ${category.id === selectedId ? "selected" : ""}>${escapeHtml(category.name)}</option>`),
  ].join("");

  function renderShell() {
    root.innerHTML = `
      <div class="card-soft p-3 mb-3">
        <div class="d-flex flex-wrap justify-content-between align-items-center gap-2 mb-3">
          <div><h5 class="fw-bold mb-0">Products</h5><div class="small text-muted">Create, edit, archive and track catalog stock.</div></div>
          <div class="d-flex gap-2"><button type="button" class="btn btn-outline-brand btn-sm" id="new-category-button">+ Category</button><button type="button" class="btn btn-brand btn-sm" id="new-product-button">+ Add product</button></div>
        </div>
        <div class="row g-2">
          <div class="col-md-5"><input id="product-search" class="form-control form-control-sm" placeholder="Search name or brand"></div>
          <div class="col-md-3"><select id="product-category-filter" class="form-select form-select-sm">${categoryOptions()}</select></div>
          <div class="col-md-3"><select id="product-stock-filter" class="form-select form-select-sm"><option value="all">All active stock</option><option value="in_stock">In stock</option><option value="low_stock">Low stock (1–10)</option><option value="out_of_stock">Out of stock</option><option value="archived">Archived</option></select></div>
          <div class="col-md-1"><button type="button" class="btn btn-outline-brand btn-sm w-100" id="product-filter-button">Go</button></div>
        </div>
      </div>
      <div id="product-editor"></div>
      <div class="card-soft p-3">
        <div class="table-responsive"><table class="table table-sm align-middle mb-0">
          <thead><tr><th>Image</th><th>Product</th><th>Category</th><th>Price</th><th>Stock</th><th class="text-end">Actions</th></tr></thead>
          <tbody id="product-table-body"><tr><td colspan="6" class="text-center text-muted py-4">Loading products…</td></tr></tbody>
        </table></div>
      </div>`;

    document.getElementById("new-product-button").addEventListener("click", () => showEditor());
    document.getElementById("new-category-button").addEventListener("click", showCategoryEditor);
    document.getElementById("product-filter-button").addEventListener("click", loadProducts);
    document.getElementById("product-search").addEventListener("keydown", (event) => {
      if (event.key === "Enter") loadProducts();
    });
  }

  function showCategoryEditor() {
    const editor = document.getElementById("product-editor");
    editor.innerHTML = `
      <div class="card-soft p-3 mb-3"><div class="d-flex justify-content-between align-items-center mb-3"><h6 class="fw-bold mb-0">Add category</h6><button type="button" class="btn-close" id="close-category-editor"></button></div>
        <form id="category-form" class="row g-2"><div class="col-md-6"><label class="form-label small fw-semibold">Category name</label><input id="category-name" class="form-control" required maxlength="120"></div><div class="col-md-4"><label class="form-label small fw-semibold">Image URL (optional)</label><input id="category-image" class="form-control" type="url"></div><div class="col-md-2 d-flex align-items-end"><button class="btn btn-brand w-100" type="submit">Create</button></div></form>
      </div>`;
    document.getElementById("close-category-editor").addEventListener("click", () => { editor.innerHTML = ""; });
    document.getElementById("category-form").addEventListener("submit", async (event) => {
      event.preventDefault();
      try {
        await Api.adminCreateCategory({ name: document.getElementById("category-name").value.trim(), image_url: document.getElementById("category-image").value.trim() || null });
        categories = await Api.listCategories();
        renderShell();
        editor.innerHTML = "";
        toast("Category created successfully.");
        loadProductDashboardStats();
      } catch (error) { toast(error.message, true); }
    });
  }

  function showEditor(product = null, viewOnly = false) {
    editingProduct = product;
    const editor = document.getElementById("product-editor");
    const image = product ? firstImage(product.image_urls) : "";
    const title = viewOnly ? "Product details" : product ? "Edit product" : "Add product";
    editor.innerHTML = `
      <div class="card-soft p-3 mb-3">
        <div class="d-flex justify-content-between align-items-center mb-3"><h6 class="fw-bold mb-0">${title}</h6><button type="button" class="btn-close" id="close-product-editor"></button></div>
        <form id="managed-product-form" class="row g-3">
          <div class="col-md-5"><label class="form-label small fw-semibold">Product name</label><input id="managed-name" class="form-control" required value="${escapeHtml(product?.name || "")}" ${viewOnly ? "disabled" : ""}></div>
          <div class="col-md-3"><label class="form-label small fw-semibold">Brand</label><input id="managed-brand" class="form-control" value="${escapeHtml(product?.brand || "")}" ${viewOnly ? "disabled" : ""}></div>
          <div class="col-md-4"><label class="form-label small fw-semibold">Category</label><select id="managed-category" class="form-select" required ${viewOnly ? "disabled" : ""}>${categoryOptions(product?.category_id)}</select></div>
          <div class="col-md-3"><label class="form-label small fw-semibold">Price (₹)</label><input id="managed-price" class="form-control" type="number" min="0" step="0.01" required value="${product?.price ?? ""}" ${viewOnly ? "disabled" : ""}></div>
          <div class="col-md-3"><label class="form-label small fw-semibold">MRP (₹)</label><input id="managed-mrp" class="form-control" type="number" min="0" step="0.01" required value="${product?.mrp ?? ""}" ${viewOnly ? "disabled" : ""}></div>
          <div class="col-md-3"><label class="form-label small fw-semibold">Stock</label><input id="managed-stock" class="form-control" type="number" min="0" step="1" required value="${product?.stock ?? 0}" ${viewOnly ? "disabled" : ""}></div>
          <div class="col-md-3"><label class="form-label small fw-semibold">Image</label><input id="managed-image" class="form-control" type="file" accept="image/jpeg,image/png,image/webp,image/gif" ${product || viewOnly ? "" : "required"} ${viewOnly ? "disabled" : ""}></div>
          <div class="col-12"><label class="form-label small fw-semibold">Description</label><textarea id="managed-description" class="form-control" rows="3" required ${viewOnly ? "disabled" : ""}>${escapeHtml(product?.description || "")}</textarea></div>
          <div class="col-12 d-flex align-items-center gap-3">
            ${image ? `<img src="${escapeHtml(image)}" alt="Current product image" class="rounded border" style="width:64px;height:64px;object-fit:cover">` : ""}
            ${viewOnly ? "" : `<button class="btn btn-brand" type="submit">${product ? "Save changes" : "Add product"}</button>`}
            <span class="small text-muted">${product ? "Upload a new image only to replace the current one." : "JPG, PNG, WebP or GIF, up to 5 MB."}</span>
          </div>
        </form>
      </div>`;
    document.getElementById("close-product-editor").addEventListener("click", () => { editor.innerHTML = ""; });
    if (!viewOnly) document.getElementById("managed-product-form").addEventListener("submit", saveProduct);
  }

  async function saveProduct(event) {
    event.preventDefault();
    const submitButton = event.currentTarget.querySelector("button[type=submit]");
    submitButton.disabled = true;
    try {
      let imageUrls = editingProduct?.image_urls;
      const imageFile = document.getElementById("managed-image").files[0];
      if (imageFile) imageUrls = (await Api.adminUploadProductImage(imageFile)).image_url;
      const payload = {
        name: document.getElementById("managed-name").value.trim(),
        brand: document.getElementById("managed-brand").value.trim() || null,
        category_id: Number(document.getElementById("managed-category").value),
        price: Number(document.getElementById("managed-price").value),
        mrp: Number(document.getElementById("managed-mrp").value),
        stock: Number(document.getElementById("managed-stock").value),
        description: document.getElementById("managed-description").value.trim(),
        image_urls: imageUrls,
      };
      if (editingProduct) await Api.adminUpdateProduct(editingProduct.id, payload);
      else await Api.adminCreateProduct(payload);
      toast(editingProduct ? "Product updated successfully." : "Product added successfully.");
      document.getElementById("product-editor").innerHTML = "";
      await loadProducts();
      loadProductDashboardStats();
    } catch (error) {
      toast(error.message, true);
    } finally {
      submitButton.disabled = false;
    }
  }

  function stockLabel(product) {
    if (!product.is_active) return '<span class="badge text-bg-secondary">Archived</span>';
    if (product.stock === 0) return '<span class="badge text-bg-danger">Out of stock</span>';
    if (product.stock <= 10) return `<span class="badge text-bg-warning">Low: ${product.stock}</span>`;
    return `<span class="badge text-bg-success">${product.stock}</span>`;
  }

  function renderProducts() {
    const table = document.getElementById("product-table-body");
    if (!products.length) {
      table.innerHTML = '<tr><td colspan="6" class="text-center text-muted py-4">No products found.</td></tr>';
      return;
    }
    const categoryNames = new Map(categories.map((category) => [category.id, category.name]));
    table.innerHTML = products.map((product) => `<tr>
      <td><img src="${escapeHtml(firstImage(product.image_urls))}" alt="" class="rounded border" style="width:46px;height:46px;object-fit:cover"></td>
      <td><div class="fw-semibold">${escapeHtml(product.name)}</div><div class="small text-muted">${escapeHtml(product.brand || "No brand")}</div></td>
      <td>${escapeHtml(categoryNames.get(product.category_id) || "—")}</td>
      <td>${formatCurrency(product.price)}<div class="small text-muted text-decoration-line-through">${formatCurrency(product.mrp)}</div></td>
      <td>${stockLabel(product)}</td>
      <td class="text-end"><div class="btn-group btn-group-sm"><button class="btn btn-outline-secondary" data-view="${product.id}">View</button><button class="btn btn-outline-primary" data-edit="${product.id}">Edit</button>${product.is_active ? `<button class="btn btn-outline-danger" data-delete="${product.id}">Archive</button>` : ""}</div></td>
    </tr>`).join("");
    table.querySelectorAll("[data-view]").forEach((button) => button.addEventListener("click", () => showEditor(products.find((product) => product.id === Number(button.dataset.view)), true)));
    table.querySelectorAll("[data-edit]").forEach((button) => button.addEventListener("click", () => showEditor(products.find((product) => product.id === Number(button.dataset.edit)))));
    table.querySelectorAll("[data-delete]").forEach((button) => button.addEventListener("click", () => archiveProduct(Number(button.dataset.delete))));
  }

  async function archiveProduct(productId) {
    const product = products.find((item) => item.id === productId);
    if (!product || !window.confirm(`Archive “${product.name}”? It will be hidden from customers but preserved for orders and records.`)) return;
    try {
      await Api.adminDeleteProduct(productId);
      toast("Product archived successfully.");
      await loadProducts();
      loadProductDashboardStats();
    } catch (error) { toast(error.message, true); }
  }

  async function loadProducts() {
    const table = document.getElementById("product-table-body");
    if (table) table.innerHTML = '<tr><td colspan="6" class="text-center text-muted py-4">Loading products…</td></tr>';
    try {
      products = await Api.adminListProducts({
        search: document.getElementById("product-search")?.value.trim(),
        category_id: document.getElementById("product-category-filter")?.value,
        stock_status: document.getElementById("product-stock-filter")?.value || "all",
        limit: 200,
      });
      renderProducts();
    } catch (error) {
      if (table) table.innerHTML = `<tr><td colspan="6" class="text-center text-danger py-4">${escapeHtml(error.message)}</td></tr>`;
    }
  }

  async function loadProductDashboardStats() {
    try {
      const stats = await Api.adminDashboard();
      const fields = { "stat-categories": stats.total_categories, "stat-stock": stats.total_stock, "stat-low-stock": stats.low_stock_products, "stat-out-of-stock": stats.out_of_stock_products };
      Object.entries(fields).forEach(([id, value]) => { const element = document.getElementById(id); if (element) element.textContent = value; });
    } catch (_) { /* The main dashboard already displays authorization errors. */ }
  }

  async function initialize() {
    try { categories = await Api.listCategories(); } catch (error) { toast(`Could not load categories: ${error.message}`, true); }
    renderShell();
    loadProductDashboardStats();
  }

  // The pre-existing tab switcher emits this event when Products is selected.
  window.addEventListener("shopai:load-products", loadProducts);
  initialize();
})();
