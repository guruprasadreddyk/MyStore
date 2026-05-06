import { useEffect, useMemo, useState } from 'react';
import { fetchProducts as fetchProductsApi, fetchSearchResults as fetchSearchResultsApi } from '../services/api';

export default function useProducts() {
  const [products, setProducts] = useState([]);
  const [filteredProducts, setFilteredProducts] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState(null);
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [minPrice, setMinPrice] = useState('');
  const [maxPrice, setMaxPrice] = useState('');
  const [minRating, setMinRating] = useState('');
  const [inStockOnly, setInStockOnly] = useState(false);
  const [sortBy, setSortBy] = useState('');
  const [loading, setLoading] = useState(false);
  const [lastEvaluatedKey, setLastEvaluatedKey] = useState(null);

  const categories = useMemo(
    () => ['All', ...new Set(products.map((product) => product.category))],
    [products]
  );

  useEffect(() => {
    fetchProducts();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    const query = searchQuery.trim();
    if (query === '') {
      setSearchResults(null);
      return;
    }

    const fetchSearchResults = async () => {
      setLoading(true);
      const queryLower = query.toLowerCase();
      const localFallback = products.filter(
        (product) =>
          product.name.toLowerCase().includes(queryLower) ||
          product.description.toLowerCase().includes(queryLower)
      );

      try {
        const filters = {
          minPrice,
          maxPrice,
          category: selectedCategory !== 'All' ? selectedCategory : undefined,
          minRating: minRating || undefined,
          inStockOnly: inStockOnly || undefined,
        };
        
        const data = await fetchSearchResultsApi(query, filters);
        if (data.status === 'success') {
          // API returns { items: [...], lastEvaluatedKey, total }
          const items = data.data?.items ?? data.data;
          setSearchResults(Array.isArray(items) ? items : localFallback);
        } else {
          console.error('Search error:', data.message);
          setSearchResults(localFallback);
        }
      } catch (error) {
        console.error('Error searching products:', error);
        setSearchResults(localFallback);
      } finally {
        setLoading(false);
      }
    };

    fetchSearchResults();
  }, [searchQuery, products, minPrice, maxPrice, selectedCategory, minRating, inStockOnly]);

  useEffect(() => {
    let filtered = Array.isArray(searchResults)
  ? searchResults
  : Array.isArray(products)
  ? products
  : [];

    if (selectedCategory !== 'All') {
      filtered = filtered.filter((product) => product.category === selectedCategory);
    }

    if (minPrice) {
      filtered = filtered.filter((product) => product.price >= parseFloat(minPrice));
    }

    if (maxPrice) {
      filtered = filtered.filter((product) => product.price <= parseFloat(maxPrice));
    }

    if (minRating) {
      filtered = filtered.filter((product) => (product.rating || 0) >= parseFloat(minRating));
    }

    if (inStockOnly) {
      filtered = filtered.filter((product) => (product.stock_quantity || 0) > 0);
    }

    if (sortBy === 'price_low_high') {
      filtered = [...filtered].sort((a, b) => a.price - b.price);
    } else if (sortBy === 'price_high_low') {
      filtered = [...filtered].sort((a, b) => b.price - a.price);
    }

    setFilteredProducts(filtered || []);
  }, [products, searchResults, selectedCategory, minPrice, maxPrice, minRating, inStockOnly, sortBy]);

  const fetchProducts = async (loadMore = false) => {
    setLoading(true);
    const startKey = loadMore ? lastEvaluatedKey : null;

    try {
      // On initial load, fetch all pages automatically so the full catalog is available
      // for client-side filtering and pagination. On "Load More", fetch one page at a time.
      if (loadMore) {
        const data = await fetchProductsApi({
          lastEvaluatedKey: startKey,
          minPrice,
          maxPrice,
          category: selectedCategory,
          sortBy,
        });
        if (data.status === 'success') {
          const newProducts = data.data.items || [];
          const existingIds = new Set(products.map(p => p.id));
          const unique = newProducts.filter(p => !existingIds.has(p.id));
          setProducts(prev => [...prev, ...unique]);
          setLastEvaluatedKey(data.data.lastEvaluatedKey || null);
        }
      } else {
        // Fetch all pages on initial load
        let allProducts = [];
        let currentKey = null;
        let hasMore = true;
        while (hasMore) {
          const data = await fetchProductsApi({
            lastEvaluatedKey: currentKey,
            minPrice,
            maxPrice,
            category: selectedCategory,
            sortBy,
          });
          if (data.status === 'success') {
            const newProducts = data.data.items || [];
            const existingIds = new Set(allProducts.map(p => p.id));
            allProducts = [...allProducts, ...newProducts.filter(p => !existingIds.has(p.id))];
            currentKey = data.data.lastEvaluatedKey || null;
            hasMore = !!currentKey;
          } else {
            hasMore = false;
          }
        }
        setProducts(allProducts);
        setLastEvaluatedKey(null); // all pages loaded, no more to fetch
      }
    } catch (error) {
      console.error('Error fetching products:', error);
    } finally {
      setLoading(false);
    }
  };

  const adjustProductStock = (cartItems) => {
    setProducts((prevProducts) =>
      prevProducts.map((product) => {
        const cartItem = cartItems.find((item) => item.id === product.id);
        if (!cartItem) return product;

        return {
          ...product,
          stock_quantity: Math.max(product.stock_quantity - cartItem.quantity, 0),
        };
      })
    );
  };

  return {
    products,
    filteredProducts,
    categories,
    loading,
    searchQuery,
    setSearchQuery,
    selectedCategory,
    setSelectedCategory,
    minPrice,
    setMinPrice,
    maxPrice,
    setMaxPrice,
    minRating,
    setMinRating,
    inStockOnly,
    setInStockOnly,
    sortBy,
    setSortBy,
    lastEvaluatedKey,
    fetchProducts,
    adjustProductStock,
  };
}
