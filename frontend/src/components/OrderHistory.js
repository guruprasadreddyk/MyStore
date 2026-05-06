import React, { useState } from 'react';
import './OrderHistory.css';

const STATUS_COLORS = {
  created:        '#f59e0b',
  confirmed:      '#3b82f6',
  processing:     '#8b5cf6',
  paid:           '#10b981',
  shipped:        '#06b6d4',
  delivered:      '#10b981',
  cancelled:      '#ef4444',
  return_pending: '#f59e0b',
  refunded:       '#10b981',
};

const fmt = (n) => `₹${Number(n).toLocaleString('en-IN')}`;

const REVIEWABLE_STATUSES = new Set(['delivered', 'shipped']);

// ── Star rating widget ────────────────────────────────────────────────────────
function StarRating({ rating, interactive, onChange }) {
  const [hovered, setHovered] = useState(0);
  return (
    <div style={{ display: 'flex', gap: '2px' }}>
      {[1, 2, 3, 4, 5].map(star => (
        <span
          key={star}
          onClick={() => interactive && onChange && onChange(star)}
          onMouseEnter={() => interactive && setHovered(star)}
          onMouseLeave={() => interactive && setHovered(0)}
          style={{
            fontSize: interactive ? '1.6rem' : '1.1rem',
            color: star <= (hovered || rating) ? '#fbbf24' : '#4b5563',
            cursor: interactive ? 'pointer' : 'default',
            lineHeight: 1,
            transition: 'color 0.1s',
          }}
        >
          ★
        </span>
      ))}
    </div>
  );
}

