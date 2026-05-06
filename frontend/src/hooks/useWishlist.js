import { useState, useEffect } from 'react';
import { useAuth0 } from '@auth0/auth0-react';
import { getHeaders, fetchWishlist, addToWishlistApi, removeFromWishlistApi, fetchProductById } from '../services/api';

export default function useWishlist() {
  const [wishlist, setWishlist] = useState([]);
  const [loading, setLoading] = useState(false);
  const { getAccessTokenSilently, isAuthenticated } = useAuth0();

  // Enrich wishlist items that are missing variants/stock data
  // (items saved before the backend fix won't have these fields)
  const enrichWishlist = async (items) => {
    const enriched = await Promise.all(
      items.map(async (item) => {
        // Already has full data — no need to fetch
        if (item.variants !== undefined && item.stock_quantity !== undefined) {
          return item;
        }
        try {
          const res = await fetchProductById(item.id);
          if (res.status === 'success' && res.data) {
            // Merge fresh product data with stored wishlist item
            return {
              ...res.data,
              id: item.id, // keep as string to be safe
            };
          }
        } catch {
          // If fetch fails, return the item as-is
        }
        return item;
      })
    );
    return enriched;
  };

  const loadWishlist = async () => {
    if (!isAuthenticated) return;

    setLoading(true);
    try {
      const headers = await getHeaders(isAuthenticated, getAccessTokenSilently);
      const data = await fetchWishlist(headers);

      if (data.status === 'success') {
        const items = data.data || [];
        // Enrich items missing variants/stock before setting state
        const enriched = await enrichWishlist(items);
        setWishlist(enriched);
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
        // Enrich the returned items too
        const enriched = await enrichWishlist(data.data || []);
        setWishlist(enriched);
      } else {
        loadWishlist();
      }
      return data;
    } catch (error) {
      console.error('Error toggling wishlist:', error);
      loadWishlist();
      return { status: 'error', message: 'Unable to update wishlist' };
    }
  };

  const isInWishlist = (productId) => wishlist.some(item => String(item.id) === String(productId));

  return { wishlist, toggleWishlist, isInWishlist, loading, loadWishlist };
}
