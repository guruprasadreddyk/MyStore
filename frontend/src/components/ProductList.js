import React, { useState, useEffect } from 'react';
import ProductCard from './ProductCard';
import './ProductList.css';

function ProductList({
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
  minRating,
  setMinRating,
  inStockOnly,
  setInStockOnly,
  sortBy,
  setSortBy,
  recommendations,
  showRecommendations,
  toggleWishlist,
  isInWishlist,
  onQuickView
}) {
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 10;

  // Reset to page 1 when filters change
  useEffect(() => {
    setCurrentPage(1);
  }, [searchQuery, selectedCategory, minPrice, maxPrice, minRating, inStockOnly, sortBy]);

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
            <label>Minimum Rating</label>
            <select
              value={minRating || ''}
              onChange={(e) => setMinRating(e.target.value)}
              className="rating-select"
            >
              <option value="">All Ratings</option>
              <option value="4">4★ & above</option>
              <option value="3">3★ & above</option>
              <option value="2">2★ & above</option>
            </select>
          </div>
          <div className="filter-group">
            <label>
              <input
                type="checkbox"
                checked={inStockOnly}
                onChange={(e) => setInStockOnly(e.target.checked)}
              />
              {' '}In Stock Only
            </label>
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

          {/* Recommendations in sidebar when cart has items */}
          {showRecommendations && recommendations.length > 0 && (
            <div style={{ marginTop: '32px', borderTop: '1px solid rgba(255,255,255,0.08)', paddingTop: '24px' }}>
              <h4 style={{ marginBottom: '16px', fontSize: '0.85rem', opacity: 0.6, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                ✨ Recommended
              </h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                {recommendations.slice(0, 4).map((product) => (
                  <div
                    key={product.id}
                    onClick={() => onQuickView && onQuickView(product)}
                    style={{
                      display: 'flex', gap: '10px', alignItems: 'center',
                      cursor: 'pointer', padding: '8px', borderRadius: '8px',
                      background: 'rgba(255,255,255,0.03)',
                      border: '1px solid rgba(255,255,255,0.06)',
                      transition: 'background 0.15s',
                    }}
                    onMouseEnter={e => e.currentTarget.style.background = 'rgba(255,255,255,0.07)'}
                    onMouseLeave={e => e.currentTarget.style.background = 'rgba(255,255,255,0.03)'}
                  >
                    <img
                      src={product.image_url || 'https://via.placeholder.com/48x48?text=?'}
                      alt={product.name}
                      style={{ width: '40px', height: '40px', objectFit: 'cover', borderRadius: '6px', flexShrink: 0 }}
                    />
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <p style={{ fontSize: '0.8rem', fontWeight: 600, margin: 0, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                        {product.name}
                      </p>
                      <p style={{ fontSize: '0.75rem', opacity: 0.6, margin: '2px 0 0' }}>
                        ₹{product.price?.toLocaleString('en-IN')}
                      </p>
                    </div>
                    <button
                      onClick={(e) => { e.stopPropagation(); addToCart(product.id); }}
                      disabled={loading || product.stock_quantity <= 0}
                      style={{
                        padding: '4px 8px', fontSize: '0.7rem', fontWeight: 600,
                        background: 'rgba(59,130,246,0.2)', border: '1px solid rgba(59,130,246,0.4)',
                        borderRadius: '6px', color: '#60a5fa', cursor: 'pointer', flexShrink: 0,
                      }}
                    >
                      + Add
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </aside>

        <main className="catalog-main fade-in-up">
          {(searchQuery || selectedCategory !== 'All') && (
            <div className="status-banner">
              <span>{filteredProducts?.length || 0} results found</span>
              <span>
                {searchQuery
                  ? `Searching for "${searchQuery}"`
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

          {totalPages > 1 && (
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

          {/* Load more from server only when there are more pages to fetch */}
          {lastEvaluatedKey && (
            <div style={{ textAlign: 'center', marginTop: '24px' }}>
              <button
                onClick={() => fetchProducts(true)}
                disabled={loading}
                style={{
                  padding: '10px 28px',
                  background: 'rgba(59,130,246,0.15)',
                  border: '1px solid #3b82f6',
                  borderRadius: '8px',
                  color: '#3b82f6',
                  cursor: loading ? 'not-allowed' : 'pointer',
                  fontSize: '0.9rem',
                  fontWeight: 600,
                  opacity: loading ? 0.6 : 1,
                }}
              >
                {loading ? 'Loading…' : 'Load More Products'}
              </button>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}

export default ProductList;
