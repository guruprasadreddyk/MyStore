import { useEffect, useState } from 'react';
import { useAuth0 } from '@auth0/auth0-react';
import {
  addToCart as addToCartApi,
  fetchCart as fetchCartApi,
  getHeaders,
  removeFromCart as removeFromCartApi
} from '../services/api';

export default function useCart() {
  const [cart, setCart] = useState([]);
  const [loading, setLoading] = useState(false);
  const { getAccessTokenSilently, isAuthenticated } = useAuth0();

  const loadCart = async () => {
    if (!isAuthenticated) return; // ✅ FIX: don’t wipe state

    setLoading(true);
    try {
      const headers = await getHeaders(isAuthenticated, getAccessTokenSilently);
      const data = await fetchCartApi(headers);

      if (data.status === 'success') {
        setCart(data.data || []); // ✅ FIX: safe fallback
      } else {
        console.warn("Cart fetch failed:", data.message);
      }
    } catch (error) {
      console.error('Error fetching cart:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCart();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAuthenticated]);

  const addToCart = async (productId, variantId) => {
    if (!isAuthenticated) {
      return { status: 'error', message: 'Authentication required' };
    }

    setLoading(true);
    try {
      const headers = await getHeaders(isAuthenticated, getAccessTokenSilently);
      const data = await addToCartApi(productId, variantId, headers);

      if (data.status === 'success') {
        setCart(data.data || []);
      }

      return data;
    } catch (error) {
      console.error('Error adding to cart:', error);
      return { status: 'error', message: 'Unable to add item to cart' };
    } finally {
      setLoading(false);
    }
  };

  const removeFromCart = async (productId, variantId = null) => {
    if (!isAuthenticated) {
      return { status: 'error', message: 'Authentication required' };
    }

    setLoading(true);
    try {
      const headers = await getHeaders(isAuthenticated, getAccessTokenSilently);
      const data = await removeFromCartApi(productId, headers, variantId);

      if (data.status === 'success') {
        setCart(data.data || []);
      }

      return data;
    } catch (error) {
      console.error('Error removing from cart:', error);
      return { status: 'error', message: 'Unable to remove item from cart' };
    } finally {
      setLoading(false);
    }
  };

  const getCartTotal = () =>
    cart.reduce((total, item) => total + item.price * item.quantity, 0);

  const getCartItemCount = () =>
    cart.reduce((total, item) => total + item.quantity, 0);

  return {
    cart,
    loading,
    addToCart,
    removeFromCart,
    loadCart,
    getCartTotal,
    getCartItemCount,
  };
}