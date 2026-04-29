import React from 'react';
import { NavLink } from 'react-router-dom';
import { useAuth0 } from '@auth0/auth0-react';

const APP_NAME = 'MyStore';

function Navigation({ cartItemCount, wishlistCount, onOpenCart, searchQuery, setSearchQuery }) {
  const { loginWithRedirect, logout, user, isAuthenticated, isLoading } = useAuth0();

  return (
    <header className="App-header">
      <div className="brand-block">
        <h1>{APP_NAME}</h1>
        <p className="hero-subtitle">Shop smart, search fast, and checkout with confidence.</p>
      </div>
      <div className="nav-center" style={{ flexGrow: 1, margin: '0 32px', maxWidth: '400px' }}>
        <input
          type="text"
          placeholder="Search products..."
          value={searchQuery || ''}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="search-input"
          style={{ width: '100%' }}
        />
      </div>
      <nav>
        <NavLink to="/products" className={({ isActive }) => isActive ? 'active' : ''}>Products</NavLink>
        <NavLink to="/wishlist" className={({ isActive }) => isActive ? 'active' : ''}>
          Wishlist {wishlistCount > 0 && <span className="badge">{wishlistCount}</span>}
        </NavLink>
        <button className="nav-btn" onClick={onOpenCart} style={{ background: 'none', border: 'none', color: 'inherit', font: 'inherit', cursor: 'pointer', padding: '10px 20px' }}>
          Cart {cartItemCount > 0 && <span className="badge">{cartItemCount}</span>}
        </button>
        <NavLink to="/orders" className={({ isActive }) => isActive ? 'active' : ''}>Orders</NavLink>

        <div className="auth-section" style={{ display: 'inline-flex', alignItems: 'center', marginLeft: '20px' }}>
          {!isLoading && !isAuthenticated && (
            <button className="auth-btn login-btn" onClick={() => loginWithRedirect()}>Log In</button>
          )}
          {!isLoading && isAuthenticated && (
            <div className="user-profile" style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <img src={user.picture} alt={user.name} style={{ width: '30px', borderRadius: '50%' }} />
              <button className="auth-btn logout-btn" onClick={() => logout({ logoutParams: { returnTo: window.location.origin } })}>
                Log Out
              </button>
            </div>
          )}
        </div>
      </nav>
    </header>
  );
}

export default Navigation;
