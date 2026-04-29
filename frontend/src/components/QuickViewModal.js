import React from 'react';
import './Modals.css';

function QuickViewModal({ product, onClose, addToCart, loading }) {
  if (!product) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content fade-in-up" onClick={(e) => e.stopPropagation()}>
        <button className="modal-close" onClick={onClose}>&times;</button>
        <div className="modal-body">
          <div className="modal-image-placeholder">
            <span className="modal-category-badge">{product.category}</span>
          </div>
          <div className="modal-details">
            <h2 className="modal-title">{product.name}</h2>
            <p className="modal-price">${product.price.toLocaleString()}</p>
            <div className="modal-rating">⭐ {product.rating}/5</div>
            <p className="modal-description">{product.description}</p>
            
            <div className="modal-stock">
              <span className={`product-stock ${product.stock_quantity > 0 ? 'in-stock' : 'out-of-stock'}`}>
                {product.stock_quantity > 0 ? `In Stock (${product.stock_quantity})` : 'Out of Stock'}
              </span>
            </div>

            <button
              className="btn-primary modal-add-btn"
              onClick={() => {
                addToCart(product.id);
                onClose();
              }}
              disabled={loading || product.stock_quantity <= 0}
            >
              {product.stock_quantity > 0 ? 'Add to Cart' : 'Out of Stock'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default QuickViewModal;
