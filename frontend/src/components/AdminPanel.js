import React, { useEffect, useState } from 'react';
import { useAuth0 } from '@auth0/auth0-react';
import { getHeaders, API_BASE } from '../services/api';

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

  // Calculate max values for chart scaling
  const maxRevenue = Math.max(...(stats.time_series?.map(d => d.revenue) || [1]));
  const maxOrders = Math.max(...(stats.time_series?.map(d => d.orders) || [1]));

  return (
    <div>
      <h3 style={{ marginBottom: '24px' }}>Overview</h3>

      <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap', marginBottom: '32px' }}>
        <StatCard label="Total Orders"   value={stats.total_orders}                          color="#3b82f6" />
        <StatCard label="Total Revenue"  value={`₹${stats.total_revenue?.toLocaleString('en-IN')}`} color="#10b981" />
        <StatCard label="Low Stock Items" value={stats.low_stock?.length ?? 0}               color="#f59e0b" />
      </div>

      {/* Time-series charts */}
      {stats.time_series && stats.time_series.length > 0 && (
        <div style={{ marginBottom: '32px' }}>
          <h4 style={{ marginBottom: '16px', opacity: 0.7 }}>📈 Trends (Last 30 Days)</h4>
          
          {/* Revenue chart */}
          <div style={{ marginBottom: '24px' }}>
            <p style={{ fontSize: '0.8rem', opacity: 0.6, marginBottom: '8px' }}>Daily Revenue</p>
            <div style={{ display: 'flex', alignItems: 'flex-end', gap: '2px', height: '120px', background: 'rgba(255,255,255,0.02)', borderRadius: '8px', padding: '12px' }}>
              {stats.time_series.map((day, i) => {
                const height = maxRevenue > 0 ? (day.revenue / maxRevenue) * 100 : 0;
                return (
                  <div key={i} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'flex-end' }}>
                    <div
                      title={`${day.date}: ₹${day.revenue.toLocaleString('en-IN')}`}
                      style={{
                        width: '100%',
                        height: `${height}%`,
                        background: 'linear-gradient(to top, #10b981, #34d399)',
                        borderRadius: '2px 2px 0 0',
                        minHeight: day.revenue > 0 ? '2px' : '0',
                        cursor: 'pointer'
                      }}
                    />
                  </div>
                );
              })}
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem', opacity: 0.4, marginTop: '4px' }}>
              <span>{stats.time_series[0]?.date}</span>
              <span>{stats.time_series[stats.time_series.length - 1]?.date}</span>
            </div>
          </div>

          {/* Orders chart */}
          <div style={{ marginBottom: '24px' }}>
            <p style={{ fontSize: '0.8rem', opacity: 0.6, marginBottom: '8px' }}>Daily Orders</p>
            <div style={{ display: 'flex', alignItems: 'flex-end', gap: '2px', height: '120px', background: 'rgba(255,255,255,0.02)', borderRadius: '8px', padding: '12px' }}>
              {stats.time_series.map((day, i) => {
                const height = maxOrders > 0 ? (day.orders / maxOrders) * 100 : 0;
                return (
                  <div key={i} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'flex-end' }}>
                    <div
                      title={`${day.date}: ${day.orders} orders`}
                      style={{
                        width: '100%',
                        height: `${height}%`,
                        background: 'linear-gradient(to top, #3b82f6, #60a5fa)',
                        borderRadius: '2px 2px 0 0',
                        minHeight: day.orders > 0 ? '2px' : '0',
                        cursor: 'pointer'
                      }}
                    />
                  </div>
                );
              })}
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem', opacity: 0.4, marginTop: '4px' }}>
              <span>{stats.time_series[0]?.date}</span>
              <span>{stats.time_series[stats.time_series.length - 1]?.date}</span>
            </div>
          </div>

          {/* Summary stats */}
          <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap', fontSize: '0.85rem' }}>
            <div style={{ flex: 1, minWidth: '140px', background: 'rgba(16,185,129,0.1)', border: '1px solid rgba(16,185,129,0.3)', borderRadius: '8px', padding: '12px' }}>
              <div style={{ opacity: 0.6, marginBottom: '4px' }}>Avg Daily Revenue</div>
              <div style={{ fontSize: '1.2rem', fontWeight: 600, color: '#10b981' }}>
                ₹{Math.round(stats.time_series.reduce((sum, d) => sum + d.revenue, 0) / stats.time_series.length).toLocaleString('en-IN')}
              </div>
            </div>
            <div style={{ flex: 1, minWidth: '140px', background: 'rgba(59,130,246,0.1)', border: '1px solid rgba(59,130,246,0.3)', borderRadius: '8px', padding: '12px' }}>
              <div style={{ opacity: 0.6, marginBottom: '4px' }}>Avg Daily Orders</div>
              <div style={{ fontSize: '1.2rem', fontWeight: 600, color: '#3b82f6' }}>
                {(stats.time_series.reduce((sum, d) => sum + d.orders, 0) / stats.time_series.length).toFixed(1)}
              </div>
            </div>
            <div style={{ flex: 1, minWidth: '140px', background: 'rgba(139,92,246,0.1)', border: '1px solid rgba(139,92,246,0.3)', borderRadius: '8px', padding: '12px' }}>
              <div style={{ opacity: 0.6, marginBottom: '4px' }}>Total Customers</div>
              <div style={{ fontSize: '1.2rem', fontWeight: 600, color: '#8b5cf6' }}>
                {stats.time_series.reduce((sum, d) => sum + d.customers, 0)}
              </div>
            </div>
          </div>
        </div>
      )}

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
  // eslint-disable-next-line react-hooks/exhaustive-deps
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

  useEffect(() => { loadOrders(); }, []); // eslint-disable-line react-hooks/exhaustive-deps

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

