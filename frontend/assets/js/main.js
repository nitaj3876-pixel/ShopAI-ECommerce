// Renders the shared navbar & footer into #navbar-root / #footer-root on every page.

function renderNavbar(active = "") {
  const root = document.getElementById("navbar-root");
  if (!root) return;
  const user = Api.currentUser();

  root.innerHTML = `
  <nav class="shopai-navbar sticky-top">
    <div class="container d-flex align-items-center flex-wrap gap-2 py-1">
      <a href="index.html" class="brand me-3">Shop<span>AI</span></a>
      <form class="search-form d-flex flex-grow-1" style="max-width:520px" onsubmit="doSearch(event)">
        <input type="search" id="navbar-search" class="form-control" placeholder="Search for products, brands and more">
        <button type="submit"><i class="bi bi-search"></i>🔍</button>
      </form>
      <div class="d-flex align-items-center ms-auto">
        <a href="${user ? "profile.html" : "login.html"}" class="icon-btn" title="Account">👤 ${user ? user.name.split(" ")[0] : "Login"}</a>
        <a href="wishlist.html" class="icon-btn" title="Wishlist">❤️<span id="wishlist-badge" class="badge-count d-none">0</span></a>
        <a href="cart.html" class="icon-btn" title="Cart">🛒<span id="cart-badge" class="badge-count d-none">0</span></a>
        <a href="orders.html" class="icon-btn" title="Orders">📦</a>
        ${user && user.is_admin ? '<a href="admin.html" class="icon-btn" title="Admin">⚙️</a>' : ""}
        ${user ? '<a href="#" onclick="doLogout(event)" class="icon-btn" title="Logout">↪️</a>' : ""}
      </div>
    </div>
    <div class="container">
      <div class="d-flex gap-3 pb-2 flex-wrap small">
        <a href="products.html" onclick="window.location.assign(this.href); return false;" class="shop-nav-link ${active === 'products' ? 'fw-bold text-decoration-underline' : ''}">All Products</a>
        <a href="products.html?featured=true" onclick="window.location.assign(this.href); return false;" class="shop-nav-link">Featured</a>
        <a href="products.html?flash_sale=true" onclick="window.location.assign(this.href); return false;" class="shop-nav-link">Flash Sale</a>
        <a href="products.html?trending=true" onclick="window.location.assign(this.href); return false;" class="shop-nav-link">Trending</a>
        <a href="products.html?best_seller=true" onclick="window.location.assign(this.href); return false;" class="shop-nav-link">Best Sellers</a>
      </div>
    </div>
  </nav>`;

  updateBadges();
}

function doSearch(e) {
  e.preventDefault();
  const q = document.getElementById("navbar-search").value.trim();
  window.location.href = `products.html${q ? "?search=" + encodeURIComponent(q) : ""}`;
}

function doLogout(e) {
  e.preventDefault();
  Api.clearToken();
  toast("Logged out");
  setTimeout(() => (window.location.href = "index.html"), 500);
}

async function updateBadges() {
  if (!Api.isLoggedIn()) return;
  try {
    const cart = await Api.getCart();
    const cartCount = cart.items.reduce((s, i) => s + i.quantity, 0);
    const cartBadge = document.getElementById("cart-badge");
    if (cartBadge) {
      cartBadge.textContent = cartCount;
      cartBadge.classList.toggle("d-none", cartCount === 0);
    }
  } catch (e) { /* ignore */ }
  try {
    const wishlist = await Api.getWishlist();
    const wishBadge = document.getElementById("wishlist-badge");
    if (wishBadge) {
      wishBadge.textContent = wishlist.length;
      wishBadge.classList.toggle("d-none", wishlist.length === 0);
    }
  } catch (e) { /* ignore */ }
}

