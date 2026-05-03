import { useEffect, useState } from 'react';
import { useAuth0 } from '@auth0/auth0-react';
import {
  fetchOrders as fetchOrdersApi,
  getHeaders,
  placeOrder as placeOrderApi,
  processPayment as processPaymentApi,
  cancelOrder as cancelOrderApi
} from '../services/api';

export default function useOrders() {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(false);
  const { getAccessTokenSilently, isAuthenticated } = useAuth0();

  const loadOrders = async () => {
    if (!isAuthenticated) return; // ✅ FIX

    setLoading(true);
    try {
      const headers = await getHeaders(isAuthenticated, getAccessTokenSilently);
      const data = await fetchOrdersApi(headers);

      if (data.status === 'success') {
        setOrders(data.data || []); // ✅ safe fallback
      } else {
        console.warn("Orders fetch failed:", data.message);
      }
    } catch (error) {
      console.error('Error fetching orders:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadOrders();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAuthenticated]);

  const placeOrder = async (items, address) => {
    if (!isAuthenticated) {
      return { status: 'error', message: 'Authentication required' };
    }

    setLoading(true);
    try {
      const headers = await getHeaders(isAuthenticated, getAccessTokenSilently);
      const data = await placeOrderApi(items, address, headers);

      if (data.status === 'success') {
        loadOrders();
      }

      return data;
    } catch (error) {
      console.error('Error placing order:', error);
      return { status: 'error', message: 'Unable to place order' };
    } finally {
      setLoading(false);
    }
  };

  const processPayment = async (orderId, total) => {
    if (!isAuthenticated) {
      return { status: 'error', message: 'Authentication required' };
    }

    setLoading(true);
    try {
      const headers = await getHeaders(isAuthenticated, getAccessTokenSilently);
      const data = await processPaymentApi(orderId, total, headers);

      if (data.status === 'success') {
        loadOrders();
      }

      return data;
    } catch (error) {
      console.error('Error processing payment:', error);
      return { status: 'error', message: 'Unable to process payment' };
    } finally {
      setLoading(false);
    }
  };

  const cancelOrder = async (orderId) => {
    if (!isAuthenticated) {
      return { status: 'error', message: 'Authentication required' };
    }
    setLoading(true);
    try {
      const headers = await getHeaders(isAuthenticated, getAccessTokenSilently);
      const data = await cancelOrderApi(orderId, headers);
      if (data.status === 'success') loadOrders();
      return data;
    } catch (error) {
      console.error('Error cancelling order:', error);
      return { status: 'error', message: 'Unable to cancel order' };
    } finally {
      setLoading(false);
    }
  };

  return {
    orders,
    loading,
    loadOrders,
    placeOrder,
    processPayment,
    cancelOrder,
  };
}