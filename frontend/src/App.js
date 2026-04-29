import React, { useEffect, useState } from 'react';
import { Routes, Route, useNavigate, Navigate } from 'react-router-dom';
import './App.css';
import Navigation from './components/Navigation';
import ProductList from './components/ProductList';
import Cart from './components/Cart';
import OrderHistory from './components/OrderHistory';
import Wishlist from './components/Wishlist';
import Toast from './components/Toast';
import QuickViewModal from './components/QuickViewModal';
import useProducts from './hooks/useProducts';
import useCart from './hooks/useCart';
import useOrders from './hooks/useOrders';
import useRecommendations from './hooks/useRecommendations';
import useWishlist from './hooks/useWishlist';
import { useAuth0 } from "@auth0/auth0-react";

const APP_NAME = 'MyStore';

function App() {
  const { isLoading } = useAuth0();

  
  const {
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
    placeOrder,
    processPayment,
  } = useOrders();

  const { recommendations, showRecommendations } = useRecommendations(cart);
  const { wishlist, toggleWishlist, isInWishlist } = useWishlist();

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

  const handlePlaceOrder = async () => {
    if (cart.length === 0) {
      addToast('Cart is empty', 'error');
      return;
    }

    const items = cart.map((item) => ({ id: item.id }));
    const data = await placeOrder(items);

    if (data.status === 'success') {
      adjustProductStock(cart);
      navigate('/orders');
      addToast('Order placed successfully!', 'success');
    } else {
      addToast(data.message || 'Order placement failed', 'error');
    }
  };

  const handleProcessPayment = async (orderId) => {
    const order = orders.find((o) => o.order_id === orderId);
    if (!order) return;

    const total = order.items.reduce((sum, item) => sum + item.price * item.quantity, 0);
    const data = await processPayment(orderId, total);

    if (data.status === 'success') {
      addToast('Payment successful!', 'success');
    } else {
      addToast(data.message || 'Payment failed', 'error');
    }
  };

  const handleAddToCart = async (productId) => {
    const data = await addToCart(productId);
    if (data && data.status === 'success') {
      addToast('Item added to cart', 'success');
    } else {
      addToast(data?.message || 'Failed to add item', 'error');
    }
  };
  
  return (
    <div className="App">
      <Navigation 
        cartItemCount={getCartItemCount()} 
        wishlistCount={wishlist.length} 
        onOpenCart={() => setIsCartOpen(true)}
        searchQuery={searchQuery}
        setSearchQuery={setSearchQuery}
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
            />
          } />
        </Routes>
      </main>

      <Cart
        cart={cart}
        loading={loading}
        removeFromCart={removeFromCart}
        placeOrder={handlePlaceOrder}
        cartTotal={getCartTotal()}
        isOpen={isCartOpen}
        onClose={() => setIsCartOpen(false)}
      />

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