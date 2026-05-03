import React, { useState, useEffect, useRef } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth0 } from '@auth0/auth0-react';

const APP_NAME = 'MyStore';

function Navigation({ cartItemCount, wishlistCount, onOpenCart, searchQuery, setSearchQuery }) {
  const { loginWithRedirect, logout, user, isAuthenticated, isLoading, getAccessTokenSilently } = useAuth0();
  const [menuOpen, setMenuOpen] = useState(false);
  const [isAdmin, setIsAdmin]   = useState(false);
  const menuRef  = useRef(null);
  const navigate = useNavigate();

  // ── Detect admin role from JWT ──────────────────────────────────────────────
  useEffect(() => {
    if (!isAuthenticated) { setIsAdmin(false); return; }
    getAccessTokenSilently()
      .then(token => {
        try {
          const payload = JSON.parse(atob(token.split('.')[1]));
          const roles   = payload['https://mystore.com/roles'] || [];
          setIsAdmin(Array.isArray(roles) ? roles.includes('admin') : roles === 'admin');
        } catch { setIsAdmin(false); }
      })
      .catch(() => setIsAdmin(false));
  }, [isAuthenticated, getAccessTokenSilently]);

  // ── Close menu on outside click ─────────────────────────────────────────────
  useEffect(() => {
    const handler = (e) => {
      if (menuRef.current && !menuRef.current.contains(e.target)) {
        setMenuOpen(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const menuItem = (icon, label, onClick) => (
    <button
      onClick={() => { setMenuOpen(false); onClick(); }}
      style={{
        display: 'flex', alignItems: 'center', gap: '12px',
        width: '100%', padding: '11px 16px', background: 'transparent',
        border: 'none', color: 'rgba(255,255,255,0.85)', cursor: 'pointer',
        fontSize: '0.9rem', textAlign: 'left', borderRadius: '8px',
        transition: 'background 0.15s'
      }}
      onMouseEnter={e => e.currentTarget.style.background = 'rgba(255,255,255,0.07)'}
      onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
    >
      <span style={{ fontSize: '1rem', width: '20px', textAlign: 'center' }}>{icon}</span>
      {label}
    </button>
  );

  const divider = () => (
    <div style={{ height: '1px', background: 'rgba(255,255,255,0.08)', margin: '6px 0' }} />
  );

  return (
    <header className="App-header">
      {/* Brand */}
      <div className="brand-block">
        <h1>{APP_NAME}</h1>
        <p className="hero-subtitle">Shop smart, search fast, and checkout with confidence.</p>
      </div>

      {/* Search */}
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

      {/* Nav links */}
      <nav>
        <NavLink to="/products" className={({ isActive }) => isActive ? 'active' : ''}>Products</NavLink>

        <NavLink to="/wishlist" className={({ isActive }) => isActive ? 'active' : ''}>
          Wishlist {wishlistCount > 0 && <span className="badge">{wishlistCount}</span>}
        </NavLink>

        <button
          className="nav-btn"
          onClick={onOpenCart}
          style={{ background: 'none', border: 'none', color: 'inherit', font: 'inherit', cursor: 'pointer', padding: '10px 20px' }}
        >
          Cart {cartItemCount > 0 && <span className="badge">{cartItemCount}</span>}
        </button>

        <NavLink to="/orders" className={({ isActive }) => isActive ? 'active' : ''}>Orders</NavLink>

        {/* Account section */}
        <div style={{ position: 'relative', marginLeft: '8px' }} ref={menuRef}>
          {!isLoading && !isAuthenticated && (
            <button className="auth-btn login-btn" onClick={() => loginWithRedirect()}>
              Log In
            </button>
          )}

          {!isLoading && isAuthenticated && (
            <>
              {/* Avatar button — avatar + chevron only */}
              <button
                onClick={() => setMenuOpen(o => !o)}
                style={{
                  display: 'flex', alignItems: 'center', gap: '6px',
                  background: menuOpen ? 'rgba(255,255,255,0.1)' : 'rgba(255,255,255,0.05)',
                  border: '1px solid rgba(255,255,255,0.15)',
                  borderRadius: '999px', padding: '4px 8px 4px 4px',
                  cursor: 'pointer', transition: 'all 0.2s'
                }}
              >
                <img
                  src={user.picture}
                  alt={user.name}
                  style={{ width: '30px', height: '30px', borderRadius: '50%', objectFit: 'cover' }}
                />
                <span style={{ color: 'rgba(255,255,255,0.4)', fontSize: '0.6rem' }}>
                  {menuOpen ? '▲' : '▼'}
                </span>
              </button>

              {/* Dropdown menu */}
              {menuOpen && (
                <div style={{
                  position: 'absolute', top: 'calc(100% + 10px)', right: 0,
                  width: '240px', zIndex: 500,
                  background: 'rgba(18,18,28,0.97)',
                  backdropFilter: 'blur(24px)',
                  border: '1px solid rgba(255,255,255,0.12)',
                  borderRadius: '14px',
                  boxShadow: '0 20px 60px rgba(0,0,0,0.6)',
                  overflow: 'hidden',
                  animation: 'fadeUp 0.15s ease-out'
                }}>
                  {/* User info header */}
                  <div style={{ padding: '16px', borderBottom: '1px solid rgba(255,255,255,0.08)' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                      <img
                        src={user.picture}
                        alt={user.name}
                        style={{ width: '40px', height: '40px', borderRadius: '50%', objectFit: 'cover' }}
                      />
                      <div style={{ overflow: 'hidden' }}>
                        <p style={{ margin: 0, fontWeight: 600, fontSize: '0.9rem', color: '#fff', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                          {user.name}
                        </p>
                        <p style={{ margin: 0, fontSize: '0.75rem', color: 'rgba(255,255,255,0.45)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                          {user.email}
                        </p>
                      </div>
                    </div>
                    {isAdmin && (
                      <div style={{ marginTop: '10px', display: 'inline-flex', alignItems: 'center', gap: '5px', background: 'rgba(59,130,246,0.15)', border: '1px solid rgba(59,130,246,0.3)', borderRadius: '20px', padding: '3px 10px', fontSize: '0.72rem', color: '#60a5fa', fontWeight: 600 }}>
                        ⚡ Admin
                      </div>
                    )}
                  </div>

                  {/* Menu items */}
                  <div style={{ padding: '6px' }}>
                    {menuItem('🛒', 'My Orders',        () => navigate('/orders'))}
                    {menuItem('❤️', 'Wishlist',         () => navigate('/wishlist'))}
                    {menuItem('📦', 'Track Order',      () => navigate('/orders'))}
                    {divider()}
                    {menuItem('👤', 'My Profile',       () => navigate('/profile'))}
                    {menuItem('📍', 'Saved Addresses',  () => navigate('/addresses'))}
                    {menuItem('💳', 'Payment Methods',  () => navigate('/payment-methods'))}
                    {menuItem('🔔', 'Notifications',    () => navigate('/notifications'))}
                    {divider()}
                    {isAdmin && menuItem('⚙️', 'Admin Panel', () => navigate('/admin'))}
                    {menuItem('❓', 'Help & Support', () => window.open('mailto:support@mystore.com'))}
                    {divider()}
                    <button
                      onClick={() => { setMenuOpen(false); logout({ logoutParams: { returnTo: window.location.origin } }); }}
                      style={{
                        display: 'flex', alignItems: 'center', gap: '12px',
                        width: '100%', padding: '11px 16px', background: 'transparent',
                        border: 'none', color: '#ef4444', cursor: 'pointer',
                        fontSize: '0.9rem', textAlign: 'left', borderRadius: '8px',
                        transition: 'background 0.15s'
                      }}
                      onMouseEnter={e => e.currentTarget.style.background = 'rgba(239,68,68,0.08)'}
                      onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
                    >
                      <span style={{ fontSize: '1rem', width: '20px', textAlign: 'center' }}>🚪</span>
                      Log Out
                    </button>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </nav>
    </header>
  );
}

export default Navigation;
