import React, { useEffect, useState } from 'react';
import { useAuth0 } from '@auth0/auth0-react';
import { getHeaders } from '../services/api';

const API_BASE = process.env.REACT_APP_API_BASE || 'https://hntwmrwmsl.execute-api.ap-southeast-1.amazonaws.com';

const adminFetch = async (path, options = {}, getAccessTokenSilently, isAuthenticated) => {
  const headers = await getHeaders(isAuthenticated, getAccessTokenSilently);
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: { ...headers, ...(options.headers || {}) },
    body: options.body ? JSON.stringify(options.body) : undefined,
  });
  return res.json();
};

// ── Stat card ─────────────────────────────────────────────────────────────────
function StatCard({ label, value, color }) {
  return (
    <div style={{
      background: 'rgba(255,255,255,0.05)',
      border: `1px solid ${color}33`,
      borderRadius: '12px',
      padding: '24px',
      flex: 1,
      minWidth: '160px'
    }}>
      <div style={{ fontSize: '0.8rem', opacity: 0.6, marginBottom: '8px' }}>{label}</div>
      <div style={{ fontSize: '1.8rem', fontWeight: 700, color }}>{value}</div>
    </div>
  );
}

// ── Dashboard tab ─────────────────────────────────────────────────────────────
function Dashboard({ stats }) {
  if (!stats) return <p style={{ opacity: 0.5 }}>Loading stats...</p>;

  const statusColors = {
    created: '#f59e0b', confirmed: '#3b82f6', processing: '#8b5cf6',
    shipped: '#06b6d4', delivered: '#10b981', paid: '#10b981',
    cancelled: '#ef4444', paid_failed: '#ef4444'
  };

  return (
    <div>
      <h3 style={{ marginBottom: '24px' }}>Overview</h3>

      <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap', marginBottom: '32px' }}>
        <StatCard label="Total Orders"   value={stats.total_orders}                          color="#3b82f6" />
        <StatCard label="Total Revenue"  value={`₹${stats.total_revenue?.toLocaleString('en-IN')}`} color="#10b981" />
        <StatCard label="Low Stock Items" value={stats.low_stock?.length ?? 0}               color="#f59e0b" />
      </div>

      <div style={{ display: 'flex', gap: '24px', flexWrap: 'wrap' }}>
        {/* Orders by status */}
        <div style={{ flex: 1, minWidth: '240px' }}>
          <h4 style={{ marginBottom: '12px', opacity: 0.7 }}>Orders by Status</h4>
          {Object.entries(stats.status_counts || {}).map(([status, count]) => (
            <div key={status} style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
              <span style={{ color: statusColors[status] || '#fff', textTransform: 'capitalize' }}>{status}</span>
              <span style={{ fontWeight: 600 }}>{count}</span>
            </div>
          ))}
        </div>

        {/* Low stock */}
        <div style={{ flex: 1, minWidth: '240px' }}>
          <h4 style={{ marginBottom: '12px', opacity: 0.7 }}>⚠️ Low Stock</h4>
          {stats.low_stock?.length === 0 && <p style={{ opacity: 0.5 }}>All products well stocked.</p>}
          {stats.low_stock?.map(p => (
            <div key={p.id} style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
              <span style={{ fontSize: '0.9rem' }}>{p.name}</span>
              <span style={{ color: p.stock_quantity === 0 ? '#ef4444' : '#f59e0b', fontWeight: 600 }}>{p.stock_quantity} left</span>
            </div>
          ))}
        </div>

        {/* Top products */}
        <div style={{ flex: 1, minWidth: '240px' }}>
          <h4 style={{ marginBottom: '12px', opacity: 0.7 }}>🏆 Top Products</h4>
          {stats.top_products?.map((p, i) => (
            <div key={p.product_id} style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
              <span style={{ opacity: 0.7 }}>#{i + 1} ID: {p.product_id}</span>
              <span style={{ fontWeight: 600 }}>{p.units_sold} sold</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ── Products tab ──────────────────────────────────────────────────────────────
function ProductsTab({ getAccessTokenSilently, isAuthenticated }) {
  const [products, setProducts]   = useState([]);
  const [editing, setEditing]     = useState(null); // product being edited
  const [editForm, setEditForm]   = useState({});
  const [msg, setMsg]             = useState('');

  useEffect(() => {
    adminFetch('/admin/products', {}, getAccessTokenSilently, isAuthenticated)
      .then(d => { if (d.status === 'success') setProducts(d.data); });
  }, []);

  const saveEdit = async () => {
    const d = await adminFetch(`/admin/products/${editing.id}`, { method: 'PUT', body: editForm }, getAccessTokenSilently, isAuthenticated);
    if (d.status === 'success') {
      setProducts(prev => prev.map(p => p.id === editing.id ? d.data : p));
      setEditing(null);
      setMsg('Product updated ✅');
    } else {
      setMsg(d.message || 'Update failed');
    }
  };

  const deleteProduct = async (id) => {
    if (!window.confirm('Delete this product?')) return;
    const d = await adminFetch(`/admin/products/${id}`, { method: 'DELETE' }, getAccessTokenSilently, isAuthenticated);
    if (d.status === 'success') {
      setProducts(prev => prev.filter(p => p.id !== id));
      setMsg('Product deleted ✅');
    }
  };

  return (
    <div>
      <h3 style={{ marginBottom: '16px' }}>Products ({products.length})</h3>
      {msg && <p style={{ color: '#10b981', marginBottom: '12px' }}>{msg}</p>}

      {editing && (
        <div style={{ background: 'rgba(255,255,255,0.05)', borderRadius: '12px', padding: '20px', marginBottom: '24px' }}>
          <h4 style={{ marginBottom: '16px' }}>Editing: {editing.name}</h4>
          {['name', 'price', 'stock_quantity', 'description'].map(field => (
            <div key={field} style={{ marginBottom: '12px' }}>
              <label style={{ display: 'block', fontSize: '0.8rem', opacity: 0.6, marginBottom: '4px', textTransform: 'capitalize' }}>{field.replace('_', ' ')}</label>
              <input
                value={editForm[field] ?? ''}
                onChange={e => setEditForm(f => ({ ...f, [field]: e.target.value }))}
                style={{ width: '100%', padding: '8px 12px', background: 'rgba(255,255,255,0.08)', border: '1px solid rgba(255,255,255,0.15)', borderRadius: '8px', color: '#fff', fontSize: '0.9rem' }}
              />
            </div>
          ))}
          <div style={{ display: 'flex', gap: '12px', marginTop: '16px' }}>
            <button className="btn-primary" onClick={saveEdit}>Save</button>
            <button onClick={() => setEditing(null)} style={{ padding: '8px 16px', background: 'transparent', border: '1px solid rgba(255,255,255,0.2)', borderRadius: '8px', color: '#fff', cursor: 'pointer' }}>Cancel</button>
          </div>
        </div>
      )}

      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.1)', opacity: 0.6 }}>
              {['ID', 'Name', 'Category', 'Price (₹)', 'Stock', 'Rating', 'Actions'].map(h => (
                <th key={h} style={{ padding: '10px 12px', textAlign: 'left', fontWeight: 500 }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {products.map(p => (
              <tr key={p.id} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                <td style={{ padding: '10px 12px', opacity: 0.5 }}>{p.id}</td>
                <td style={{ padding: '10px 12px' }}>{p.name}</td>
                <td style={{ padding: '10px 12px', opacity: 0.7 }}>{p.category}</td>
                <td style={{ padding: '10px 12px' }}>₹{p.price?.toLocaleString('en-IN')}</td>
                <td style={{ padding: '10px 12px', color: p.stock_quantity < 10 ? '#f59e0b' : '#10b981', fontWeight: 600 }}>{p.stock_quantity}</td>
                <td style={{ padding: '10px 12px' }}>⭐ {p.rating}</td>
                <td style={{ padding: '10px 12px' }}>
                  <button onClick={() => { setEditing(p); setEditForm({ name: p.name, price: p.price, stock_quantity: p.stock_quantity, description: p.description }); }}
                    style={{ marginRight: '8px', padding: '4px 10px', background: 'rgba(59,130,246,0.2)', border: '1px solid #3b82f6', borderRadius: '6px', color: '#3b82f6', cursor: 'pointer', fontSize: '0.8rem' }}>
                    Edit
                  </button>
                  <button onClick={() => deleteProduct(p.id)}
                    style={{ padding: '4px 10px', background: 'rgba(239,68,68,0.2)', border: '1px solid #ef4444', borderRadius: '6px', color: '#ef4444', cursor: 'pointer', fontSize: '0.8rem' }}>
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ── Orders tab ────────────────────────────────────────────────────────────────
function OrdersTab({ getAccessTokenSilently, isAuthenticated }) {
  const [orders, setOrders]       = useState([]);
  const [statusFilter, setFilter] = useState('');
  const [msg, setMsg]             = useState('');

  const loadOrders = async (filter = '') => {
    const path = filter ? `/admin/orders?status=${filter}` : '/admin/orders';
    const d    = await adminFetch(path, {}, getAccessTokenSilently, isAuthenticated);
    if (d.status === 'success') setOrders(d.data);
  };

  useEffect(() => { loadOrders(); }, []);

  const updateStatus = async (orderId, newStatus) => {
    const d = await adminFetch(`/admin/orders/${orderId}`, { method: 'PUT', body: { status: newStatus } }, getAccessTokenSilently, isAuthenticated);
    if (d.status === 'success') {
      setOrders(prev => prev.map(o => o.order_id === orderId ? { ...o, status: newStatus } : o));
      setMsg(`Order ${orderId.slice(0, 8)}... → ${newStatus} ✅`);
    }
  };

  const statusOptions = ['created', 'confirmed', 'processing', 'shipped', 'delivered', 'paid', 'cancelled'];
  const statusColors  = { created: '#f59e0b', confirmed: '#3b82f6', processing: '#8b5cf6', shipped: '#06b6d4', delivered: '#10b981', paid: '#10b981', cancelled: '#ef4444' };

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '20px' }}>
        <h3>Orders ({orders.length})</h3>
        <select value={statusFilter} onChange={e => { setFilter(e.target.value); loadOrders(e.target.value); }}
          style={{ padding: '6px 12px', background: 'rgba(255,255,255,0.08)', border: '1px solid rgba(255,255,255,0.15)', borderRadius: '8px', color: '#fff', fontSize: '0.85rem' }}>
          <option value="">All statuses</option>
          {statusOptions.map(s => <option key={s} value={s}>{s}</option>)}
        </select>
      </div>
      {msg && <p style={{ color: '#10b981', marginBottom: '12px' }}>{msg}</p>}

      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.1)', opacity: 0.6 }}>
              {['Order ID', 'User', 'Items', 'Total (₹)', 'Status', 'Update Status'].map(h => (
                <th key={h} style={{ padding: '10px 12px', textAlign: 'left', fontWeight: 500 }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {orders.map(o => {
              const total = o.items?.reduce((s, i) => s + i.price * i.quantity, 0) || 0;
              return (
                <tr key={o.order_id} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                  <td style={{ padding: '10px 12px', opacity: 0.5, fontSize: '0.75rem' }}>{o.order_id?.slice(0, 12)}...</td>
                  <td style={{ padding: '10px 12px', opacity: 0.7, fontSize: '0.75rem' }}>{o.user_id?.slice(0, 16)}...</td>
                  <td style={{ padding: '10px 12px' }}>{o.items?.length} item(s)</td>
                  <td style={{ padding: '10px 12px' }}>₹{total.toLocaleString('en-IN')}</td>
                  <td style={{ padding: '10px 12px' }}>
                    <span style={{ color: statusColors[o.status] || '#fff', fontWeight: 600, textTransform: 'capitalize' }}>{o.status}</span>
                  </td>
                  <td style={{ padding: '10px 12px' }}>
                    <select defaultValue="" onChange={e => { if (e.target.value) updateStatus(o.order_id, e.target.value); }}
                      style={{ padding: '4px 8px', background: 'rgba(255,255,255,0.08)', border: '1px solid rgba(255,255,255,0.15)', borderRadius: '6px', color: '#fff', fontSize: '0.8rem' }}>
                      <option value="">Change...</option>
                      {statusOptions.filter(s => s !== o.status).map(s => <option key={s} value={s}>{s}</option>)}
                    </select>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ── Main AdminPanel ───────────────────────────────────────────────────────────
export default function AdminPanel() {
  const { getAccessTokenSilently, isAuthenticated, user } = useAuth0();
  const [tab, setTab]     = useState('dashboard');
  const [stats, setStats] = useState(null);
  const [allowed, setAllowed] = useState(null); // null = checking

  useEffect(() => {
    if (!isAuthenticated) { setAllowed(false); return; }

    // Check admin role from Auth0 custom claim
    getAccessTokenSilently()
      .then(token => {
        const payload = JSON.parse(atob(token.split('.')[1]));
        const roles   = payload['https://mystore.com/roles'] || [];
        setAllowed(Array.isArray(roles) ? roles.includes('admin') : roles === 'admin');
      })
      .catch(() => setAllowed(false));
  }, [isAuthenticated]);

  useEffect(() => {
    if (allowed && tab === 'dashboard') {
      adminFetch('/admin/dashboard', {}, getAccessTokenSilently, isAuthenticated)
        .then(d => { if (d.status === 'success') setStats(d.data); });
    }
  }, [allowed, tab]);

  if (allowed === null) return <div style={{ padding: '40px', opacity: 0.5 }}>Checking access...</div>;
  if (!allowed) return (
    <div style={{ padding: '40px', textAlign: 'center' }}>
      <h2 style={{ color: '#ef4444' }}>Access Denied</h2>
      <p style={{ opacity: 0.6 }}>You need admin privileges to view this page.</p>
    </div>
  );

  const tabs = [
    { id: 'dashboard', label: '📊 Dashboard' },
    { id: 'products',  label: '📦 Products'  },
    { id: 'orders',    label: '🛒 Orders'    },
  ];

  return (
    <div style={{ padding: '32px', maxWidth: '1200px', margin: '0 auto' }}>
      <div style={{ marginBottom: '32px' }}>
        <h1 style={{ fontSize: '1.8rem', fontWeight: 700, marginBottom: '4px' }}>Admin Panel</h1>
        <p style={{ opacity: 0.5, fontSize: '0.85rem' }}>Logged in as {user?.email}</p>
      </div>

      {/* Tab bar */}
      <div style={{ display: 'flex', gap: '8px', marginBottom: '32px', borderBottom: '1px solid rgba(255,255,255,0.1)', paddingBottom: '0' }}>
        {tabs.map(t => (
          <button key={t.id} onClick={() => setTab(t.id)}
            style={{
              padding: '10px 20px', background: 'transparent', border: 'none',
              borderBottom: tab === t.id ? '2px solid #3b82f6' : '2px solid transparent',
              color: tab === t.id ? '#3b82f6' : 'rgba(255,255,255,0.6)',
              cursor: 'pointer', fontSize: '0.9rem', fontWeight: tab === t.id ? 600 : 400,
              marginBottom: '-1px'
            }}>
            {t.label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      {tab === 'dashboard' && <Dashboard stats={stats} />}
      {tab === 'products'  && <ProductsTab getAccessTokenSilently={getAccessTokenSilently} isAuthenticated={isAuthenticated} />}
      {tab === 'orders'    && <OrdersTab   getAccessTokenSilently={getAccessTokenSilently} isAuthenticated={isAuthenticated} />}
    </div>
  );
}
