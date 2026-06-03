const API_BASE = process.env.REACT_APP_API_BASE || 'https://hntwmrwmsl.execute-api.ap-southeast-1.amazonaws.com';

// Export API_BASE for use in other components
export { API_BASE };

const buildUrl = (path, params = {}) => {
  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  const url = new URL(`${API_BASE}${normalizedPath}`);

  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      url.searchParams.append(key, value);
    }
  });

  return url.toString();
};

export const apiFetch = async (path, { query, ...options } = {}) => {
  const url = path.startsWith('http') ? path : buildUrl(path, query);

  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
  };

  const init = {
    ...options,
    headers,
  };

  if (init.body && typeof init.body !== 'string') {
    init.body = JSON.stringify(init.body);
  }

  const response = await fetch(url, init);

  // ✅ FIX: handle unauthorized safely
  if (response.status === 401) {
    console.warn("Unauthorized request:", path);
    return { status: "error", message: "Unauthorized" };
  }

  return response.json();
};

export const getHeaders = async (isAuthenticated, getAccessTokenSilently) => {
  const headers = {
    'Content-Type': 'application/json',
  };

  if (!isAuthenticated || typeof getAccessTokenSilently !== 'function') {
    return headers;
  }

  try {
    const token = await getAccessTokenSilently({
      cacheMode: 'on', // prefer cache, avoid silent iframe (blocked by tracking prevention)
    });
    headers.Authorization = `Bearer ${token}`;
  } catch (error) {
    console.error('Error getting access token — request will proceed without auth:', error);
  }

  return headers;
};

export const fetchProductById = async (productId) =>
  apiFetch(`/products/${productId}`);

export const fetchProducts = async ({ lastEvaluatedKey, minPrice, maxPrice, category, sortBy } = {}) => {
  const query = {
    limit: 10,
    minPrice,
    maxPrice,
    sortBy,
  };

  if (lastEvaluatedKey) {
    query.lastEvaluatedKey = JSON.stringify(lastEvaluatedKey);
  }

  if (category && category !== 'All') {
    query.category = category;
  }

  return apiFetch('/products', { query });
};

export const fetchSearchResults = async (query, filters = {}) => {
  const queryParams = { q: query };
  
  // Add optional filters
  if (filters.brand) queryParams.brand = filters.brand;
  if (filters.minRating) queryParams.minRating = filters.minRating;
  if (filters.inStockOnly) queryParams.inStockOnly = 'true';
  if (filters.minPrice) queryParams.minPrice = filters.minPrice;
  if (filters.maxPrice) queryParams.maxPrice = filters.maxPrice;
  if (filters.category && filters.category !== 'All') queryParams.category = filters.category;
  
  return apiFetch('/search', { query: queryParams });
};

export const fetchCart = async (headers) => apiFetch('/cart', { headers });

export const fetchOrders = async (headers) => apiFetch('/order', { headers });

export const addToCart = async (productId, variantId, headers) => {
  const body = { id: productId };
  if (variantId) {
    body.variant_id = variantId;
  }
  return apiFetch('/cart/add', {
    method: 'POST',
    headers,
    body,
  });
};

export const removeFromCart = async (productId, headers, variantId = null) => {
  const path = variantId
    ? `/cart/remove/${productId}?variant_id=${encodeURIComponent(variantId)}`
    : `/cart/remove/${productId}`;
  return apiFetch(path, { method: 'DELETE', headers });
};

export const placeOrder = async (items, address, headers, idempotencyKey = null) =>
  apiFetch('/order', {
    method: 'POST',
    headers,
    body: { items, address, ...(idempotencyKey && { idempotency_key: idempotencyKey }) },
  });

export const cancelOrder = async (orderId, headers) =>
  apiFetch(`/order/${orderId}`, {
    method: 'DELETE',
    headers,
  });

export const createRazorpayOrder = async (orderId, headers) =>
  apiFetch('/payment/create-order', {
    method: 'POST',
    headers,
    body: { order_id: orderId },
  });

export const processPayment = async (orderId, amount, headers, razorpayDetails = null) =>
  apiFetch('/payment', {
    method: 'POST',
    headers,
    body: razorpayDetails
      ? { order_id: orderId, amount, ...razorpayDetails }
      : { order_id: orderId, amount },
  });

export const fetchRecommendations = async (productIds, limit = 5) =>
  apiFetch('/recommendations', {
    query: { productIds, limit },
  });

export const fetchWishlist = async (headers) => apiFetch('/wishlist', { headers });

export const addToWishlistApi = async (productId, headers) =>
  apiFetch('/wishlist/add', {
    method: 'POST',
    headers,
    body: { id: productId },
  });

export const removeFromWishlistApi = async (productId, headers) =>
  apiFetch(`/wishlist/remove/${productId}`, {
    method: 'DELETE',
    headers,
  });

// ── Saved Addresses ───────────────────────────────────────────────────────────
export const fetchAddresses = async (headers) => apiFetch('/addresses', { headers });

export const addAddress = async (address, headers) =>
  apiFetch('/addresses', { method: 'POST', headers, body: address });

export const setDefaultAddress = async (addressId, headers) =>
  apiFetch(`/addresses/${addressId}`, { method: 'PUT', headers });

export const deleteAddress = async (addressId, headers) =>
  apiFetch(`/addresses/${addressId}`, { method: 'DELETE', headers });

// ── User Profile ──────────────────────────────────────────────────────────────
export const fetchProfile = async (headers) => apiFetch('/profile/me', { headers });

export const updateProfile = async (profile, headers) =>
  apiFetch('/profile/me', { method: 'PUT', headers, body: profile });

export const sendVerificationEmail = async (headers) =>
  apiFetch('/profile/verify-email', { method: 'POST', headers });

// ── Reviews ───────────────────────────────────────────────────────────────────
export const submitReview = async (productId, reviewData, headers) =>
  apiFetch(`/products/${productId}/reviews`, {
    method: 'POST',
    headers,
    body: reviewData,
  });