function renderFooter() {
  const root = document.getElementById("footer-root");
  if (!root) return;
  root.innerHTML = `
  <footer class="shopai-footer">
    <div class="container">
      <div class="row g-4">
        <div class="col-6 col-md-3">
          <h6>ShopAI</h6>
          <a href="index.html">About Us</a>
          <a href="#">Careers</a>
          <a href="#">Press</a>
        </div>
        <div class="col-6 col-md-3">
          <h6>Help</h6>
          <a href="orders.html">Track Order</a>
          <a href="#">Returns & Refunds</a>
          <a href="#">Shipping Info</a>
        </div>
        <div class="col-6 col-md-3">
          <h6>Policy</h6>
          <a href="#">Terms of Use</a>
          <a href="#">Privacy Policy</a>
          <a href="#">Security</a>
        </div>
        <div class="col-6 col-md-3">
          <h6>Newsletter</h6>
          <p class="small mb-2">Get the latest deals in your inbox.</p>
          <form class="d-flex gap-2" onsubmit="event.preventDefault(); toast('Subscribed! 🎉')">
            <input type="email" class="form-control form-control-sm" placeholder="Email address" required>
            <button class="btn btn-accent btn-sm">Go</button>
          </form>
        </div>
      </div>
      <hr class="border-secondary mt-4">
      <p class="small text-center mb-0">© 2026 ShopAI. Built for demo/educational purposes.</p>
    </div>
  </footer>`;
}

// ---- Product card ----
function productCardHtml(p) {
  const discount = p.discount_percent || 0;
  return `
  <div class="col-6 col-md-4 col-lg-3">
    <div class="card-soft product-card position-relative">
      <button class="wishlist-btn" onclick="toggleWishlistQuick(event, ${p.id}, this)" title="Add to wishlist">♡</button>
      <a href="product_details.html?id=${p.id}" onclick="openProductDetail(event, ${p.id})">
        <img src="${firstImage(p.image_urls)}" alt="${p.name}">
      </a>
      <div class="body">
        <a href="product_details.html?id=${p.id}" class="text-dark text-decoration-none" onclick="openProductDetail(event, ${p.id})">
          <div class="small text-muted">${p.brand || ""}</div>
          <div class="fw-semibold mb-1" style="font-size:.92rem; min-height:2.4em;">${p.name}</div>
        </a>
        <div class="d-flex align-items-center gap-2 mb-1">
          <span class="rating-pill">${p.rating_avg?.toFixed(1) || "New"} ★</span>
          <span class="small text-muted">(${p.rating_count || 0})</span>
        </div>
        <div class="d-flex align-items-center gap-2 mb-2">
          <span class="price">${formatCurrency(p.price)}</span>
          ${discount > 0 ? `<span class="mrp">${formatCurrency(p.mrp)}</span><span class="discount">${discount}% off</span>` : ""}
        </div>
        <button class="btn btn-brand w-100 btn-sm mt-auto" onclick="quickAddToCart(event, ${p.id})" ${p.stock === 0 ? "disabled" : ""}>
          ${p.stock === 0 ? "Out of stock" : "Add to Cart"}
        </button>
      </div>
    </div>
  </div>`;
}

async function quickAddToCart(e, productId) {
  e.preventDefault();
  if (!requireLogin("Please log in to add items to your cart")) return;
  try {
    await Api.addToCart(productId, 1);
    window.location.href = "cart.html";
  } catch (err) {
    toast(err.message, true);
  }
}

async function toggleWishlistQuick(e, productId, btnEl) {
  e.preventDefault();
  if (!requireLogin("Please log in to use your wishlist")) return;
  try {
    await Api.addToWishlist(productId);
    btnEl.classList.add("active");
    btnEl.textContent = "❤";
    toast("Added to wishlist!");
    updateBadges();
  } catch (err) {
    toast(err.message, true);
  }
}

function renderProductGrid(containerId, products) {
  const el = document.getElementById(containerId);
  if (!el) return;
  if (!products || products.length === 0) {
    el.innerHTML = `<div class="col-12 text-center text-muted py-5">No products found.</div>`;
    return;
  }
  el.innerHTML = products.map(productCardHtml).join("");
}

async function openProductDetail(event, productId) {
  event.preventDefault();
  const destination = event.currentTarget.href;
  try {
    const product = await Api.getProduct(productId);
    sessionStorage.setItem(`shopai_product_${productId}`, JSON.stringify(product));
  } catch (_) {
    // Fall back to the normal detail-page request if preloading is unavailable.
  }
  window.location.assign(destination);
}
