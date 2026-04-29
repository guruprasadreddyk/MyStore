const API_BASE = process.env.REACT_APP_API_BASE || 'https://hntwmrwmsl.execute-api.ap-southeast-1.amazonaws.com';

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

const apiFetch = async (path, { query, ...options } = {}) => {
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
    const token = await getAccessTokenSilently();
    headers.Authorization = `Bearer ${token}`;
  } catch (error) {
    console.error('Error getting access token', error);
  }

  return headers;
};

export const fetchProducts = async ({ lastEvaluatedKey, minPrice, maxPrice, category, sortBy } = {}) => {
  const query = {
    limit: 8,
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

export const fetchSearchResults = async (query) => apiFetch('/search', { query: { q: query } });

export const fetchCart = async (headers) => apiFetch('/cart', { headers });

export const fetchOrders = async (headers) => apiFetch('/order', { headers });

export const addToCart = async (productId, headers) =>
  apiFetch('/cart/add', {
    method: 'POST',
    headers,
    body: { id: productId },
  });

export const removeFromCart = async (productId, headers) =>
  apiFetch(`/cart/remove/${productId}`, {
    method: 'DELETE',
    headers,
  });

export const placeOrder = async (items, headers) =>
  apiFetch('/order', {
    method: 'POST',
    headers,
    body: { items },
  });

export const processPayment = async (orderId, amount, headers) =>
  apiFetch('/payment', {
    method: 'POST',
    headers,
    body: { order_id: orderId, amount },
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
