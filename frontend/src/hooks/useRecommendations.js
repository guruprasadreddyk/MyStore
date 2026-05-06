import { useEffect, useRef, useState } from 'react';
import { fetchRecommendations as fetchRecommendationsApi } from '../services/api';

export default function useRecommendations(cart, orders = []) {
  const [recommendations, setRecommendations] = useState([]);
  const [showRecommendations, setShowRecommendations] = useState(false);
  // Track the last set of product IDs we fetched for — avoid redundant API calls
  const lastFetchedIds = useRef('');

  useEffect(() => {
    const fetchRecommendations = async () => {
      // Collect product IDs from cart
      const cartIds = cart.map((item) => String(item.id));

      // Collect product IDs from all past orders
      const orderIds = orders.flatMap((order) =>
        (order.items || []).map((item) => String(item.id))
      );

      // Deduplicate and combine
      const allIds = [...new Set([...cartIds, ...orderIds])];

      if (allIds.length === 0) {
        // No cart items and no order history — nothing to recommend from
        // But keep existing recommendations visible if we already have some
        if (recommendations.length === 0) {
          setShowRecommendations(false);
        }
        return;
      }

      const idsKey = allIds.sort().join(',');

      // Skip fetch if the product pool hasn't changed
      if (idsKey === lastFetchedIds.current) return;
      lastFetchedIds.current = idsKey;

      try {
        const data = await fetchRecommendationsApi(allIds.join(','), 6);
        if (data.status === 'success' && data.data?.length > 0) {
          setRecommendations(data.data);
          setShowRecommendations(true);
        }
        // On failure, keep whatever recommendations we already have
      } catch (error) {
        console.error('Error fetching recommendations:', error);
        // Keep existing recommendations on error
      }
    };

    fetchRecommendations();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cart, orders]);

  return { recommendations, showRecommendations };
}
