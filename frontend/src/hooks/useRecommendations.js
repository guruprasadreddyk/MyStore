import { useEffect, useState } from 'react';
import { fetchRecommendations as fetchRecommendationsApi } from '../services/api';

export default function useRecommendations(cart) {
  const [recommendations, setRecommendations] = useState([]);
  const [showRecommendations, setShowRecommendations] = useState(false);

  useEffect(() => {
    const fetchRecommendations = async () => {
      if (cart.length === 0) {
        setRecommendations([]);
        setShowRecommendations(false);
        return;
      }

      const productIds = cart.map((item) => item.id).join(',');

      try {
        const data = await fetchRecommendationsApi(productIds, 5);
        if (data.status === 'success') {
          setRecommendations(data.data);
          setShowRecommendations(true);
        } else {
          console.error('Error fetching recommendations:', data.message);
          setRecommendations([]);
          setShowRecommendations(false);
        }
      } catch (error) {
        console.error('Error fetching recommendations:', error);
        setRecommendations([]);
        setShowRecommendations(false);
      }
    };

    fetchRecommendations();
  }, [cart]);

  return {
    recommendations,
    showRecommendations,
  };
}
