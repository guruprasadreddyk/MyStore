import { useEffect, useState, useCallback } from 'react';
import { fetchProducts as fetchProductsApi, fetchSearchResults as fetchSearchResultsApi } from '../services/api';

// Known categories (matches seed data and DynamoDB GSI)
const KNOWN_CATEGORIES = ['All', 'Books', 'Electronics', 'Clothing', 'Home & Kitchen', 'Sports & Fitness'];

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

  const categories = KNOWN_CATEGORIES;

  // Fetch products — shows first page immediately, loads remaining in background
  const fetchProducts = useCallback(async () => {
    setLoading(true);

    try {
      // Fetch first page — display immediately
      const firstPage = await fetchProductsApi({
        lastEvaluatedKey: null,
        minPrice,
        maxPrice,
        category: selectedCategory,
        sortBy,
      });

      if (firstPage.status === 'success') {
        const firstProducts = firstPage.data.items || [];
        setProducts(firstProducts);
        setLoading(false); // UI is now interactive

        // Fetch remaining pages in background
        let currentKey = firstPage.data.lastEvaluatedKey || null;
        while (currentKey) {
          const data = await fetchProductsApi({
            lastEvaluatedKey: currentKey,
            minPrice,
            maxPrice,
            category: selectedCategory,
            sortBy,
          });

          if (data.status === 'success') {
            const newProducts = data.data.items || [];
            setProducts(prev => {
              const existingIds = new Set(prev.map(p => p.id));
              return [...prev, ...newProducts.filter(p => !existingIds.has(p.id))];
            });
            currentKey = data.data.lastEvaluatedKey || null;
          } else {
            break;
          }
        }
      }
    } catch (error) {
      console.error('Error fetching products:', error);
    } finally {
      setLoading(false);
      setLastEvaluatedKey(null);
    }
  }, [minPrice, maxPrice, selectedCategory, sortBy]);

  // Initial load
  useEffect(() => {
    fetchProducts();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Re-fetch when filters or sort change
  useEffect(() => {
    const timer = setTimeout(() => {
      fetchProducts();
    }, 300); // debounce filter changes

    return () => clearTimeout(timer);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedCategory, minPrice, maxPrice, sortBy]);

  // Search handler
  useEffect(() => {
    const query = searchQuery.trim();
    if (query === '') {
      setSearchResults(null);
      return;
    }

    const fetchSearchResults = async () => {
      setLoading(true);
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
          const items = data.data?.items ?? data.data;
          setSearchResults(Array.isArray(items) ? items : []);
        } else {
          console.error('Search error:', data.message);
          // Fallback: filter loaded products locally
          const queryLower = query.toLowerCase();
          setSearchResults(
            products.filter(
              (p) =>
                p.name.toLowerCase().includes(queryLower) ||
                (p.description || '').toLowerCase().includes(queryLower)
            )
          );
        }
      } catch (error) {
        console.error('Error searching products:', error);
        const queryLower = query.toLowerCase();
        setSearchResults(
          products.filter(
            (p) =>
              p.name.toLowerCase().includes(queryLower) ||
              (p.description || '').toLowerCase().includes(queryLower)
          )
        );
      } finally {
        setLoading(false);
      }
    };

    const debounce = setTimeout(fetchSearchResults, 300);
    return () => clearTimeout(debounce);
  }, [searchQuery, products, minPrice, maxPrice, selectedCategory, minRating, inStockOnly]);

  // Apply client-side filters on loaded data (rating + stock filters not supported server-side)
  useEffect(() => {
    let filtered = Array.isArray(searchResults)
      ? searchResults
      : Array.isArray(products)
      ? products
      : [];

    if (minRating) {
      filtered = filtered.filter((product) => (product.rating || 0) >= parseFloat(minRating));
    }

    if (inStockOnly) {
      filtered = filtered.filter((product) => (product.stock_quantity || 0) > 0);
    }

    setFilteredProducts(filtered);
  }, [products, searchResults, minRating, inStockOnly]);

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
