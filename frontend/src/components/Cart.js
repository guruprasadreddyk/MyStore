import React from 'react';
import './Cart.css';

const fmt = (n) => `₹${Number(n).toLocaleString('en-IN')}`;

function Cart({ cart, loading, addToCart, removeFromCart, onCheckout, cartTotal, isOpen, onClose }) {
  return (
    <div className={`cart-overlay ${isOpen ? 'open' : ''}`} onClick={onClose}>
      <div className="cart-drawer" onClick={(e) => e.stopPropagation()}>
        <div className="cart-header">
          <h2>Your Cart</h2>
          <button className="modal-close" style={{ position: 'static' }} onClick={onClose}>&times;</button>
        </div>

        <div className="cart-body">
          {cart.length === 0 ? (
            <p style={{ color: 'var(--text-secondary)' }}>Your cart is empty.</p>
          ) : (
            <div className="cart-items">
              {cart.map(item => (
                <div key={item.id} className="cart-item" style={{
                  padding: '14px 16px', marginBottom: '12px',
                  background: 'rgba(255,255,255,0.03)',
                  borderRadius: '10px', border: '1px solid rgba(255,255,255,0.06)'
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '10px' }}>
                    <h3 style={{ fontSize: '0.95rem', fontWeight: 600, flex: 1, marginRight: '8px' }}>{item.name}</h3>
                    <span style={{ fontWeight: 700, fontSize: '0.95rem', whiteSpace: 'nowrap' }}>
                      {fmt(item.price * item.quantity)}
                    </span>
                  </div>

                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    {/* Quantity controls */}
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0' }}>
                      <button
                        onClick={() => removeFromCart(item.id, item.variant_id || null)}
                        disabled={loading}
                        style={{
                          width: '30px', height: '30px', border: '1px solid rgba(255,255,255,0.2)',
                          borderRadius: '6px 0 0 6px', background: 'rgba(255,255,255,0.06)',
                          color: '#fff', cursor: 'pointer', fontSize: '1rem', lineHeight: 1
                        }}
                      >−</button>
                      <span style={{
                        width: '36px', height: '30px', display: 'flex', alignItems: 'center',
                        justifyContent: 'center', border: '1px solid rgba(255,255,255,0.2)',
                        borderLeft: 'none', borderRight: 'none',
                        fontSize: '0.9rem', fontWeight: 600
                      }}>
                        {item.quantity}
                      </span>
                      <button
                        onClick={() => addToCart(item.id, item.variant_id || null)}
                        disabled={loading}
                        style={{
                          width: '30px', height: '30px', border: '1px solid rgba(255,255,255,0.2)',
                          borderRadius: '0 6px 6px 0', background: 'rgba(255,255,255,0.06)',
                          color: '#fff', cursor: 'pointer', fontSize: '1rem', lineHeight: 1
                        }}
                      >+</button>
                    </div>

                    <span style={{ fontSize: '0.8rem', opacity: 0.5 }}>
                      {fmt(item.price)} each
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {cart.length > 0 && (
          <div className="cart-footer">
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', fontSize: '0.85rem', opacity: 0.6 }}>
              <span>Subtotal ({cart.reduce((s, i) => s + i.quantity, 0)} items)</span>
              <span>{fmt(cartTotal)}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '16px', fontSize: '0.75rem', opacity: 0.45 }}>
              <span>GST & delivery calculated at checkout</span>
            </div>
            <button
              onClick={onCheckout}
              disabled={loading}
              className="btn-primary"
              style={{ width: '100%', padding: '14px', fontSize: '1rem' }}
            >
              Proceed to Checkout
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

export default Cart;
