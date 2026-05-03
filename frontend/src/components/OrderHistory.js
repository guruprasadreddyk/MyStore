import React, { useState } from 'react';

const STATUS_COLORS = {
  created:      '#f59e0b',
  confirmed:    '#3b82f6',
  processing:   '#8b5cf6',
  paid:         '#10b981',
  shipped:      '#06b6d4',
  delivered:    '#10b981',
  cancelled:    '#ef4444',
};

const fmt = (n) => `₹${Number(n).toLocaleString('en-IN')}`;

function OrderHistory({ orders, loading, processPayment, cancelOrder }) {
  const [expanded, setExpanded] = useState(null);

  if (loading) return <div style={{ padding: '40px', opacity: 0.5 }}>Loading orders...</div>;

  return (
    <div className="orders" style={{ maxWidth: '800px', margin: '0 auto', padding: '32px 24px' }}>
      <h2 style={{ marginBottom: '24px' }}>Your Orders</h2>

      {orders.length === 0 ? (
        <p style={{ opacity: 0.5 }}>No orders yet. Start shopping!</p>
      ) : (
        <div className="order-list" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {orders.map(order => {
            const subtotal       = order.subtotal       ?? order.items.reduce((s, i) => s + i.price * i.quantity, 0);
            const deliveryCharge = order.delivery_charge ?? (subtotal >= 500 ? 0 : 49);
            const gst            = order.gst            ?? Math.round(subtotal * 0.18);
            const grandTotal     = order.grand_total    ?? (subtotal + deliveryCharge + gst);
            const isExpanded     = expanded === order.order_id;

            return (
              <div key={order.order_id} style={{
                background: 'rgba(255,255,255,0.04)',
                border: '1px solid rgba(255,255,255,0.08)',
                borderRadius: '12px',
                overflow: 'hidden'
              }}>
                {/* ── Order header ─────────────────────────────────────── */}
                <div
                  onClick={() => setExpanded(isExpanded ? null : order.order_id)}
                  style={{ padding: '16px 20px', cursor: 'pointer', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}
                >
                  <div>
                    <p style={{ fontSize: '0.75rem', opacity: 0.5, marginBottom: '4px' }}>
                      Order #{order.order_id?.slice(0, 8).toUpperCase()}
                    </p>
                    <p style={{ fontWeight: 600 }}>{fmt(grandTotal)}</p>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                    <span style={{
                      color: STATUS_COLORS[order.status] || '#fff',
                      background: `${STATUS_COLORS[order.status]}22`,
                      padding: '4px 10px', borderRadius: '20px',
                      fontSize: '0.8rem', fontWeight: 600, textTransform: 'capitalize'
                    }}>
                      {order.status}
                    </span>
                    <span style={{ opacity: 0.4, fontSize: '0.85rem' }}>{isExpanded ? '▲' : '▼'}</span>
                  </div>
                </div>

                {/* ── Expanded detail ───────────────────────────────────── */}
                {isExpanded && (
                  <div style={{ padding: '0 20px 20px', borderTop: '1px solid rgba(255,255,255,0.06)' }}>

                    {/* Items */}
                    <h4 style={{ margin: '16px 0 10px', fontSize: '0.85rem', opacity: 0.6, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Items</h4>
                    {order.items.map(item => (
                      <div key={item.id} style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0', fontSize: '0.9rem', borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
                        <span>{item.name} <span style={{ opacity: 0.5 }}>× {item.quantity}</span></span>
                        <span>{fmt(item.price * item.quantity)}</span>
                      </div>
                    ))}

                    {/* Pricing breakdown */}
                    <div style={{ marginTop: '16px', display: 'flex', flexDirection: 'column', gap: '6px', fontSize: '0.85rem' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', opacity: 0.6 }}>
                        <span>Subtotal</span><span>{fmt(subtotal)}</span>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', opacity: 0.6 }}>
                        <span>Delivery</span>
                        <span style={{ color: deliveryCharge === 0 ? '#10b981' : 'inherit' }}>
                          {deliveryCharge === 0 ? 'FREE' : fmt(deliveryCharge)}
                        </span>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', opacity: 0.6 }}>
                        <span>GST (18%)</span><span>{fmt(gst)}</span>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontWeight: 700, borderTop: '1px solid rgba(255,255,255,0.1)', paddingTop: '8px', marginTop: '4px' }}>
                        <span>Grand Total</span><span>{fmt(grandTotal)}</span>
                      </div>
                    </div>

                    {/* Delivery address */}
                    {order.address && (
                      <>
                        <h4 style={{ margin: '20px 0 8px', fontSize: '0.85rem', opacity: 0.6, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Delivery Address</h4>
                        <div style={{ fontSize: '0.85rem', opacity: 0.8, lineHeight: 1.6 }}>
                          <p style={{ fontWeight: 600 }}>{order.address.full_name}</p>
                          <p>{order.address.address_line1}{order.address.address_line2 ? `, ${order.address.address_line2}` : ''}</p>
                          <p>{order.address.city}, {order.address.state} – {order.address.pincode}</p>
                          <p>📞 {order.address.phone}</p>
                        </div>
                      </>
                    )}

                    {/* Pay Now / Cancel buttons */}
                    {order.status === 'created' && (
                      <div style={{ display: 'flex', gap: '12px', marginTop: '20px' }}>
                        <button
                          onClick={() => processPayment(order.order_id)}
                          disabled={loading}
                          className="btn-primary"
                          style={{ padding: '12px 24px' }}
                        >
                          Pay Now · {fmt(grandTotal)}
                        </button>
                        <button
                          onClick={() => {
                            if (window.confirm('Cancel this order? This cannot be undone.')) {
                              cancelOrder(order.order_id);
                            }
                          }}
                          disabled={loading}
                          style={{
                            padding: '12px 20px', background: 'rgba(239,68,68,0.1)',
                            border: '1px solid #ef4444', borderRadius: '8px',
                            color: '#ef4444', cursor: 'pointer', fontSize: '0.9rem'
                          }}
                        >
                          Cancel Order
                        </button>
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

export default OrderHistory;