// ── Returns tab ───────────────────────────────────────────────────────────────
function ReturnsTab({ getAccessTokenSilently, isAuthenticated }) {
  const [returns, setReturns]     = useState([]);
  const [statusFilter, setFilter] = useState('');
  const [msg, setMsg]             = useState('');
  const [loading, setLoading]     = useState({});
  const [rejectModal, setRejectModal] = useState(null); // { returnId, reason }

  const loadReturns = async (filter = '') => {
    const path = filter ? `/admin/returns?status=${filter}` : '/admin/returns';
    const d    = await adminFetch(path, {}, getAccessTokenSilently, isAuthenticated);
    if (d.status === 'success') setReturns(d.data);
  };

  useEffect(() => { loadReturns(); }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const approveReturn = async (returnId) => {
    setLoading(prev => ({ ...prev, [returnId]: 'approving' }));
    const d = await adminFetch(`/admin/returns/${returnId}/approve`, { method: 'PUT' }, getAccessTokenSilently, isAuthenticated);
    setLoading(prev => ({ ...prev, [returnId]: null }));
    
    if (d.status === 'success') {
      setReturns(prev => prev.map(r => r.return_id === returnId ? d.data : r));
      setMsg(`Return ${returnId.slice(0, 8)}... approved ✅`);
      setTimeout(() => setMsg(''), 3000);
    } else {
      setMsg(`Error: ${d.message || 'Failed to approve return'}`);
      setTimeout(() => setMsg(''), 5000);
    }
  };

  const rejectReturn = async (returnId, reason) => {
    setLoading(prev => ({ ...prev, [returnId]: 'rejecting' }));
    const d = await adminFetch(`/admin/returns/${returnId}/reject`, { 
      method: 'PUT',
      body: { reason }
    }, getAccessTokenSilently, isAuthenticated);
    setLoading(prev => ({ ...prev, [returnId]: null }));
    setRejectModal(null);
    
    if (d.status === 'success') {
      setReturns(prev => prev.map(r => r.return_id === returnId ? d.data : r));
      setMsg(`Return ${returnId.slice(0, 8)}... rejected ✅`);
      setTimeout(() => setMsg(''), 3000);
    } else {
      setMsg(`Error: ${d.message || 'Failed to reject return'}`);
      setTimeout(() => setMsg(''), 5000);
    }
  };

  const processRefund = async (returnId) => {
    setLoading(prev => ({ ...prev, [returnId]: 'refunding' }));
    const d = await adminFetch(`/admin/returns/${returnId}/refund`, { method: 'PUT' }, getAccessTokenSilently, isAuthenticated);
    setLoading(prev => ({ ...prev, [returnId]: null }));
    
    if (d.status === 'success') {
      setReturns(prev => prev.map(r => r.return_id === returnId ? d.data : r));
      setMsg(`Refund processed for ${returnId.slice(0, 8)}... ✅`);
      setTimeout(() => setMsg(''), 3000);
    } else {
      setMsg(`Error: ${d.message || 'Failed to process refund'}`);
      setTimeout(() => setMsg(''), 5000);
    }
  };

  const statusColors = { 
    pending: '#f59e0b', 
    approved: '#3b82f6', 
    refunded: '#10b981', 
    rejected: '#ef4444' 
  };

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '20px' }}>
        <h3>Return Requests ({returns.length})</h3>
        <select value={statusFilter} onChange={e => { setFilter(e.target.value); loadReturns(e.target.value); }}
          style={{ padding: '6px 12px', background: 'rgba(255,255,255,0.08)', border: '1px solid rgba(255,255,255,0.15)', borderRadius: '8px', color: '#fff', fontSize: '0.85rem' }}>
          <option value="">All statuses</option>
          <option value="pending">Pending</option>
          <option value="approved">Approved</option>
          <option value="refunded">Refunded</option>
          <option value="rejected">Rejected</option>
        </select>
      </div>
      {msg && <p style={{ color: msg.startsWith('Error') ? '#ef4444' : '#10b981', marginBottom: '12px' }}>{msg}</p>}

      {/* Reject Modal */}
      {rejectModal && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.7)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}>
          <div style={{ background: '#1a1a1a', borderRadius: '12px', padding: '24px', maxWidth: '400px', width: '90%', border: '1px solid rgba(255,255,255,0.1)' }}>
            <h4 style={{ marginBottom: '16px' }}>Reject Return Request</h4>
            <p style={{ opacity: 0.7, fontSize: '0.9rem', marginBottom: '16px' }}>Please provide a reason for rejecting this return:</p>
            <textarea
              value={rejectModal.reason}
              onChange={e => setRejectModal({ ...rejectModal, reason: e.target.value })}
              placeholder="e.g., Return window expired, item not eligible for return..."
              style={{ width: '100%', minHeight: '80px', padding: '10px', background: 'rgba(255,255,255,0.08)', border: '1px solid rgba(255,255,255,0.15)', borderRadius: '8px', color: '#fff', fontSize: '0.9rem', resize: 'vertical' }}
            />
            <div style={{ display: 'flex', gap: '12px', marginTop: '16px' }}>
              <button 
                onClick={() => rejectReturn(rejectModal.returnId, rejectModal.reason)}
                disabled={!rejectModal.reason.trim()}
                style={{ 
                  flex: 1,
                  padding: '8px 16px', 
                  background: rejectModal.reason.trim() ? 'rgba(239,68,68,0.2)' : 'rgba(239,68,68,0.1)', 
                  border: '1px solid #ef4444', 
                  borderRadius: '8px', 
                  color: '#ef4444', 
                  cursor: rejectModal.reason.trim() ? 'pointer' : 'not-allowed', 
                  fontSize: '0.9rem',
                  opacity: rejectModal.reason.trim() ? 1 : 0.5
                }}>
                Reject Return
              </button>
              <button 
                onClick={() => setRejectModal(null)}
                style={{ flex: 1, padding: '8px 16px', background: 'transparent', border: '1px solid rgba(255,255,255,0.2)', borderRadius: '8px', color: '#fff', cursor: 'pointer', fontSize: '0.9rem' }}>
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {returns.length === 0 && (
        <p style={{ opacity: 0.5, textAlign: 'center', padding: '40px' }}>
          {statusFilter ? `No ${statusFilter} returns found` : 'No return requests yet'}
        </p>
      )}

      {returns.length > 0 && (
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.1)', opacity: 0.6 }}>
                {['Return ID', 'Order ID', 'User', 'Reason', 'Refund Amount (₹)', 'Status', 'Actions'].map(h => (
                  <th key={h} style={{ padding: '10px 12px', textAlign: 'left', fontWeight: 500 }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {returns.map(r => (
                <tr key={r.return_id} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                  <td style={{ padding: '10px 12px', opacity: 0.5, fontSize: '0.75rem' }}>{r.return_id?.slice(0, 12)}...</td>
                  <td style={{ padding: '10px 12px', opacity: 0.7, fontSize: '0.75rem' }}>{r.order_id?.slice(0, 12)}...</td>
                  <td style={{ padding: '10px 12px', opacity: 0.7, fontSize: '0.75rem' }}>{r.user_id?.slice(0, 16)}...</td>
                  <td style={{ padding: '10px 12px', textTransform: 'capitalize' }}>{r.reason?.replace('_', ' ')}</td>
                  <td style={{ padding: '10px 12px', fontWeight: 600 }}>₹{r.refund_amount?.toLocaleString('en-IN')}</td>
                  <td style={{ padding: '10px 12px' }}>
                    <span style={{ 
                      color: statusColors[r.status] || '#fff', 
                      fontWeight: 600, 
                      textTransform: 'capitalize',
                      padding: '4px 8px',
                      background: `${statusColors[r.status] || '#fff'}22`,
                      borderRadius: '6px',
                      fontSize: '0.8rem'
                    }}>
                      {r.status}
                    </span>
                  </td>
                  <td style={{ padding: '10px 12px' }}>
                    <div style={{ display: 'flex', gap: '8px' }}>
                      {r.status === 'pending' && (
                        <>
                          <button 
                            onClick={() => approveReturn(r.return_id)}
                            disabled={loading[r.return_id]}
                            style={{ 
                              padding: '4px 10px', 
                              background: loading[r.return_id] === 'approving' ? 'rgba(59,130,246,0.1)' : 'rgba(59,130,246,0.2)', 
                              border: '1px solid #3b82f6', 
                              borderRadius: '6px', 
                              color: '#3b82f6', 
                              cursor: loading[r.return_id] ? 'not-allowed' : 'pointer', 
                              fontSize: '0.8rem',
                              opacity: loading[r.return_id] ? 0.5 : 1
                            }}>
                            {loading[r.return_id] === 'approving' ? 'Approving...' : 'Approve'}
                          </button>
                          <button 
                            onClick={() => setRejectModal({ returnId: r.return_id, reason: '' })}
                            disabled={loading[r.return_id]}
                            style={{ 
                              padding: '4px 10px', 
                              background: 'rgba(239,68,68,0.2)', 
                              border: '1px solid #ef4444', 
                              borderRadius: '6px', 
                              color: '#ef4444', 
                              cursor: loading[r.return_id] ? 'not-allowed' : 'pointer', 
                              fontSize: '0.8rem',
                              opacity: loading[r.return_id] ? 0.5 : 1
                            }}>
                            Reject
                          </button>
                        </>
                      )}
                      {r.status === 'approved' && (
                        <button 
                          onClick={() => processRefund(r.return_id)}
                          disabled={loading[r.return_id]}
                          style={{ 
                            padding: '4px 10px', 
                            background: loading[r.return_id] === 'refunding' ? 'rgba(16,185,129,0.1)' : 'rgba(16,185,129,0.2)', 
                            border: '1px solid #10b981', 
                            borderRadius: '6px', 
                            color: '#10b981', 
                            cursor: loading[r.return_id] ? 'not-allowed' : 'pointer', 
                            fontSize: '0.8rem',
                            opacity: loading[r.return_id] ? 0.5 : 1
                          }}>
                          {loading[r.return_id] === 'refunding' ? 'Processing...' : 'Process Refund'}
                        </button>
                      )}
                      {(r.status === 'refunded' || r.status === 'rejected') && (
                        <span style={{ fontSize: '0.8rem', opacity: 0.5 }}>
                          {r.status === 'refunded' ? 'Completed' : 'Rejected'}
                        </span>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
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
    // JWT base64url uses '-' and '_' instead of '+' and '/', and omits '=' padding
    getAccessTokenSilently()
      .then(token => {
        try {
          const base64Url = token.split('.')[1];
          const base64    = base64Url.replace(/-/g, '+').replace(/_/g, '/');
          const padded    = base64.padEnd(base64.length + (4 - base64.length % 4) % 4, '=');
          const payload   = JSON.parse(atob(padded));
          const roles     = payload['https://mystore.com/roles'] || [];
          setAllowed(Array.isArray(roles) ? roles.includes('admin') : roles === 'admin');
        } catch {
          setAllowed(false);
        }
      })
      .catch(() => setAllowed(false));
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAuthenticated]);

  useEffect(() => {
    if (allowed && tab === 'dashboard') {
      adminFetch('/admin/dashboard', {}, getAccessTokenSilently, isAuthenticated)
        .then(d => { if (d.status === 'success') setStats(d.data); });
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
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
    { id: 'returns',   label: '↩️ Returns'   },
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
      {tab === 'returns'   && <ReturnsTab  getAccessTokenSilently={getAccessTokenSilently} isAuthenticated={isAuthenticated} />}
    </div>
  );
}
