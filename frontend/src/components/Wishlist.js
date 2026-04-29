import React from 'react';
import ProductCard from './ProductCard';

function Wishlist({ wishlist, toggleWishlist, addToCart, loading, onQuickView }) {
  return (
    <div className="wishlist-page fade-in-up" style={{ padding: '40px 20px', maxWidth: '1400px', margin: '0 auto' }}>
      <h2 style={{ fontFamily: 'var(--font-display)', fontSize: '2.5rem', marginBottom: '24px' }}>My Wishlist</h2>
      {wishlist.length === 0 ? (
        <div className="empty-state glass-panel" style={{ textAlign: 'center', padding: '60px 20px' }}>
          <span style={{ fontSize: '3rem', display: 'block', marginBottom: '16px' }}>🤍</span>
          <p style={{ color: 'var(--text-secondary)', fontSize: '1.2rem' }}>Your wishlist is empty.</p>
        </div>
      ) : (
        <div className="product-grid">
          {wishlist.map((product) => (
            <ProductCard
              key={product.id}
              product={product}
              addToCart={addToCart}
              loading={loading}
              toggleWishlist={toggleWishlist}
              isWishlisted={true}
              index={0}
              onQuickView={onQuickView}
            />
          ))}
        </div>
      )}
    </div>
  );
}

export default Wishlist;
