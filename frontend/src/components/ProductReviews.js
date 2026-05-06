import React, { useState, useEffect } from 'react';
import { useAuth0 } from '@auth0/auth0-react';
import { API_BASE } from '../services/api';

function ProductReviews({ productId }) {
  const { isAuthenticated, getAccessTokenSilently, loginWithRedirect } = useAuth0();
  const [reviews, setReviews] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({ rating: 5, title: '', comment: '' });
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState('');

  useEffect(() => {
    loadReviews();
  }, [productId]);

  const loadReviews = async () => {
    try {
      const res = await fetch(`${API_BASE}/products/${productId}/reviews`);
      const data = await res.json();
      if (data.status === 'success') {
        setReviews(data.data.reviews || []);
      }
    } catch (error) {
      console.error('Error loading reviews:', error);
    } finally {
      setLoading(false);
    }
  };

  const submitReview = async (e) => {
    e.preventDefault();
    
    if (!isAuthenticated) {
      loginWithRedirect();
      return;
    }

    if (!formData.comment.trim()) {
      setMessage('Please write a comment');
      return;
    }

    setSubmitting(true);
    setMessage('');

    try {
      const token = await getAccessTokenSilently();
      const res = await fetch(`${API_BASE}/products/${productId}/reviews`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(formData)
      });

      const data = await res.json();
      
      if (data.status === 'success') {
        setMessage('Review submitted successfully! ✅');
        setFormData({ rating: 5, title: '', comment: '' });
        setShowForm(false);
        loadReviews();
      } else {
        setMessage(data.message || 'Failed to submit review');
      }
    } catch (error) {
      console.error('Error submitting review:', error);
      setMessage('Failed to submit review');
    } finally {
      setSubmitting(false);
    }
  };

  const markHelpful = async (reviewId) => {
    try {
      await fetch(`${API_BASE}/reviews/${reviewId}/helpful`, { method: 'PUT' });
      loadReviews();
    } catch (error) {
      console.error('Error marking helpful:', error);
    }
  };

  const deleteReview = async (reviewId) => {
    if (!window.confirm('Delete this review?')) return;

    try {
      const token = await getAccessTokenSilently();
      const res = await fetch(`${API_BASE}/reviews/${reviewId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      const data = await res.json();
      if (data.status === 'success') {
        setMessage('Review deleted ✅');
        loadReviews();
      }
    } catch (error) {
      console.error('Error deleting review:', error);
    }
  };

  const StarRating = ({ rating, interactive, onChange }) => {
    return (
      <div style={{ display: 'flex', gap: '4px' }}>
        {[1, 2, 3, 4, 5].map(star => (
          <span
            key={star}
            onClick={() => interactive && onChange && onChange(star)}
            style={{
              fontSize: '1.5rem',
              color: star <= rating ? '#fbbf24' : '#4b5563',
              cursor: interactive ? 'pointer' : 'default'
            }}
          >
            ★
          </span>
        ))}
      </div>
    );
  };

  if (loading) return <div style={{ padding: '20px', opacity: 0.5 }}>Loading reviews...</div>;

  return (
    <div style={{ padding: '24px 0' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <h3>Customer Reviews ({reviews.length})</h3>
        {!showForm && (
          <button
            onClick={() => isAuthenticated ? setShowForm(true) : loginWithRedirect()}
            style={{
              padding: '8px 16px',
              background: '#3b82f6',
              border: 'none',
              borderRadius: '8px',
              color: '#fff',
              cursor: 'pointer',
              fontSize: '0.9rem'
            }}
          >
            Write a Review
          </button>
        )}
      </div>

      {message && (
        <div style={{
          padding: '12px',
          marginBottom: '16px',
          background: message.includes('✅') ? 'rgba(16,185,129,0.1)' : 'rgba(239,68,68,0.1)',
          border: `1px solid ${message.includes('✅') ? '#10b981' : '#ef4444'}`,
          borderRadius: '8px',
          color: message.includes('✅') ? '#10b981' : '#ef4444'
        }}>
          {message}
        </div>
      )}

      {showForm && (
        <form onSubmit={submitReview} style={{
          background: 'rgba(255,255,255,0.05)',
          border: '1px solid rgba(255,255,255,0.1)',
          borderRadius: '12px',
          padding: '20px',
          marginBottom: '24px'
        }}>
          <h4 style={{ marginBottom: '16px' }}>Write Your Review</h4>
          
          <div style={{ marginBottom: '16px' }}>
            <label style={{ display: 'block', marginBottom: '8px', fontSize: '0.9rem', opacity: 0.7 }}>
              Rating
            </label>
            <StarRating
              rating={formData.rating}
              interactive
              onChange={(rating) => setFormData({ ...formData, rating })}
            />
          </div>

          <div style={{ marginBottom: '16px' }}>
            <label style={{ display: 'block', marginBottom: '8px', fontSize: '0.9rem', opacity: 0.7 }}>
              Title (optional)
            </label>
            <input
              type="text"
              value={formData.title}
              onChange={(e) => setFormData({ ...formData, title: e.target.value })}
              placeholder="Sum up your experience"
              style={{
                width: '100%',
                padding: '10px 12px',
                background: 'rgba(255,255,255,0.08)',
                border: '1px solid rgba(255,255,255,0.15)',
                borderRadius: '8px',
                color: '#fff',
                fontSize: '0.9rem'
              }}
            />
          </div>

          <div style={{ marginBottom: '16px' }}>
            <label style={{ display: 'block', marginBottom: '8px', fontSize: '0.9rem', opacity: 0.7 }}>
              Comment *
            </label>
            <textarea
              value={formData.comment}
              onChange={(e) => setFormData({ ...formData, comment: e.target.value })}
              placeholder="Share your experience with this product"
              required
              rows={4}
              style={{
                width: '100%',
                padding: '10px 12px',
                background: 'rgba(255,255,255,0.08)',
                border: '1px solid rgba(255,255,255,0.15)',
                borderRadius: '8px',
                color: '#fff',
                fontSize: '0.9rem',
                resize: 'vertical'
              }}
            />
          </div>

          <div style={{ display: 'flex', gap: '12px' }}>
            <button
              type="submit"
              disabled={submitting}
              className="btn-primary"
              style={{ padding: '10px 20px' }}
            >
              {submitting ? 'Submitting...' : 'Submit Review'}
            </button>
            <button
              type="button"
              onClick={() => setShowForm(false)}
              style={{
                padding: '10px 20px',
                background: 'transparent',
                border: '1px solid rgba(255,255,255,0.2)',
                borderRadius: '8px',
                color: '#fff',
                cursor: 'pointer'
              }}
            >
              Cancel
            </button>
          </div>
        </form>
      )}

      {reviews.length === 0 ? (
        <p style={{ opacity: 0.5, textAlign: 'center', padding: '40px 0' }}>
          No reviews yet. Be the first to review this product!
        </p>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {reviews.map(review => (
            <div
              key={review.review_id}
              style={{
                background: 'rgba(255,255,255,0.03)',
                border: '1px solid rgba(255,255,255,0.08)',
                borderRadius: '12px',
                padding: '16px'
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '12px' }}>
                <div>
                  <StarRating rating={review.rating} />
                  {review.title && (
                    <h4 style={{ margin: '8px 0 4px', fontSize: '1rem' }}>{review.title}</h4>
                  )}
                  <p style={{ fontSize: '0.8rem', opacity: 0.5 }}>
                    {review.user_email?.split('@')[0]} • {new Date(review.created_at).toLocaleDateString()}
                  </p>
                </div>
              </div>

              <p style={{ marginBottom: '12px', lineHeight: 1.6 }}>{review.comment}</p>

              <div style={{ display: 'flex', gap: '12px', fontSize: '0.85rem' }}>
                <button
                  onClick={() => markHelpful(review.review_id)}
                  style={{
                    padding: '4px 12px',
                    background: 'rgba(59,130,246,0.1)',
                    border: '1px solid rgba(59,130,246,0.3)',
                    borderRadius: '6px',
                    color: '#3b82f6',
                    cursor: 'pointer'
                  }}
                >
                  👍 Helpful ({review.helpful_count || 0})
                </button>
                
                {isAuthenticated && (
                  <button
                    onClick={() => deleteReview(review.review_id)}
                    style={{
                      padding: '4px 12px',
                      background: 'rgba(239,68,68,0.1)',
                      border: '1px solid rgba(239,68,68,0.3)',
                      borderRadius: '6px',
                      color: '#ef4444',
                      cursor: 'pointer'
                    }}
                  >
                    Delete
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default ProductReviews;
