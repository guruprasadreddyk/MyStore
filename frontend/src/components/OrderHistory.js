import React from 'react';

function OrderHistory({ orders, loading, processPayment }) {
  return (
    <div className="orders">
      <h2>Your Orders</h2>
      {orders.length === 0 ? (
        <p>No orders yet</p>
      ) : (
        <div className="order-list">
          {orders.map(order => (
            <div key={order.order_id} className="order-card">
              <h3>Order ID: {order.order_id}</h3>
              <p>Status: {order.status}</p>
              <div className="order-items">
                {order.items.map(item => (
                  <div key={item.id} className="order-item">
                    <span>{item.name}</span>
                    <span>Qty: {item.quantity}</span>
                    <span>₹{(item.price * item.quantity).toLocaleString('en-IN')}</span>
                  </div>
                ))}
              </div>
              <p className="order-total">
                Total: ₹{order.items.reduce((sum, item) => sum + (item.price * item.quantity), 0).toLocaleString('en-IN')}
              </p>
              {order.status === 'created' && (
                <button
                  onClick={() => processPayment(order.order_id)}
                  disabled={loading}
                  className="pay-btn"
                >
                  Pay Now
                </button>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default OrderHistory;
