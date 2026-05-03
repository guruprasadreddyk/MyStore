import React from 'react';
import { useAuth0 } from '@auth0/auth0-react';

// Display-only page — we never store real card data.
// Shows saved UPI and card placeholders with a note about security.

const MOCK_METHODS = [
  { id: 1, type: 'upi',  label: 'UPI',         detail: 'yourname@upi',      icon: '📱', default: true  },
  { id: 2, type: 'card', label: 'Visa Card',    detail: '**** **** **** 4242', icon: '💳', default: false },
];

function PaymentMethodsPage() {
  const { isAuthenticated, loginWithRedirect } = useAuth0();

  if (!isAuthenticated) return (
    <div style={{ padding: '60px 24px', textAlign: 'center' }}>
      <p style={{ opacity: 0.5, marginBottom: '16px' }}>Please log in to view payment methods.</p>
      <button className="btn-primary" style={{ width: 'auto', padding: '12px 32px' }} onClick={() => loginWithRedirect()}>Log In</button>
    </div>
  );

  return (
    <div style={{ maxWidth: '600px', margin: '0 auto', padding: '40px 24px' }}>
      <h2 style={{ marginBottom: '8px', fontSize: '1.6rem' }}>Payment Methods</h2>
      <p style={{ opacity: 0.45, fontSize: '0.85rem', marginBottom: '28px' }}>
        Your payment details are securely tokenised. We never store full card numbers.
      </p>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginBottom: '28px' }}>
        {MOCK_METHODS.map(m => (
          <div key={m.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'rgba(255,255,255,0.04)', border: `1px solid ${m.default ? 'rgba(59,130,246,0.4)' : 'rgba(255,255,255,0.08)'}`, borderRadius: '12px', padding: '16px 20px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
              <span style={{ fontSize: '1.5rem' }}>{m.icon}</span>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{ fontWeight: 600, fontSize: '0.9rem' }}>{m.label}</span>
                  {m.default && <span style={{ background: 'rgba(59,130,246,0.15)', border: '1px solid rgba(59,130,246,0.3)', color: '#60a5fa', fontSize: '0.7rem', padding: '2px 8px', borderRadius: '20px', fontWeight: 600 }}>DEFAULT</span>}
                </div>
                <p style={{ margin: 0, fontSize: '0.82rem', opacity: 0.5 }}>{m.detail}</p>
              </div>
            </div>
            <button style={{ padding: '5px 12px', background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)', borderRadius: '6px', color: '#ef4444', cursor: 'pointer', fontSize: '0.78rem' }}>
              Remove
            </button>
          </div>
        ))}
      </div>

      <div style={{ background: 'rgba(255,255,255,0.03)', border: '1px dashed rgba(255,255,255,0.12)', borderRadius: '12px', padding: '20px', textAlign: 'center', cursor: 'pointer', opacity: 0.6 }}
        onClick={() => alert('Payment gateway integration coming soon.')}>
        <p style={{ margin: 0, fontSize: '0.9rem' }}>+ Add Payment Method</p>
        <p style={{ margin: '4px 0 0', fontSize: '0.75rem', opacity: 0.6 }}>UPI, Credit / Debit Card, Net Banking</p>
      </div>

      <div style={{ marginTop: '24px', padding: '14px 16px', background: 'rgba(16,185,129,0.08)', border: '1px solid rgba(16,185,129,0.2)', borderRadius: '10px', display: 'flex', gap: '10px', alignItems: 'flex-start' }}>
        <span style={{ fontSize: '1rem' }}>🔒</span>
        <p style={{ margin: 0, fontSize: '0.8rem', color: '#6ee7b7', lineHeight: 1.5 }}>
          All transactions are secured with 256-bit SSL encryption. Payment details are processed by our payment gateway and never stored on our servers.
        </p>
      </div>
    </div>
  );
}

export default PaymentMethodsPage;
