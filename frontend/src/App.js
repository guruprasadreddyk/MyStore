import React, { useEffect, useState } from 'react';
import { Routes, Route, useNavigate, Navigate } from 'react-router-dom';
import './App.css';
import Navigation from './components/Navigation';
import ProductList from './components/ProductList';
import Cart from './components/Cart';
import Checkout from './components/Checkout';
import OrderHistory from './components/OrderHistory';
import Wishlist from './components/Wishlist';
import Toast from './components/Toast';
import QuickViewModal from './components/QuickViewModal';
import AdminPanel from './components/AdminPanel';
import ProfilePage from './components/ProfilePage';
import AddressesPage from './components/AddressesPage';
import PaymentMethodsPage from './components/PaymentMethodsPage';
import NotificationsPage from './components/NotificationsPage';
import useProducts from './hooks/useProducts';
import useCart from './hooks/useCart';
import useOrders from './hooks/useOrders';
import useRecommendations from './hooks/useRecommendations';
import useWishlist from './hooks/useWishlist';
import { useAuth0 } from "@auth0/auth0-react";
import { apiFetch, getHeaders } from './services/api';

const APP_NAME = 'MyStore';

function App() {
  const { isLoading, isAuthenticated, getAccessTokenSilently } = useAuth0();

  
  const {
    products,
    filteredProducts,
    categories,
    loading: productsLoading,
    searchQuery,
    setSearchQuery,
    selectedCategory,
    setSelectedCategory,
    minPrice,
    setMinPrice,
    maxPrice,
    setMaxPrice,
    minRating,
    setMinRating,
    inStockOnly,
    setInStockOnly,
    sortBy,
    setSortBy,
    lastEvaluatedKey,
    fetchProducts,
    adjustProductStock,
  } = useProducts();

  const {
    cart,
    loading: cartLoading,
    addToCart,
    removeFromCart,
    getCartTotal,
    getCartItemCount,
  } = useCart();

  const {
    orders,
    loading: ordersLoading,
    loadOrders,
    placeOrder,
    processPayment,
    cancelOrder,
    submitReview,
  } = useOrders();

  const { wishlist, toggleWishlist, isInWishlist } = useWishlist();
  const { recommendations, showRecommendations } = useRecommendations(cart, orders, wishlist, searchQuery);

  const handleToggleWishlist = async (product) => {
    const res = await toggleWishlist(product);
    if (res && res.status === 'error') {
      addToast(res.message || 'Failed to update wishlist', 'error');
    } else if (res && res.status === 'success') {
      addToast(res.message || 'Wishlist updated', 'success');
    }
  };

  const [toasts, setToasts] = useState([]);
  const [isCartOpen, setIsCartOpen] = useState(false);
  const [isCheckoutOpen, setIsCheckoutOpen] = useState(false);
  const [quickViewProduct, setQuickViewProduct] = useState(null);

  const addToast = (message, type = 'success') => {
    const id = Date.now();
    setToasts((prev) => [...prev, { id, message, type }]);
  };

  const removeToast = (id) => {
    setToasts((prev) => prev.filter((toast) => toast.id !== id));
  };

  const navigate = useNavigate();
  const loading = productsLoading || cartLoading || ordersLoading;

  useEffect(() => {
    document.title = APP_NAME;
  }, []);

  if (isLoading) {
    return <div>Loading authentication...</div>;
  }

  const handlePlaceOrder = async ({ address, grandTotal, paymentComplete }) => {
    if (paymentComplete) {
      setIsCheckoutOpen(false);
      await loadOrders();
      navigate('/orders');
      addToast('Order placed and payment confirmed!', 'success');
    }
  };

  const handleProcessPayment = async (orderId) => {
    const order = orders.find((o) => o.order_id === orderId);
    if (!order) return;

    // Use grand_total if available (includes GST + delivery), else fall back
    const total = order.grand_total
      ?? order.items.reduce((sum, item) => sum + item.price * item.quantity, 0);
    const data = await processPayment(orderId, total);

    if (data.status === 'success') {
      addToast('Payment successful!', 'success');
    } else {
      addToast(data.message || 'Payment failed', 'error');
    }
  };

  const handleCancelOrder = async (orderId) => {
    const data = await cancelOrder(orderId);
    if (data.status === 'success') {
      addToast('Order cancelled successfully', 'success');
    } else {
      addToast(data.message || 'Failed to cancel order', 'error');
    }
  };

  const handleRequestReturn = async (orderId, reason) => {
    try {
      const headers = await getHeaders(isAuthenticated, getAccessTokenSilently);
      const data = await apiFetch('/return', {
        method: 'POST',
        headers,
        body: { order_id: orderId, reason },
      });

      if (data.status === 'success') {
        addToast('Return request submitted successfully', 'success');
        setTimeout(() => { window.location.reload(); }, 1500);
      } else {
        addToast(data.message || 'Failed to submit return request', 'error');
      }
    } catch (error) {
      console.error('Return request error:', error);
      addToast('Failed to submit return request. Please try again.', 'error');
    }
  };

  const handleAddToCart = async (productId, variantId) => {
    const data = await addToCart(productId, variantId);
    if (data && data.status === 'success') {
      addToast('Item added to cart', 'success');
    } else {
      addToast(data?.message || 'Failed to add item', 'error');
    }
    return data; // return so Wishlist can check success before removing
  };
  
  return (
    <div className="App">
      <Navigation 
        cartItemCount={getCartItemCount()} 
        wishlistCount={wishlist.length} 
        onOpenCart={() => setIsCartOpen(true)}
        searchQuery={searchQuery}
        setSearchQuery={setSearchQuery}
        products={products}
      />
      <main>
        <Routes>
          <Route path="/" element={<Navigate to="/products" />} />
          <Route path="/products" element={
            <ProductList
              filteredProducts={filteredProducts}
              searchQuery={searchQuery}
              setSearchQuery={setSearchQuery}
              selectedCategory={selectedCategory}
              setSelectedCategory={setSelectedCategory}
              loading={loading}
              addToCart={handleAddToCart}
              categories={categories}
              fetchProducts={fetchProducts}
              lastEvaluatedKey={lastEvaluatedKey}
              minPrice={minPrice}
              setMinPrice={setMinPrice}
              maxPrice={maxPrice}
              setMaxPrice={setMaxPrice}
              minRating={minRating}
              setMinRating={setMinRating}
              inStockOnly={inStockOnly}
              setInStockOnly={setInStockOnly}
              sortBy={sortBy}
              setSortBy={setSortBy}
              recommendations={recommendations}
              showRecommendations={showRecommendations}
              toggleWishlist={handleToggleWishlist}
              isInWishlist={isInWishlist}
              onQuickView={setQuickViewProduct}
            />
          } />
          <Route path="/wishlist" element={
            <Wishlist
              wishlist={wishlist}
              toggleWishlist={handleToggleWishlist}
              addToCart={handleAddToCart}
              loading={loading}
              onQuickView={setQuickViewProduct}
            />
          } />
          <Route path="/orders" element={
            <OrderHistory
              orders={orders}
              loading={loading}
              processPayment={handleProcessPayment}
              cancelOrder={handleCancelOrder}
              requestReturn={handleRequestReturn}
              submitReview={submitReview}
            />
          } />
          <Route path="/admin" element={<AdminPanel />} />
          <Route path="/profile" element={<ProfilePage />} />
          <Route path="/addresses" element={<AddressesPage />} />
          <Route path="/payment-methods" element={<PaymentMethodsPage />} />
          <Route path="/notifications" element={<NotificationsPage orders={orders} />} />
        </Routes>
      </main>

      <Cart
        cart={cart}
        loading={loading}
        addToCart={handleAddToCart}
        removeFromCart={removeFromCart}
        onCheckout={() => { setIsCartOpen(false); setIsCheckoutOpen(true); }}
        cartTotal={getCartTotal()}
        isOpen={isCartOpen}
        onClose={() => setIsCartOpen(false)}
      />

      {isCheckoutOpen && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.85)', zIndex: 1000, overflowY: 'auto' }}>
          <Checkout
            cart={cart}
            onConfirm={handlePlaceOrder}
            onCancel={() => { setIsCheckoutOpen(false); setIsCartOpen(true); }}
            loading={cartLoading}
            addToast={addToast}
          />
        </div>
      )}

      <QuickViewModal
        product={quickViewProduct}
        onClose={() => setQuickViewProduct(null)}
        addToCart={handleAddToCart}
        loading={loading}
      />
      
      <div className="toast-container">
        {toasts.map((toast) => (
          <Toast
            key={toast.id}
            message={toast.message}
            type={toast.type}
            onClose={() => removeToast(toast.id)}
          />
        ))}
      </div>
    </div>
  );
}

export default App;