// ── Review modal ──────────────────────────────────────────────────────────────
function ReviewModal({ item, orderId, onSubmit, onClose, submitting }) {
  const [form, setForm] = useState({ rating: 5, title: '', comment: '' });
  const [error, setError] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!form.comment.trim()) {
      setError('Please write a comment');
      return;
    }
    setError('');
    onSubmit(item.id, form);
  };

  return (
    <div style={{
      position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.85)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      zIndex: 1100, padding: '20px',
    }}>
      <div style={{
        background: '#1a1a1a', borderRadius: '16px', padding: '32px',
        maxWidth: '480px', width: '100%', border: '1px solid rgba(255,255,255,0.1)',
      }}>
        <h3 style={{ marginBottom: '4px' }}>Review Product</h3>
        <p style={{ opacity: 0.5, fontSize: '0.85rem', marginBottom: '24px' }}>
          {item.name}
        </p>

        <form onSubmit={handleSubmit}>
          {/* Rating */}
          <div style={{ marginBottom: '20px' }}>
            <label style={{ display: 'block', marginBottom: '8px', fontSize: '0.85rem', opacity: 0.7 }}>
              Your Rating *
            </label>
            <StarRating
              rating={form.rating}
              interactive
              onChange={(r) => setForm(f => ({ ...f, rating: r }))}
            />
          </div>

          {/* Title */}
          <div style={{ marginBottom: '16px' }}>
            <label style={{ display: 'block', marginBottom: '8px', fontSize: '0.85rem', opacity: 0.7 }}>
              Title <span style={{ opacity: 0.4 }}>(optional)</span>
            </label>
            <input
              type="text"
              value={form.title}
              onChange={(e) => setForm(f => ({ ...f, title: e.target.value }))}
              placeholder="Sum up your experience"
              maxLength={200}
              style={{
                width: '100%', padding: '10px 12px', boxSizing: 'border-box',
                background: 'rgba(255,255,255,0.07)', border: '1px solid rgba(255,255,255,0.12)',
                borderRadius: '8px', color: '#fff', fontSize: '0.9rem',
              }}
            />
          </div>

          {/* Comment */}
          <div style={{ marginBottom: '20px' }}>
            <label style={{ display: 'block', marginBottom: '8px', fontSize: '0.85rem', opacity: 0.7 }}>
              Comment *
            </label>
            <textarea
              value={form.comment}
              onChange={(e) => setForm(f => ({ ...f, comment: e.target.value }))}
              placeholder="Share your experience with this product"
              rows={4}
              required
              style={{
                width: '100%', padding: '10px 12px', boxSizing: 'border-box',
                background: 'rgba(255,255,255,0.07)', border: '1px solid rgba(255,255,255,0.12)',
                borderRadius: '8px', color: '#fff', fontSize: '0.9rem', resize: 'vertical',
              }}
            />
            {error && (
              <p style={{ color: '#ef4444', fontSize: '0.8rem', marginTop: '6px' }}>{error}</p>
            )}
          </div>

          <div style={{ display: 'flex', gap: '12px' }}>
            <button
              type="submit"
              disabled={submitting}
              className="btn-primary"
              style={{ flex: 1, padding: '12px' }}
            >
              {submitting ? 'Submitting…' : 'Submit Review'}
            </button>
            <button
              type="button"
              onClick={onClose}
              disabled={submitting}
              style={{
                flex: 1, padding: '12px', background: 'rgba(255,255,255,0.05)',
                border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px',
                color: '#fff', cursor: 'pointer',
              }}
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ── Main component ────────────────────────────────────────────────────────────
function OrderHistory({ orders, loading, processPayment, cancelOrder, requestReturn, submitReview }) {
  const [expanded, setExpanded]           = useState(null);
  const [returnReason, setReturnReason]   = useState('');
  const [showReturnModal, setShowReturnModal] = useState(null);
  const [reviewModal, setReviewModal]     = useState(null); // { item, orderId }
  const [submittingReview, setSubmittingReview] = useState(false);
  // Track which product IDs have been reviewed this session
  const [reviewedItems, setReviewedItems] = useState(new Set());
  const [reviewMessage, setReviewMessage] = useState({ id: null, text: '', ok: true });

  if (loading) return <div style={{ padding: '40px', opacity: 0.5 }}>Loading orders…</div>;

  const handleSubmitReview = async (productId, formData) => {
    if (!submitReview) return;
    setSubmittingReview(true);
    try {
      const data = await submitReview(productId, formData);
      if (data.status === 'success') {
        setReviewedItems(prev => new Set([...prev, String(productId)]));
        setReviewMessage({ id: productId, text: 'Review submitted! ✅', ok: true });
        setReviewModal(null);
      } else {
        setReviewMessage({ id: productId, text: data.message || 'Failed to submit review', ok: false });
        setReviewModal(null);
      }
    } finally {
      setSubmittingReview(false);
      // Clear message after 4 s
      setTimeout(() => setReviewMessage({ id: null, text: '', ok: true }), 4000);
    }
  };

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
            const canReview      = REVIEWABLE_STATUSES.has(order.status);

            return (
              <div key={order.order_id} style={{
                background: 'rgba(255,255,255,0.04)',
                border: '1px solid rgba(255,255,255,0.08)',
                borderRadius: '12px', overflow: 'hidden',
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
                      fontSize: '0.8rem', fontWeight: 600, textTransform: 'capitalize',
                    }}>
                      {order.status?.replace('_', ' ')}
                    </span>
                    <span style={{ opacity: 0.4, fontSize: '0.85rem' }}>{isExpanded ? '▲' : '▼'}</span>
                  </div>
                </div>

                {/* ── Expanded detail ───────────────────────────────────── */}
                {isExpanded && (
                  <div style={{ padding: '0 20px 20px', borderTop: '1px solid rgba(255,255,255,0.06)' }}>

                    {/* Items */}
                    <h4 style={{ margin: '16px 0 10px', fontSize: '0.85rem', opacity: 0.6, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Items</h4>
                    {order.items.map(item => {
                      const alreadyReviewed = reviewedItems.has(String(item.id));
                      const msg = reviewMessage.id === item.id ? reviewMessage : null;

                      return (
                        <div key={`${item.id}-${item.variant_id || ''}`} style={{
                          display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                          padding: '8px 0', borderBottom: '1px solid rgba(255,255,255,0.04)',
                        }}>
                          <div style={{ flex: 1 }}>
                            <span style={{ fontSize: '0.9rem' }}>
                              {item.name} <span style={{ opacity: 0.5 }}>× {item.quantity}</span>
                            </span>
                            {/* Inline review feedback */}
                            {msg && (
                              <p style={{
                                fontSize: '0.78rem', marginTop: '4px',
                                color: msg.ok ? '#10b981' : '#ef4444',
                              }}>
                                {msg.text}
                              </p>
                            )}
                          </div>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                            <span style={{ fontSize: '0.9rem' }}>{fmt(item.price * item.quantity)}</span>
                            {/* Review button — only on reviewable orders */}
                            {canReview && !alreadyReviewed && (
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  setReviewModal({ item, orderId: order.order_id });
                                }}
                                title="Write a review for this product"
                                style={{
                                  padding: '4px 10px', fontSize: '0.78rem', fontWeight: 600,
                                  background: 'rgba(251,191,36,0.1)', border: '1px solid rgba(251,191,36,0.4)',
                                  borderRadius: '6px', color: '#fbbf24', cursor: 'pointer',
                                  whiteSpace: 'nowrap',
                                }}
                              >
                                ★ Review
                              </button>
                            )}
                            {canReview && alreadyReviewed && (
                              <span style={{ fontSize: '0.78rem', color: '#10b981', opacity: 0.8 }}>✓ Reviewed</span>
                            )}
                          </div>
                        </div>
                      );
                    })}

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
                            color: '#ef4444', cursor: 'pointer', fontSize: '0.9rem',
                          }}
                        >
                          Cancel Order
                        </button>
                      </div>
                    )}

                    {/* Return button for delivered orders */}
                    {order.status === 'delivered' && (
                      <div style={{ marginTop: '20px' }}>
                        <button
                          onClick={() => setShowReturnModal(order.order_id)}
                          disabled={loading}
                          style={{
                            padding: '12px 24px', background: 'rgba(251,191,36,0.1)',
                            border: '1px solid #fbbf24', borderRadius: '8px',
                            color: '#fbbf24', cursor: 'pointer', fontSize: '0.9rem', fontWeight: 600,
                          }}
                        >
                          Request Return
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

      {/* ── Return Modal ──────────────────────────────────────────────────── */}
      {showReturnModal && (
        <div style={{
          position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.8)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          zIndex: 1000, padding: '20px',
        }}>
          <div style={{
            background: '#1a1a1a', borderRadius: '16px', padding: '32px',
            maxWidth: '500px', width: '100%', border: '1px solid rgba(255,255,255,0.1)',
          }}>
            <h3 style={{ marginBottom: '20px' }}>Request Return</h3>
            <p style={{ opacity: 0.7, marginBottom: '20px', fontSize: '0.9rem' }}>
              Please select a reason for returning this order:
            </p>

            <select
              value={returnReason}
              onChange={(e) => setReturnReason(e.target.value)}
              style={{
                width: '100%', padding: '12px', borderRadius: '8px',
                background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)',
                color: '#fff', fontSize: '0.95rem', marginBottom: '24px',
              }}
            >
              <option value="">Select a reason…</option>
              <option value="defective">Product is defective</option>
              <option value="wrong_item">Wrong item received</option>
              <option value="not_as_described">Not as described</option>
              <option value="changed_mind">Changed my mind</option>
            </select>

            <div style={{ display: 'flex', gap: '12px' }}>
              <button
                onClick={() => {
                  if (!returnReason) { alert('Please select a reason for return'); return; }
                  requestReturn(showReturnModal, returnReason);
                  setShowReturnModal(null);
                  setReturnReason('');
                }}
                disabled={!returnReason || loading}
                className="btn-primary"
                style={{ flex: 1, padding: '12px' }}
              >
                Submit Return Request
              </button>
              <button
                onClick={() => { setShowReturnModal(null); setReturnReason(''); }}
                style={{
                  flex: 1, padding: '12px', background: 'rgba(255,255,255,0.05)',
                  border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px',
                  color: '#fff', cursor: 'pointer',
                }}
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── Review Modal ──────────────────────────────────────────────────── */}
      {reviewModal && (
        <ReviewModal
          item={reviewModal.item}
          orderId={reviewModal.orderId}
          onSubmit={handleSubmitReview}
          onClose={() => setReviewModal(null)}
          submitting={submittingReview}
        />
      )}
    </div>
  );
}

export default OrderHistory;
