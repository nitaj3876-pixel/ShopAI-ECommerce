// Central API client. Local pages should use the local FastAPI server; the
// hosted API is only the default for a deployed storefront.
const isLocalStorefront = ["localhost", "127.0.0.1"].includes(window.location.hostname);
const API_BASE = window.SHOPAI_API_BASE || (
  isLocalStorefront ? "http://127.0.0.1:8000" : "https://shopai-ecommerce.onrender.com"
);

const Api = {
  token() {
    return localStorage.getItem("shopai_token");
  },
  setToken(token) {
    localStorage.setItem("shopai_token", token);
  },
  clearToken() {
    localStorage.removeItem("shopai_token");
    localStorage.removeItem("shopai_user");
    window.dispatchEvent(new Event("shopai:auth-changed"));
  },
  currentUser() {
    const raw = localStorage.getItem("shopai_user");
    return raw ? JSON.parse(raw) : null;
  },
  setUser(user) {
    localStorage.setItem("shopai_user", JSON.stringify(user));
  },
  isLoggedIn() {
    return !!this.token();
  },
  isAdmin() {
    const u = this.currentUser();
    return !!(u && u.is_admin);
  },

  async request(path, { method = "GET", body, auth = false, query } = {}) {
    let url = `${API_BASE}${path}`;
    if (query) {
      const params = new URLSearchParams(
        Object.entries(query).filter(([, v]) => v !== undefined && v !== null && v !== "")
      );
      const qs = params.toString();
      if (qs) url += `?${qs}`;
    }

    const headers = { "Content-Type": "application/json" };
    if (auth && this.token()) headers["Authorization"] = `Bearer ${this.token()}`;

    const res = await fetch(url, {
      method,
      headers,
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });

    let data = null;
    try {
      data = await res.json();
    } catch (e) {
      data = null;
    }

    if (!res.ok) {
      const message = (data && (data.detail || data.message)) || `Request failed (${res.status})`;
      throw new Error(typeof message === "string" ? message : JSON.stringify(message));
    }
    return data;
  },

  async upload(path, file) {
    const headers = {};
    if (this.token()) headers.Authorization = `Bearer ${this.token()}`;
    const formData = new FormData();
    formData.append("image", file);
    const res = await fetch(`${API_BASE}${path}`, { method: "POST", headers, body: formData });
    const data = await res.json().catch(() => null);
    if (!res.ok) {
      const message = (data && (data.detail || data.message)) || `Upload failed (${res.status})`;
      throw new Error(typeof message === "string" ? message : JSON.stringify(message));
    }
    return data;
  },

  // ---- Auth ----
  register: (payload) => Api.request("/api/auth/register", { method: "POST", body: payload }),
  login: (payload) => Api.request("/api/auth/login", { method: "POST", body: payload }),
  me: () => Api.request("/api/auth/me", { auth: true }),
  forgotPassword: (email) => Api.request("/api/auth/forgot-password", { method: "POST", body: { email } }),
  resetPassword: (payload) => Api.request("/api/auth/reset-password", { method: "POST", body: payload }),

  // ---- Products ----
  listProducts: (query) => Api.request("/api/products", { query }),
  async getProduct(id) {
    try {
      return await Api.request(`/api/products/${id}`, { auth: Api.isLoggedIn() });
    } catch (error) {
      // Product pages are public. A token can become invalid after a backend
      // redeploy, so discard it and retry the request anonymously.
      if (Api.isLoggedIn() && error.message === "Could not validate credentials") {
        Api.clearToken();
        return Api.request(`/api/products/${id}`);
      }
      throw error;
    }
  },
  similarProducts: (id) => Api.request(`/api/products/${id}/similar`),
  productReviews: (id) => Api.request(`/api/products/${id}/reviews`),
  listCategories: () => Api.request("/api/categories"),
  listBrands: () => Api.request("/api/products/brands"),

  // ---- Cart ----
  getCart: () => Api.request("/api/cart", { auth: true }),
  addToCart: (product_id, quantity = 1) =>
    Api.request("/api/cart/items", { method: "POST", auth: true, body: { product_id, quantity } }),
  updateCartItem: (itemId, quantity) =>
    Api.request(`/api/cart/items/${itemId}`, { method: "PUT", auth: true, body: { quantity } }),
  removeCartItem: (itemId) => Api.request(`/api/cart/items/${itemId}`, { method: "DELETE", auth: true }),
  applyCoupon: (code) => Api.request(`/api/cart/apply-coupon?code=${encodeURIComponent(code)}`, { method: "POST", auth: true }),

  // ---- Wishlist ----
  getWishlist: () => Api.request("/api/wishlist", { auth: true }),
  addToWishlist: (productId) => Api.request(`/api/wishlist/${productId}`, { method: "POST", auth: true }),
  removeFromWishlist: (productId) => Api.request(`/api/wishlist/${productId}`, { method: "DELETE", auth: true }),
  moveToCart: (productId) => Api.request(`/api/wishlist/${productId}/move-to-cart`, { method: "POST", auth: true }),

  // ---- Reviews ----
  createReview: (payload) => Api.request("/api/reviews", { method: "POST", auth: true, body: payload }),

  // ---- Orders ----
  checkout: (payload) => Api.request("/api/orders/checkout", { method: "POST", auth: true, body: payload }),
  myOrders: () => Api.request("/api/orders", { auth: true }),
  orderDetail: (id) => Api.request(`/api/orders/${id}`, { auth: true }),
  cancelOrder: (id) => Api.request(`/api/orders/${id}/cancel`, { method: "PUT", auth: true }),
  returnOrder: (id) => Api.request(`/api/orders/${id}/return`, { method: "PUT", auth: true }),

  // ---- Recommendations ----
  personalized: () => Api.request("/api/recommendations/personalized", { auth: true }),
  recentlyViewed: () => Api.request("/api/recommendations/recently-viewed", { auth: true }),
  frequentlyBoughtTogether: (id) => Api.request(`/api/recommendations/frequently-bought-together/${id}`),

  // ---- Chatbot ----
  chat: (message) => Api.request("/api/chatbot", { method: "POST", body: { message } }),

  // ---- User ----
  updateProfile: (payload) => Api.request("/api/users/profile", { method: "PUT", auth: true, body: payload }),
  changePassword: (payload) => Api.request("/api/users/change-password", { method: "PUT", auth: true, body: payload }),
  listAddresses: () => Api.request("/api/users/addresses", { auth: true }),
  addAddress: (payload) => Api.request("/api/users/addresses", { method: "POST", auth: true, body: payload }),
  deleteAddress: (id) => Api.request(`/api/users/addresses/${id}`, { method: "DELETE", auth: true }),
  listNotifications: () => Api.request("/api/users/notifications", { auth: true }),

  // ---- Admin ----
  adminDashboard: () => Api.request("/api/admin/dashboard", { auth: true }),
  adminMonthlySales: () => Api.request("/api/admin/analytics/monthly-sales", { auth: true }),
  adminTopProducts: () => Api.request("/api/admin/analytics/top-products", { auth: true }),
  adminCategorySales: () => Api.request("/api/admin/analytics/category-sales", { auth: true }),
  adminListOrders: (status) => Api.request("/api/admin/orders", { auth: true, query: { status } }),
  adminUpdateOrderStatus: (id, status) => Api.request(`/api/admin/orders/${id}/status`, { method: "PUT", auth: true, body: { status } }),
  adminListUsers: () => Api.request("/api/admin/users", { auth: true }),
  adminToggleUser: (id) => Api.request(`/api/admin/users/${id}/toggle-active`, { method: "PUT", auth: true }),
  adminListProducts: (query) => Api.request("/api/admin/products", { auth: true, query }),
  adminCreateProduct: (payload) => Api.request("/api/admin/products", { method: "POST", auth: true, body: payload }),
  adminUpdateProduct: (id, payload) => Api.request(`/api/admin/products/${id}`, { method: "PUT", auth: true, body: payload }),
  adminDeleteProduct: (id) => Api.request(`/api/admin/products/${id}`, { method: "DELETE", auth: true }),
  adminUploadProductImage: (file) => Api.upload("/api/admin/products/upload-image", file),
  adminCreateCategory: (payload) => Api.request("/api/admin/categories", { method: "POST", auth: true, body: payload }),
  adminListCoupons: () => Api.request("/api/admin/coupons", { auth: true }),
  adminCreateCoupon: (payload) => Api.request("/api/admin/coupons", { method: "POST", auth: true, body: payload }),
};

// ---- Small helpers shared across pages ----
function firstImage(imageUrls) {
  const image = (imageUrls || "").split(",")[0];
  if (!image) return "https://picsum.photos/seed/placeholder/600/600";
  return image.startsWith("/") ? `${API_BASE}${image}` : image;
}
function formatCurrency(n) {
  return "₹" + Number(n || 0).toLocaleString("en-IN", { maximumFractionDigits: 0 });
}
function toast(message, isError = false) {
  const el = document.createElement("div");
  el.textContent = message;
  el.style.cssText = `position:fixed;bottom:20px;left:50%;transform:translateX(-50%);
    background:${isError ? "#e0393e" : "#1a4fd6"};color:#fff;padding:.7rem 1.3rem;border-radius:10px;
    box-shadow:0 8px 24px rgba(0,0,0,.2);z-index:2000;font-size:.9rem;`;
  document.body.appendChild(el);
  setTimeout(() => el.remove(), 2600);
}
function requireLogin(redirectMsg = "Please log in to continue") {
  if (!Api.isLoggedIn()) {
    toast(redirectMsg, true);
    setTimeout(() => (window.location.href = "login.html"), 800);
    return false;
  }
  return true;
}
