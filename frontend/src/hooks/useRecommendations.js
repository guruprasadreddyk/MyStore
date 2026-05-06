import { useEffect, useRef, useState } from 'react';
import { fetchRecommendations as fetchRecommendationsApi, fetchProducts } from '../services/api';

export default function useRecommendations(cart, orders = [], wishlist = [], searchQuery = '') {
  const [recommendations, setRecommendations] = useState([]);
  const lastFetchedIds = useRef('');

  useEffect(() => {
    const fetchRecommendations = async () => {
      // 1. Cart items
      const cartIds = cart.map((item) => String(item.id));

      // 2. Past order items
      const orderIds = orders.flatMap((order) =>
        (order.items || []).map((item) => String(item.id))
      );

      // 3. Wishlist items
      const wishlistIds = wishlist.map((item) => String(item.id));

      // 4. Search query — seed from cart/wishlist items matching the query
      const searchIds = searchQuery.trim().length >= 2
        ? [...cart, ...wishlist]
            .filter((p) =>
              p.name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
              p.category?.toLowerCase().includes(searchQuery.toLowerCase())
            )
            .map((p) => String(p.id))
        : [];

      const allIds = [...new Set([...cartIds, ...orderIds, ...wishlistIds, ...searchIds])];
      const idsKey = allIds.sort().join(',');

      // Skip if nothing changed
      if (idsKey === lastFetchedIds.current) return;
      lastFetchedIds.current = idsKey;

      try {
        if (allIds.length > 0) {
          // Personalised recommendations based on user activity
          const data = await fetchRecommendationsApi(allIds.join(','), 8);
          if (data.status === 'success' && data.data?.length > 0) {
            setRecommendations(data.data);
            return;
          }
        }

        // Fallback: no activity yet — show top-rated products
        const fallback = await fetchProducts({ sortBy: 'price_high_low' });
        if (fallback.status === 'success') {
          const items = (fallback.data?.items || [])
            .sort((a, b) => (b.rating || 0) - (a.rating || 0))
            .slice(0, 8);
          setRecommendations(items);
        }
      } catch (error) {
        console.error('Error fetching recommendations:', error);
      }
    };

    fetchRecommendations();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cart, orders, wishlist, searchQuery]);

  // Always show — recommendations are permanent
  return { recommendations, showRecommendations: recommendations.length > 0 };
}
