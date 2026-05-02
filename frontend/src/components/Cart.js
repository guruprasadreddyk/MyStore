import React from 'react';
import './Modals.css';

function Cart({ cart, loading, removeFromCart, placeOrder, cartTotal, isOpen, onClose }) {
  return (
    <div className={`cart-overlay ${isOpen ? 'open' : ''}`} onClick={onClose}>
      <div className="cart-drawer" onClick={(e) => e.stopPropagation()}>
        <div className="cart-header">
          <h2>Your Cart</h2>
          <button className="modal-close" style={{position: 'static'}} onClick={onClose}>&times;</button>
        </div>
        
        <div className="cart-body">
          {cart.length === 0 ? (
            <p style={{ color: 'var(--text-secondary)' }}>Your cart is empty.</p>
          ) : (
            <div className="cart-items">
              {cart.map(item => (
                <div key={item.id} className="cart-item" style={{ padding: '16px', marginBottom: '16px', background: 'rgba(255,255,255,0.02)' }}>
                  <h3 style={{ fontSize: '1.2rem' }}>{item.name}</h3>
                  <div style={{ display: 'flex', justifyContent: 'space-between', margin: '12px 0' }}>
                    <span>₹{item.price.toLocaleString('en-IN')}</span>
                    <span>Qty: {item.quantity}</span>
                  </div>
                  <button
                    onClick={() => removeFromCart(item.id)}
                    disabled={loading}
                    style={{ padding: '8px 16px', fontSize: '0.85rem' }}
                  >
                    Remove
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        {cart.length > 0 && (
          <div className="cart-footer">
            <h3 style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '24px' }}>
              <span>Total:</span>
              <span>₹{cartTotal.toLocaleString('en-IN')}</span>
            </h3>
            <button
              onClick={() => {
                placeOrder();
                onClose();
              }}
              disabled={loading}
              className="btn-primary"
              style={{ width: '100%', padding: '16px' }}
            >
              Checkout Now
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

export default Cart;
