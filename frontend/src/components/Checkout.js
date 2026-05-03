import React, { useState } from 'react';

const INDIAN_STATES = [
  'Andhra Pradesh','Arunachal Pradesh','Assam','Bihar','Chhattisgarh',
  'Goa','Gujarat','Haryana','Himachal Pradesh','Jharkhand','Karnataka',
  'Kerala','Madhya Pradesh','Maharashtra','Manipur','Meghalaya','Mizoram',
  'Nagaland','Odisha','Punjab','Rajasthan','Sikkim','Tamil Nadu','Telangana',
  'Tripura','Uttar Pradesh','Uttarakhand','West Bengal',
  'Andaman and Nicobar Islands','Chandigarh','Dadra and Nagar Haveli and Daman and Diu',
  'Delhi','Jammu and Kashmir','Ladakh','Lakshadweep','Puducherry'
];

function Checkout({ cart, onConfirm, onCancel, loading }) {
  const [address, setAddress] = useState({
    full_name: '', phone: '', address_line1: '', address_line2: '',
    city: '', state: '', pincode: ''
  });
  const [errors, setErrors] = useState({});

  // ── Pricing breakdown ──────────────────────────────────────────────────────
  const subtotal        = cart.reduce((s, i) => s + i.price * i.quantity, 0);
  const deliveryCharge  = subtotal >= 500 ? 0 : 49;
  const gst             = Math.round(subtotal * 0.18);
  const grandTotal      = subtotal + deliveryCharge + gst;

  const fmt = (n) => `₹${n.toLocaleString('en-IN')}`;

  // ── Validation ─────────────────────────────────────────────────────────────
  const validate = () => {
    const e = {};
    if (!address.full_name.trim())       e.full_name     = 'Full name is required';
    if (!/^\d{10}$/.test(address.phone)) e.phone         = 'Enter a valid 10-digit phone number';
    if (!address.address_line1.trim())   e.address_line1 = 'Address is required';
    if (!address.city.trim())            e.city          = 'City is required';
    if (!address.state)                  e.state         = 'State is required';
    if (!/^\d{6}$/.test(address.pincode))e.pincode       = 'Enter a valid 6-digit PIN code';
    setErrors(e);
    return Object.keys(e).length === 0;
  };

  const handleSubmit = () => {
    if (!validate()) return;
    onConfirm({ address, grandTotal });
  };

  const field = (key, label, placeholder, type = 'text') => (
    <div style={{ marginBottom: '16px' }}>
      <label style={{ display: 'block', fontSize: '0.8rem', opacity: 0.6, marginBottom: '4px' }}>{label}</label>
      <input
        type={type}
        value={address[key]}
        onChange={e => setAddress(a => ({ ...a, [key]: e.target.value }))}
        placeholder={placeholder}
        style={{
          width: '100%', padding: '10px 14px', boxSizing: 'border-box',
          background: 'rgba(255,255,255,0.07)', border: `1px solid ${errors[key] ? '#ef4444' : 'rgba(255,255,255,0.15)'}`,
          borderRadius: '8px', color: '#fff', fontSize: '0.9rem'
        }}
      />
      {errors[key] && <p style={{ color: '#ef4444', fontSize: '0.75rem', marginTop: '4px' }}>{errors[key]}</p>}
    </div>
  );

  return (
    <div style={{ maxWidth: '960px', margin: '0 auto', padding: '32px 24px' }}>
      <h2 style={{ marginBottom: '32px', fontSize: '1.6rem' }}>Checkout</h2>

      <div style={{ display: 'flex', gap: '32px', flexWrap: 'wrap' }}>

        {/* ── Left: Address form ─────────────────────────────────────────── */}
        <div style={{ flex: '1 1 380px' }}>
          <h3 style={{ marginBottom: '20px', fontSize: '1rem', opacity: 0.8 }}>Delivery Address</h3>

          {field('full_name',     'Full Name',    'John Doe')}
          {field('phone',         'Phone Number', '10-digit mobile number', 'tel')}
          {field('address_line1', 'Address Line 1', 'House / Flat / Block No., Street')}
          {field('address_line2', 'Address Line 2 (optional)', 'Area, Colony, Landmark')}

          <div style={{ display: 'flex', gap: '12px' }}>
            <div style={{ flex: 1 }}>{field('city', 'City', 'Mumbai')}</div>
            <div style={{ flex: 1 }}>
              <label style={{ display: 'block', fontSize: '0.8rem', opacity: 0.6, marginBottom: '4px' }}>State</label>
              <select
                value={address.state}
                onChange={e => setAddress(a => ({ ...a, state: e.target.value }))}
                style={{
                  width: '100%', padding: '10px 14px', boxSizing: 'border-box',
                  background: 'rgba(255,255,255,0.07)', border: `1px solid ${errors.state ? '#ef4444' : 'rgba(255,255,255,0.15)'}`,
                  borderRadius: '8px', color: address.state ? '#fff' : 'rgba(255,255,255,0.4)', fontSize: '0.9rem'
                }}
              >
                <option value="">Select state</option>
                {INDIAN_STATES.map(s => <option key={s} value={s} style={{ background: '#1a1a2e', color: '#fff' }}>{s}</option>)}
              </select>
              {errors.state && <p style={{ color: '#ef4444', fontSize: '0.75rem', marginTop: '4px' }}>{errors.state}</p>}
            </div>
          </div>

          {field('pincode', 'PIN Code', '400001')}
        </div>

        {/* ── Right: Order summary ───────────────────────────────────────── */}
        <div style={{ flex: '1 1 280px' }}>
          <h3 style={{ marginBottom: '20px', fontSize: '1rem', opacity: 0.8 }}>Order Summary</h3>

          <div style={{ background: 'rgba(255,255,255,0.04)', borderRadius: '12px', padding: '20px', marginBottom: '20px' }}>
            {cart.map(item => (
              <div key={item.id} style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid rgba(255,255,255,0.05)', fontSize: '0.85rem' }}>
                <span style={{ opacity: 0.8 }}>{item.name} × {item.quantity}</span>
                <span>{fmt(item.price * item.quantity)}</span>
              </div>
            ))}

            <div style={{ marginTop: '16px', display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '0.85rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', opacity: 0.7 }}>
                <span>Subtotal</span><span>{fmt(subtotal)}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', opacity: 0.7 }}>
                <span>Delivery</span>
                <span style={{ color: deliveryCharge === 0 ? '#10b981' : 'inherit' }}>
                  {deliveryCharge === 0 ? 'FREE' : fmt(deliveryCharge)}
                </span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', opacity: 0.7 }}>
                <span>GST (18%)</span><span>{fmt(gst)}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontWeight: 700, fontSize: '1rem', borderTop: '1px solid rgba(255,255,255,0.1)', paddingTop: '12px', marginTop: '4px' }}>
                <span>Grand Total</span><span>{fmt(grandTotal)}</span>
              </div>
            </div>
          </div>

          {deliveryCharge > 0 && (
            <p style={{ fontSize: '0.75rem', opacity: 0.5, marginBottom: '16px' }}>
              Add {fmt(500 - subtotal)} more for free delivery
            </p>
          )}

          <button
            className="btn-primary"
            onClick={handleSubmit}
            disabled={loading}
            style={{ width: '100%', padding: '14px', fontSize: '1rem', marginBottom: '12px' }}
          >
            {loading ? 'Placing Order...' : `Place Order · ${fmt(grandTotal)}`}
          </button>

          <button
            onClick={onCancel}
            disabled={loading}
            style={{ width: '100%', padding: '12px', background: 'transparent', border: '1px solid rgba(255,255,255,0.15)', borderRadius: '8px', color: 'rgba(255,255,255,0.6)', cursor: 'pointer', fontSize: '0.9rem' }}
          >
            Back to Cart
          </button>
        </div>
      </div>
    </div>
  );
}

export default Checkout;
