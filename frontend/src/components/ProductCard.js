import React, { useState } from 'react';
import './ProductCard.css';

// Build a human-readable label for a product variant
const getVariantLabel = (variant) => {
  if (variant.capacity)   return variant.capacity;
  if (variant.weight)     return variant.weight;
  if (variant.resistance) return variant.resistance;
  const parts = [];
  if (variant.size)  parts.push(variant.size);
  if (variant.color) parts.push(variant.color);
  return parts.length > 0 ? parts.join(' - ') : 'Standard';
};

function ProductCard({ product, addToCart, loading, toggleWishlist, isWishlisted, index, onQuickView }) {
  const [selectedVariant, setSelectedVariant] = useState(null);
  const [showVariantSelector, setShowVariantSelector] = useState(false);

  const hasVariants = product.variants && product.variants.length > 0;

  const handleAddToCart = () => {
    if (hasVariants && !selectedVariant) {
      setShowVariantSelector(true);
      return;
    }
    addToCart(product.id, selectedVariant?.variant_id);
    setSelectedVariant(null);
    setShowVariantSelector(false);
  };

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
      
      {/* Product Image */}
      <div 
        style={{ 
          width: '100%', 
          height: '200px', 
          background: '#f0f0f0', 
          borderRadius: '8px', 
          marginBottom: '12px',
          overflow: 'hidden',
          cursor: 'pointer'
        }}
        onClick={() => onQuickView && onQuickView(product)}
      >
        <img 
          src={product.image_url || 'https://via.placeholder.com/400x400?text=No+Image'} 
          alt={product.name}
          style={{ 
            width: '100%', 
            height: '100%', 
            objectFit: 'cover',
            transition: 'transform 0.2s'
          }}
          onMouseEnter={(e) => e.target.style.transform = 'scale(1.05)'}
          onMouseLeave={(e) => e.target.style.transform = 'scale(1)'}
        />
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
          {product.stock_quantity !== undefined && (
            <span className={`product-stock ${product.stock_quantity > 0 ? 'in-stock' : 'out-of-stock'}`}>
              {product.stock_quantity > 0 ? `In Stock (${product.stock_quantity})` : 'Out of Stock'}
            </span>
          )}
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

      {/* Variant Selector (inline) */}
      {hasVariants && showVariantSelector && (
        <div style={{ marginBottom: '8px', padding: '8px', background: '#f9f9f9', borderRadius: '4px' }}>
          <label style={{ display: 'block', marginBottom: '6px', fontSize: '0.85rem', fontWeight: '500' }}>
            Select Variant:
          </label>
          <select 
            value={selectedVariant?.variant_id || ''}
            onChange={(e) => {
              const variant = product.variants.find(v => v.variant_id === e.target.value);
              setSelectedVariant(variant);
            }}
            style={{
              width: '100%',
              padding: '6px',
              borderRadius: '4px',
              border: '1px solid #ddd',
              fontSize: '13px',
              marginBottom: '6px'
            }}
          >
            <option value="">-- Choose variant --</option>
            {product.variants.map((variant) => (
                <option key={variant.variant_id} value={variant.variant_id}>
                  {getVariantLabel(variant)} (₹{variant.price.toLocaleString('en-IN')})
                </option>
              ))}
          </select>
          <button
            onClick={() => setShowVariantSelector(false)}
            style={{
              width: '100%',
              padding: '4px',
              fontSize: '12px',
              background: '#f0f0f0',
              border: '1px solid #ddd',
              borderRadius: '4px',
              cursor: 'pointer'
            }}
          >
            Cancel
          </button>
        </div>
      )}

      <div className="card-actions-bottom" style={{ display: 'flex', gap: '8px' }}>
        <button
          className="btn-primary"
          onClick={handleAddToCart}
          disabled={loading || product.stock_quantity === 0}
          style={{ flex: 1 }}
        >
          {product.stock_quantity === 0 ? 'Out of Stock' : 'Add to Cart'}
        </button>
      </div>
    </div>
  );
}

export default ProductCard;
