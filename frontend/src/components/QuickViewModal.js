import React, { useState } from 'react';
import ProductReviews from './ProductReviews';
import './QuickViewModal.css';

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

function QuickViewModal({ product, onClose, addToCart, loading }) {
  const [selectedVariant, setSelectedVariant] = useState(null);
  const [activeTab, setActiveTab] = useState('details'); // 'details' or 'reviews'
  
  if (!product) return null;

  const hasVariants = product.variants && product.variants.length > 0;
  const displayPrice = selectedVariant 
    ? selectedVariant.price 
    : product.price;

  const handleAddToCart = () => {
    if (hasVariants && !selectedVariant) {
      alert('Please select a variant');
      return;
    }
    addToCart(product.id, selectedVariant?.variant_id);
    onClose();
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content fade-in-up" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '900px', maxHeight: '90vh', overflowY: 'auto' }}>
        <button className="modal-close" onClick={onClose}>&times;</button>
        <div className="modal-body">
          <div className="modal-image-placeholder" style={{ position: 'relative', overflow: 'hidden' }}>
            <img 
              src={product.image_url || 'https://via.placeholder.com/400x400?text=No+Image'} 
              alt={product.name}
              style={{ 
                width: '100%', 
                height: '100%', 
                objectFit: 'cover'
              }}
            />
            <span className="modal-category-badge">{product.category}</span>
          </div>
          <div className="modal-details">
            <h2 className="modal-title">{product.name}</h2>
            <p className="modal-price">₹{displayPrice.toLocaleString('en-IN')}</p>
            <div className="modal-rating">
              ⭐ {product.rating}/5
              {product.review_count && (
                <span style={{ fontSize: '0.8rem', opacity: 0.6, marginLeft: '8px' }}>
                  ({product.review_count.toLocaleString('en-IN')} reviews)
                </span>
              )}
            </div>
            
            {/* Tabs */}
            <div style={{ display: 'flex', gap: '16px', borderBottom: '1px solid rgba(255,255,255,0.1)', marginBottom: '16px' }}>
              <button
                onClick={() => setActiveTab('details')}
                style={{
                  padding: '8px 0',
                  background: 'transparent',
                  border: 'none',
                  borderBottom: activeTab === 'details' ? '2px solid #3b82f6' : '2px solid transparent',
                  color: activeTab === 'details' ? '#3b82f6' : 'rgba(255,255,255,0.6)',
                  cursor: 'pointer',
                  fontSize: '0.9rem',
                  fontWeight: activeTab === 'details' ? 600 : 400
                }}
              >
                Details
              </button>
              <button
                onClick={() => setActiveTab('reviews')}
                style={{
                  padding: '8px 0',
                  background: 'transparent',
                  border: 'none',
                  borderBottom: activeTab === 'reviews' ? '2px solid #3b82f6' : '2px solid transparent',
                  color: activeTab === 'reviews' ? '#3b82f6' : 'rgba(255,255,255,0.6)',
                  cursor: 'pointer',
                  fontSize: '0.9rem',
                  fontWeight: activeTab === 'reviews' ? 600 : 400
                }}
              >
                Reviews ({product.review_count || 0})
              </button>
            </div>

            {activeTab === 'details' ? (
              <>
                <p className="modal-description">{product.description}</p>
                
                {/* Variant Selector */}
                {hasVariants && (
                  <div className="variant-selector" style={{ marginBottom: '16px' }}>
                    <label style={{ display: 'block', marginBottom: '8px', fontWeight: '500' }}>
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
                        padding: '8px',
                        borderRadius: '4px',
                        border: '1px solid #ddd',
                        fontSize: '14px'
                      }}
                    >
                      <option value="">-- Choose a variant --</option>
                      {product.variants.map((variant) => (
                          <option key={variant.variant_id} value={variant.variant_id}>
                            {getVariantLabel(variant)} (₹{variant.price.toLocaleString('en-IN')})
                          </option>
                        ))}
                    </select>
                  </div>
                )}
                
                <div className="modal-stock">
                  <span className={`product-stock ${product.stock_quantity > 0 ? 'in-stock' : 'out-of-stock'}`}>
                    {product.stock_quantity > 0 ? `In Stock (${product.stock_quantity})` : 'Out of Stock'}
                  </span>
                </div>

                <button
                  className="btn-primary modal-add-btn"
                  onClick={handleAddToCart}
                  disabled={loading || product.stock_quantity <= 0 || (hasVariants && !selectedVariant)}
                >
                  {product.stock_quantity > 0 ? 'Add to Cart' : 'Out of Stock'}
                </button>
              </>
            ) : (
              <ProductReviews productId={product.id} />
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default QuickViewModal;
