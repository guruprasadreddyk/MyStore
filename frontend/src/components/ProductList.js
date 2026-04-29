import React, { useState, useEffect } from 'react';
import ProductCard from './ProductCard';

function ProductList({
  products,
  searchQuery,
  setSearchQuery,
  selectedCategory,
  setSelectedCategory,
  loading,
  addToCart,
  categories,
  filteredProducts,
  fetchProducts,
  lastEvaluatedKey,
  minPrice,
  setMinPrice,
  maxPrice,
  setMaxPrice,
  sortBy,
  setSortBy,
  recommendations,
  showRecommendations,
  toggleWishlist,
  isInWishlist,
  onQuickView
}) {
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 8;

  // Reset to page 1 when filters change
  useEffect(() => {
    setCurrentPage(1);
  }, [searchQuery, selectedCategory, minPrice, maxPrice, sortBy]);

  const totalPages = Math.ceil((filteredProducts?.length || 0) / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const currentItems = filteredProducts?.slice(startIndex, startIndex + itemsPerPage) || [];

  return (
    <div className="catalog-container">
      <div className="catalog-layout">
        <aside className="catalog-sidebar glass-panel">
          <h3>Filters</h3>
          <div className="filter-group">
            <label>Category</label>
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="category-select"
            >
              {(categories || []).map(category => (
                <option key={category} value={category}>{category}</option>
              ))}
            </select>
          </div>
          <div className="filter-group">
            <label>Price Range</label>
            <div className="price-filter">
              <input
                type="number"
                placeholder="Min"
                value={minPrice}
                onChange={(e) => setMinPrice(e.target.value)}
                className="price-input"
                min="0"
              />
              <input
                type="number"
                placeholder="Max"
                value={maxPrice}
                onChange={(e) => setMaxPrice(e.target.value)}
                className="price-input"
                min="0"
              />
            </div>
          </div>
          <div className="filter-group">
            <label>Sort By</label>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="sort-select"
            >
              <option value="">Default</option>
              <option value="price_low_high">Price: Low to High</option>
              <option value="price_high_low">Price: High to Low</option>
            </select>
          </div>
        </aside>

        <main className="catalog-main fade-in-up">
          {(searchQuery || selectedCategory !== 'All') && (
            <div className="status-banner">
              <span>{filteredProducts?.length || 0} results found</span>
              <span>
                {searchQuery
                  ? `Searching for “${searchQuery}”`
                  : 'Showing all filtered products'}
              </span>
            </div>
          )}
          
          <div className="product-grid">
            {currentItems.map((product, index) => (
              <ProductCard
                key={product.id}
                product={product}
                addToCart={addToCart}
                loading={loading}
                toggleWishlist={toggleWishlist}
                isWishlisted={isInWishlist(product.id)}
                index={index}
                onQuickView={onQuickView}
              />
            ))}
          </div>

          {totalPages > 0 && (
            <div className="pagination">
              {Array.from({ length: totalPages }, (_, i) => i + 1).map(page => (
                <button
                  key={page}
                  className={`page-btn ${currentPage === page ? 'active' : ''}`}
                  onClick={() => setCurrentPage(page)}
                >
                  {page}
                </button>
              ))}
            </div>
          )}
        </main>
      </div>
      {showRecommendations && recommendations.length > 0 && (
        <div className="recommendations-section">
          <h3>Recommended for You</h3>
          <div className="recommendations-grid">
            {recommendations.map((product, index) => (
              <ProductCard
                key={product.id}
                product={product}
                addToCart={addToCart}
                loading={loading}
                toggleWishlist={toggleWishlist}
                isWishlisted={isInWishlist(product.id)}
                index={index}
                onQuickView={onQuickView}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default ProductList;
