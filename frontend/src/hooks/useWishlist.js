import { useState, useEffect } from 'react';
import { useAuth0 } from '@auth0/auth0-react';
import { getHeaders, fetchWishlist, addToWishlistApi, removeFromWishlistApi } from '../services/api';

export default function useWishlist() {
  const [wishlist, setWishlist] = useState([]);
  const [loading, setLoading] = useState(false);
  const { getAccessTokenSilently, isAuthenticated } = useAuth0();

  const loadWishlist = async () => {
    if (!isAuthenticated) return;

    setLoading(true);
    try {
      const headers = await getHeaders(isAuthenticated, getAccessTokenSilently);
      const data = await fetchWishlist(headers);

      if (data.status === 'success') {
        setWishlist(data.data || []);
      }
    } catch (error) {
      console.error('Error fetching wishlist:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadWishlist();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAuthenticated]);

  const toggleWishlist = async (product) => {
    if (!isAuthenticated) {
      return { status: 'error', message: 'Authentication required to use wishlist' };
    }

    const isWishlisted = wishlist.some(item => item.id === product.id);
    
    // Optimistic UI update
    setWishlist(prev => {
      if (isWishlisted) {
        return prev.filter(item => item.id !== product.id);
      } else {
        return [...prev, product];
      }
    });

    try {
      const headers = await getHeaders(isAuthenticated, getAccessTokenSilently);
      let data;
      if (isWishlisted) {
        data = await removeFromWishlistApi(product.id, headers);
      } else {
        data = await addToWishlistApi(product.id, headers);
      }

      if (data.status === 'success') {
        setWishlist(data.data || []);
      } else {
        // Revert on failure
        loadWishlist();
      }
      return data;
    } catch (error) {
      console.error('Error toggling wishlist:', error);
      loadWishlist(); // Revert on error
      return { status: 'error', message: 'Unable to update wishlist' };
    }
  };

  const isInWishlist = (productId) => wishlist.some(item => String(item.id) === String(productId));

  return { wishlist, toggleWishlist, isInWishlist, loading, loadWishlist };
}
