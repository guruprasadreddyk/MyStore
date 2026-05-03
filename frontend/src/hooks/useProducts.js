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
  const [sortBy, setSortBy] = useState('');
  const [loading, setLoading] = useState(false);

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
        const data = await fetchSearchResultsApi(query);
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
  }, [searchQuery, products]);

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

    if (sortBy === 'price_low_high') {
      filtered = [...filtered].sort((a, b) => a.price - b.price);
    } else if (sortBy === 'price_high_low') {
      filtered = [...filtered].sort((a, b) => b.price - a.price);
    }

    setFilteredProducts(filtered || []);
  }, [products, searchResults, selectedCategory, minPrice, maxPrice, sortBy]);

  const fetchProducts = async () => {
    setLoading(true);
    let allFetchedProducts = [];
    let currentKey = null;
    let hasMore = true;

    try {
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
          const existingIds = new Set(allFetchedProducts.map(p => p.id));
          const newUniqueProducts = newProducts.filter(p => !existingIds.has(p.id));
          allFetchedProducts = [...allFetchedProducts, ...newUniqueProducts];
          
          currentKey = data.data.lastEvaluatedKey || null;
          hasMore = !!currentKey;
        } else {
          hasMore = false;
        }
      }
      setProducts(allFetchedProducts);
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
    sortBy,
    setSortBy,
    fetchProducts,
    adjustProductStock,
  };
}
