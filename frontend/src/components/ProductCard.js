import React from 'react';

function ProductCard({ product, addToCart, loading, toggleWishlist, isWishlisted, index, onQuickView }) {
  return (
    <div className="product-card">
      <div className="product-actions-top">
        <button 
          className={`wishlist-btn ${isWishlisted ? 'active' : ''}`}
          onClick={() => toggleWishlist(product)}
          aria-label="Toggle Wishlist"
        >
          {isWishlisted ? '❤️' : '🤍'}
        </button>
      </div>
      <div 
        style={{ flexGrow: 1, cursor: 'pointer' }} 
        onClick={() => onQuickView && onQuickView(product)}
      >
        <h3>{product.name}</h3>
        <p className="product-category">{product.category}</p>
        <p className="product-description">{product.description}</p>
        <div className="product-details">
          <span className="product-price">₹{product.price.toLocaleString('en-IN')}</span>
          <span className={`product-stock ${product.stock_quantity > 0 ? 'in-stock' : 'out-of-stock'}`}>
            {product.stock_quantity > 0 ? `In Stock (${product.stock_quantity})` : 'Out of Stock'}
          </span>
        </div>
        <div className="product-rating">
          ⭐ {product.rating}/5
          {product.review_count && (
            <span style={{ fontSize: '0.75rem', opacity: 0.6, marginLeft: '6px' }}>
              ({product.review_count.toLocaleString('en-IN')} reviews)
            </span>
          )}
        </div>
      </div>
      <div className="card-actions-bottom" style={{ display: 'flex', gap: '8px' }}>
        <button
          className="btn-primary"
          onClick={() => addToCart(product.id)}
          disabled={loading || product.stock_quantity <= 0}
          style={{ flex: 1 }}
        >
          {product.stock_quantity > 0 ? 'Add to Cart' : 'Out of Stock'}
        </button>
      </div>
    </div>
  );
}

export default ProductCard;
