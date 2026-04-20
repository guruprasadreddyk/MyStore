import React, { useState, useEffect } from 'react';
import './App.css';

const APP_NAME = 'MyStore';
const API_BASE = '';

function App() {
  const [products, setProducts] = useState([]);
  const [cart, setCart] = useState([]);
  const [orders, setOrders] = useState([]);
  const [currentView, setCurrentView] = useState('products');
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState(null);
  const [filteredProducts, setFilteredProducts] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState('All');

  // Fetch products on component mount
  useEffect(() => {
    document.title = APP_NAME;
    fetchProducts();
    fetchCart();
    fetchOrders();
  }, []);

  // Search API integration
  useEffect(() => {
    const query = searchQuery.trim();
    if (query === '') {
      setSearchResults(null);
      return;
    }

    const fetchSearchResults = async () => {
      setLoading(true);
      const queryLower = query.toLowerCase();
      const localFallback = products.filter(product =>
        product.name.toLowerCase().includes(queryLower) ||
        product.description.toLowerCase().includes(queryLower)
      );

      try {
        const response = await fetch(`${API_BASE}/search?q=${encodeURIComponent(query)}`);
        const data = await response.json();
        if (data.status === 'success') {
          setSearchResults(data.data);
        } else {
          console.error('Search error:', data.message);
          setSearchResults(localFallback);
        }
      } catch (error) {
        console.error('Error searching products:', error);
        setSearchResults(localFallback);
      }
    };

    fetchSearchResults();
  }, [searchQuery, products]);

  // Filter products based on search results and category
  useEffect(() => {
    let filtered = searchResults ?? products;

    // Filter by category
    if (selectedCategory !== 'All') {
      filtered = filtered.filter(product => product.category === selectedCategory);
    }

    setFilteredProducts(filtered);
  }, [searchResults, selectedCategory, products]);

  const fetchProducts = async () => {
    try {
      const response = await fetch(`${API_BASE}/products`);
      const data = await response.json();
      if (data.status === 'success') {
        setProducts(data.data);
      }
    } catch (error) {
      console.error('Error fetching products:', error);
    }
  };

  // Get unique categories
  const categories = ['All', ...new Set(products.map(product => product.category))];

  const fetchCart = async () => {
    try {
      const response = await fetch(`${API_BASE}/cart`);
      const data = await response.json();
      if (data.status === 'success') {
        setCart(data.data);
      }
    } catch (error) {
      console.error('Error fetching cart:', error);
    }
  };

  const fetchOrders = async () => {
    try {
      const response = await fetch(`${API_BASE}/order`);
      const data = await response.json();
      if (data.status === 'success') {
        setOrders(data.data);
      }
    } catch (error) {
      console.error('Error fetching orders:', error);
    }
  };

  const addToCart = async (productId) => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE}/cart/add`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ id: productId }),
      });
      const data = await response.json();
      if (data.status === 'success') {
        setCart(data.data);
      } else {
        alert(data.message);
      }
    } catch (error) {
      console.error('Error adding to cart:', error);
      alert('Error adding item to cart');
    }
    setLoading(false);
  };

  const removeFromCart = async (productId) => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE}/cart/remove/${productId}`, {
        method: 'DELETE',
      });
      const data = await response.json();
      if (data.status === 'success') {
        setCart(data.data);
      } else {
        alert(data.message);
      }
    } catch (error) {
      console.error('Error removing from cart:', error);
      alert('Error removing item from cart');
    }
    setLoading(false);
  };

  const placeOrder = async () => {
    if (cart.length === 0) {
      alert('Cart is empty');
      return;
    }

    setLoading(true);
    try {
      const items = cart.map(item => ({ id: item.id }));
      const response = await fetch(`${API_BASE}/order`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ items }),
      });
      const data = await response.json();
      if (data.status === 'success') {
        setProducts(prevProducts => prevProducts.map(product => {
          const cartItem = cart.find(item => item.id === product.id);
          if (!cartItem) return product;
          return {
            ...product,
            stock_quantity: Math.max(product.stock_quantity - cartItem.quantity, 0),
          };
        }));
        // Refetch orders from backend instead of adding to local state
        fetchOrders();
        setCart([]);
        setCurrentView('orders');
        alert('Order placed successfully!');
      } else {
        alert(data.message);
      }
    } catch (error) {
      console.error('Error placing order:', error);
      alert('Error placing order');
    }
    setLoading(false);
  };

  const processPayment = async (orderId) => {
    const order = orders.find(o => o.order_id === orderId);
    if (!order) return;

    const total = order.items.reduce((sum, item) => sum + (item.price * item.quantity), 0);

    setLoading(true);
    try {
      const response = await fetch(`${API_BASE}/payment`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          order_id: orderId,
          amount: total,
        }),
      });
      const data = await response.json();
      if (data.status === 'success') {
        alert('Payment successful!');
        // Refresh orders from backend to get updated status
        fetchOrders();
      } else {
        alert(data.message);
      }
    } catch (error) {
      console.error('Error processing payment:', error);
      alert('Error processing payment');
    }
    setLoading(false);
  };

  const getCartTotal = () => {
    return cart.reduce((total, item) => total + (item.price * item.quantity), 0);
  };

  const getCartItemCount = () => {
    return cart.reduce((total, item) => total + item.quantity, 0);
  };

  return (
    <div className="App">
      <header className="App-header">
        <div className="brand-block">
          <h1>{APP_NAME}</h1>
          <p className="hero-subtitle">Shop smart, search fast, and checkout with confidence.</p>
        </div>
        <nav>
          <button onClick={() => setCurrentView('products')} className={currentView === 'products' ? 'active' : ''}>Products</button>
          <button onClick={() => setCurrentView('cart')} className={currentView === 'cart' ? 'active' : ''}>
            Cart ({getCartItemCount()})
          </button>
          <button onClick={() => setCurrentView('orders')} className={currentView === 'orders' ? 'active' : ''}>Orders</button>
        </nav>
      </header>

      <main>
        {currentView === 'products' && (
          <div className="products">
            <h2>Products</h2>
            <div className="filters">
              <div className="search-container">
                <input
                  type="text"
                  placeholder="Search products..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="search-input"
                />
              </div>
              <div className="category-filter">
                <select
                  value={selectedCategory}
                  onChange={(e) => setSelectedCategory(e.target.value)}
                  className="category-select"
                >
                  {categories.map(category => (
                    <option key={category} value={category}>{category}</option>
                  ))}
                </select>
              </div>
            </div>
            {(searchQuery || selectedCategory !== 'All') && (
              <div className="status-banner">
                <span>{filteredProducts.length} results found</span>
                <span>{searchQuery ? `Searching for “${searchQuery}”` : 'Showing all filtered products'}</span>
              </div>
            )}
            <div className="product-grid">
              {filteredProducts.map(product => (
                <div key={product.id} className="product-card">
                  <h3>{product.name}</h3>
                  <p className="product-category">{product.category}</p>
                  <p className="product-description">{product.description}</p>
                  <div className="product-details">
                    <span className="product-price">${product.price}</span>
                    <span className={`product-stock ${product.stock_quantity > 0 ? 'in-stock' : 'out-of-stock'}`}>
                      {product.stock_quantity > 0 ? `In Stock (${product.stock_quantity})` : 'Out of Stock'}
                    </span>
                  </div>
                  <div className="product-rating">
                    ⭐ {product.rating}/5
                  </div>
                  <button
                    onClick={() => addToCart(product.id)}
                    disabled={loading || product.stock_quantity <= 0}
                  >
                    {product.stock_quantity > 0 ? 'Add to Cart' : 'Out of Stock'}
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {currentView === 'cart' && (
          <div className="cart">
            <h2>Shopping Cart</h2>
            {cart.length === 0 ? (
              <p>Your cart is empty</p>
            ) : (
              <>
                <div className="cart-items">
                  {cart.map(item => (
                    <div key={item.id} className="cart-item">
                      <h3>{item.name}</h3>
                      <p>Price: ${item.price}</p>
                      <p>Quantity: {item.quantity}</p>
                      <button
                        onClick={() => removeFromCart(item.id)}
                        disabled={loading}
                      >
                        Remove One
                      </button>
                    </div>
                  ))}
                </div>
                <div className="cart-total">
                  <h3>Total: ${getCartTotal()}</h3>
                  <button
                    onClick={placeOrder}
                    disabled={loading}
                    className="place-order-btn"
                  >
                    Place Order
                  </button>
                </div>
              </>
            )}
          </div>
        )}

        {currentView === 'orders' && (
          <div className="orders">
            <h2>Your Orders</h2>
            {orders.length === 0 ? (
              <p>No orders yet</p>
            ) : (
              <div className="order-list">
                {orders.map(order => (
                  <div key={order.order_id} className="order-card">
                    <h3>Order ID: {order.order_id}</h3>
                    <p>Status: {order.status}</p>
                    <div className="order-items">
                      {order.items.map(item => (
                        <div key={item.id} className="order-item">
                          <span>{item.name}</span>
                          <span>Qty: {item.quantity}</span>
                          <span>${item.price * item.quantity}</span>
                        </div>
                      ))}
                    </div>
                    <p className="order-total">
                      Total: ${order.items.reduce((sum, item) => sum + (item.price * item.quantity), 0)}
                    </p>
                    {order.status === 'created' && (
                      <button
                        onClick={() => processPayment(order.order_id)}
                        disabled={loading}
                        className="pay-btn"
                      >
                        Pay Now
                      </button>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}

export default App;