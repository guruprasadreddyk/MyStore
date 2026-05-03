import React, { useEffect, useState } from 'react';
import { useAuth0 } from '@auth0/auth0-react';
import { fetchAddresses, addAddress, setDefaultAddress, deleteAddress, getHeaders } from '../services/api';

const INDIAN_STATES = [
  'Andhra Pradesh','Arunachal Pradesh','Assam','Bihar','Chhattisgarh',
  'Goa','Gujarat','Haryana','Himachal Pradesh','Jharkhand','Karnataka',
  'Kerala','Madhya Pradesh','Maharashtra','Manipur','Meghalaya','Mizoram',
  'Nagaland','Odisha','Punjab','Rajasthan','Sikkim','Tamil Nadu','Telangana',
  'Tripura','Uttar Pradesh','Uttarakhand','West Bengal',
  'Andaman and Nicobar Islands','Chandigarh','Dadra and Nagar Haveli and Daman and Diu',
  'Delhi','Jammu and Kashmir','Ladakh','Lakshadweep','Puducherry'
];

const EMPTY_FORM = { full_name: '', phone: '', address_line1: '', address_line2: '', city: '', state: '', pincode: '' };

function AddressesPage() {
  const { isAuthenticated, getAccessTokenSilently, loginWithRedirect } = useAuth0();
  const [addresses, setAddresses] = useState([]);
  const [loading, setLoading]     = useState(false);
  const [showForm, setShowForm]   = useState(false);
  const [form, setForm]           = useState(EMPTY_FORM);
  const [errors, setErrors]       = useState({});
  const [msg, setMsg]             = useState('');

  const headers = async () => getHeaders(isAuthenticated, getAccessTokenSilently);

  const load = async () => {
    if (!isAuthenticated) return;
    setLoading(true);
    const d = await fetchAddresses(await headers());
    if (d.status === 'success') setAddresses(d.data || []);
    setLoading(false);
  };

  useEffect(() => { load(); }, [isAuthenticated]);

  const validate = () => {
    const e = {};
    if (!form.full_name.trim())        e.full_name     = 'Required';
    if (!/^\d{10}$/.test(form.phone))  e.phone         = '10-digit number';
    if (!form.address_line1.trim())    e.address_line1 = 'Required';
    if (!form.city.trim())             e.city          = 'Required';
    if (!form.state)                   e.state         = 'Required';
    if (!/^\d{6}$/.test(form.pincode)) e.pincode       = '6-digit PIN';
    setErrors(e);
    return Object.keys(e).length === 0;
  };

  const handleAdd = async () => {
    if (!validate()) return;
    setLoading(true);
    const d = await addAddress(form, await headers());
    if (d.status === 'success') {
      setAddresses(d.data);
      setShowForm(false);
      setForm(EMPTY_FORM);
      setMsg('Address saved ✅');
    } else {
      setMsg(d.message || 'Failed to save');
    }
    setLoading(false);
  };

  const handleSetDefault = async (id) => {
    setLoading(true);
    const d = await setDefaultAddress(id, await headers());
    if (d.status === 'success') { setAddresses(d.data); setMsg('Default address updated ✅'); }
    setLoading(false);
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Delete this address?')) return;
    setLoading(true);
    const d = await deleteAddress(id, await headers());
    if (d.status === 'success') { setAddresses(d.data); setMsg('Address deleted'); }
    setLoading(false);
  };

  const inp = (key, label, placeholder, type = 'text') => (
    <div style={{ marginBottom: '12px' }}>
      <label style={{ display: 'block', fontSize: '0.78rem', opacity: 0.55, marginBottom: '4px' }}>{label}</label>
      <input type={type} value={form[key]} placeholder={placeholder}
        onChange={e => setForm(f => ({ ...f, [key]: e.target.value }))}
        style={{ width: '100%', padding: '9px 12px', boxSizing: 'border-box', background: 'rgba(255,255,255,0.07)', border: `1px solid ${errors[key] ? '#ef4444' : 'rgba(255,255,255,0.15)'}`, borderRadius: '8px', color: '#fff', fontSize: '0.88rem' }}
      />
      {errors[key] && <p style={{ color: '#ef4444', fontSize: '0.72rem', margin: '3px 0 0' }}>{errors[key]}</p>}
    </div>
  );

  if (!isAuthenticated) return (
    <div style={{ padding: '60px 24px', textAlign: 'center' }}>
      <p style={{ opacity: 0.5, marginBottom: '16px' }}>Please log in to manage addresses.</p>
      <button className="btn-primary" style={{ width: 'auto', padding: '12px 32px' }} onClick={() => loginWithRedirect()}>Log In</button>
    </div>
  );

  return (
    <div style={{ maxWidth: '680px', margin: '0 auto', padding: '40px 24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '28px' }}>
        <h2 style={{ fontSize: '1.6rem', margin: 0 }}>Saved Addresses</h2>
        <button className="btn-primary" style={{ width: 'auto', padding: '10px 20px', fontSize: '0.9rem' }}
          onClick={() => { setShowForm(s => !s); setErrors({}); setForm(EMPTY_FORM); }}>
          {showForm ? 'Cancel' : '+ Add New'}
        </button>
      </div>

      {msg && <p style={{ color: '#10b981', marginBottom: '16px', fontSize: '0.85rem' }}>{msg}</p>}

      {/* Add form */}
      {showForm && (
        <div style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '14px', padding: '20px', marginBottom: '24px' }}>
          <h4 style={{ margin: '0 0 16px', fontSize: '0.95rem' }}>New Address</h4>
          {inp('full_name', 'Full Name', 'John Doe')}
          {inp('phone', 'Phone', '10-digit mobile', 'tel')}
          {inp('address_line1', 'Address Line 1', 'House / Flat / Street')}
          {inp('address_line2', 'Address Line 2 (optional)', 'Area, Landmark')}
          <div style={{ display: 'flex', gap: '12px' }}>
            <div style={{ flex: 1 }}>{inp('city', 'City', 'Mumbai')}</div>
            <div style={{ flex: 1 }}>
              <label style={{ display: 'block', fontSize: '0.78rem', opacity: 0.55, marginBottom: '4px' }}>State</label>
              <select value={form.state} onChange={e => setForm(f => ({ ...f, state: e.target.value }))}
                style={{ width: '100%', padding: '9px 12px', background: 'rgba(255,255,255,0.07)', border: `1px solid ${errors.state ? '#ef4444' : 'rgba(255,255,255,0.15)'}`, borderRadius: '8px', color: form.state ? '#fff' : 'rgba(255,255,255,0.35)', fontSize: '0.88rem' }}>
                <option value="">Select</option>
                {INDIAN_STATES.map(s => <option key={s} value={s} style={{ background: '#1a1a2e' }}>{s}</option>)}
              </select>
              {errors.state && <p style={{ color: '#ef4444', fontSize: '0.72rem', margin: '3px 0 0' }}>{errors.state}</p>}
            </div>
          </div>
          {inp('pincode', 'PIN Code', '400001')}
          <button className="btn-primary" onClick={handleAdd} disabled={loading} style={{ marginTop: '8px', padding: '11px 24px', width: 'auto' }}>
            {loading ? 'Saving...' : 'Save Address'}
          </button>
        </div>
      )}

      {/* Address list */}
      {loading && addresses.length === 0 && <p style={{ opacity: 0.4 }}>Loading...</p>}
      {!loading && addresses.length === 0 && !showForm && (
        <div style={{ textAlign: 'center', padding: '48px', opacity: 0.4 }}>
          <p style={{ fontSize: '2rem', marginBottom: '8px' }}>📍</p>
          <p>No saved addresses yet.</p>
        </div>
      )}

      <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
        {addresses.map(addr => (
          <div key={addr.address_id} style={{ background: 'rgba(255,255,255,0.04)', border: `1px solid ${addr.is_default ? 'rgba(59,130,246,0.4)' : 'rgba(255,255,255,0.08)'}`, borderRadius: '12px', padding: '18px 20px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '6px' }}>
                  <span style={{ fontWeight: 600, fontSize: '0.95rem' }}>{addr.full_name}</span>
                  {addr.is_default && (
                    <span style={{ background: 'rgba(59,130,246,0.15)', border: '1px solid rgba(59,130,246,0.3)', color: '#60a5fa', fontSize: '0.7rem', padding: '2px 8px', borderRadius: '20px', fontWeight: 600 }}>DEFAULT</span>
                  )}
                </div>
                <p style={{ margin: '0 0 2px', fontSize: '0.85rem', opacity: 0.7 }}>
                  {addr.address_line1}{addr.address_line2 ? `, ${addr.address_line2}` : ''}
                </p>
                <p style={{ margin: '0 0 2px', fontSize: '0.85rem', opacity: 0.7 }}>
                  {addr.city}, {addr.state} – {addr.pincode}
                </p>
                <p style={{ margin: 0, fontSize: '0.82rem', opacity: 0.5 }}>📞 {addr.phone}</p>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', alignItems: 'flex-end' }}>
                {!addr.is_default && (
                  <button onClick={() => handleSetDefault(addr.address_id)} disabled={loading}
                    style={{ padding: '5px 12px', background: 'transparent', border: '1px solid rgba(255,255,255,0.2)', borderRadius: '6px', color: 'rgba(255,255,255,0.6)', cursor: 'pointer', fontSize: '0.78rem' }}>
                    Set Default
                  </button>
                )}
                <button onClick={() => handleDelete(addr.address_id)} disabled={loading}
                  style={{ padding: '5px 12px', background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)', borderRadius: '6px', color: '#ef4444', cursor: 'pointer', fontSize: '0.78rem' }}>
                  Delete
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default AddressesPage;
