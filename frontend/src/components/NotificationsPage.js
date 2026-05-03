import React from 'react';
import { useAuth0 } from '@auth0/auth0-react';
import { useNavigate } from 'react-router-dom';

const STATUS_ICONS = {
  created:   { icon: '🛒', color: '#f59e0b', label: 'Order Placed'    },
  paid:      { icon: '✅', color: '#10b981', label: 'Payment Confirmed' },
  shipped:   { icon: '🚚', color: '#06b6d4', label: 'Order Shipped'   },
  delivered: { icon: '📦', color: '#10b981', label: 'Delivered'       },
  cancelled: { icon: '❌', color: '#ef4444', label: 'Order Cancelled'  },
};

function NotificationsPage({ orders = [] }) {
  const { isAuthenticated, loginWithRedirect } = useAuth0();
  const navigate = useNavigate();

  if (!isAuthenticated) return (
    <div style={{ padding: '60px 24px', textAlign: 'center' }}>
      <p style={{ opacity: 0.5, marginBottom: '16px' }}>Please log in to view notifications.</p>
      <button className="btn-primary" style={{ width: 'auto', padding: '12px 32px' }} onClick={() => loginWithRedirect()}>Log In</button>
    </div>
  );

  // Generate notifications from order history — one notification per order status
  const notifications = orders
    .flatMap(order => {
      const events = [];
      const statusInfo = STATUS_ICONS[order.status] || { icon: '📋', color: '#fff', label: order.status };
      const grandTotal = order.grand_total ?? order.items?.reduce((s, i) => s + i.price * i.quantity, 0) ?? 0;

      events.push({
        id:      `${order.order_id}-${order.status}`,
        icon:    statusInfo.icon,
        color:   statusInfo.color,
        title:   statusInfo.label,
        body:    `Order #${order.order_id?.slice(0, 8).toUpperCase()} · ₹${grandTotal.toLocaleString('en-IN')}`,
        orderId: order.order_id,
        read:    order.status === 'delivered' || order.status === 'cancelled'
      });

      return events;
    })
    .reverse(); // most recent first

  return (
    <div style={{ maxWidth: '600px', margin: '0 auto', padding: '40px 24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '28px' }}>
        <h2 style={{ fontSize: '1.6rem', margin: 0 }}>Notifications</h2>
        {notifications.length > 0 && (
          <span style={{ fontSize: '0.8rem', opacity: 0.4 }}>{notifications.length} total</span>
        )}
      </div>

      {notifications.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '60px', opacity: 0.35 }}>
          <p style={{ fontSize: '2.5rem', marginBottom: '12px' }}>🔔</p>
          <p>No notifications yet.</p>
          <p style={{ fontSize: '0.85rem' }}>Order updates will appear here.</p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {notifications.map(n => (
            <div
              key={n.id}
              onClick={() => navigate('/orders')}
              style={{
                display: 'flex', alignItems: 'center', gap: '14px',
                padding: '14px 16px', borderRadius: '12px', cursor: 'pointer',
                background: n.read ? 'rgba(255,255,255,0.02)' : 'rgba(255,255,255,0.05)',
                border: `1px solid ${n.read ? 'rgba(255,255,255,0.06)' : 'rgba(255,255,255,0.12)'}`,
                transition: 'background 0.15s'
              }}
              onMouseEnter={e => e.currentTarget.style.background = 'rgba(255,255,255,0.07)'}
              onMouseLeave={e => e.currentTarget.style.background = n.read ? 'rgba(255,255,255,0.02)' : 'rgba(255,255,255,0.05)'}
            >
              <div style={{ width: '40px', height: '40px', borderRadius: '50%', background: `${n.color}22`, border: `1px solid ${n.color}44`, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1.1rem', flexShrink: 0 }}>
                {n.icon}
              </div>
              <div style={{ flex: 1, minWidth: 0 }}>
                <p style={{ margin: '0 0 2px', fontWeight: n.read ? 400 : 600, fontSize: '0.9rem', color: n.color }}>{n.title}</p>
                <p style={{ margin: 0, fontSize: '0.8rem', opacity: 0.55, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{n.body}</p>
              </div>
              {!n.read && (
                <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: n.color, flexShrink: 0 }} />
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default NotificationsPage;
