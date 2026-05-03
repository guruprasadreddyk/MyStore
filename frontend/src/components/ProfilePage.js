import React, { useEffect, useState } from 'react';
import { useAuth0 } from '@auth0/auth0-react';
import { fetchProfile, updateProfile, sendVerificationEmail, getHeaders } from '../services/api';

function ProfilePage() {
  const { user, isAuthenticated, loginWithRedirect, logout, getAccessTokenSilently } = useAuth0();
  const [editing, setEditing]             = useState(false);
  const [profile, setProfile]             = useState({});
  const [form, setForm]                   = useState({ display_name: '', phone: '', bio: '' });
  const [loading, setLoading]             = useState(false);
  const [msg, setMsg]                     = useState({ text: '', type: '' });
  const [verifyLoading, setVerifyLoading] = useState(false);
  const [verifyMsg, setVerifyMsg]         = useState('');

  useEffect(() => {
    if (!isAuthenticated) return;
    getHeaders(isAuthenticated, getAccessTokenSilently).then(h =>
      fetchProfile(h).then(d => {
        if (d.status === 'success') setProfile(d.data || {});
      })
    );
  }, [isAuthenticated, getAccessTokenSilently]);

  if (!isAuthenticated) {
    return (
      <div style={{ padding: '60px 24px', textAlign: 'center' }}>
        <p style={{ opacity: 0.5, marginBottom: '16px' }}>Please log in to view your profile.</p>
        <button className="btn-primary" style={{ width: 'auto', padding: '12px 32px' }}
          onClick={() => loginWithRedirect()}>Log In</button>
      </div>
    );
  }

  const startEdit = () => {
    setForm({
      display_name: profile.display_name || user.name || '',
      phone:        profile.phone        || '',
      bio:          profile.bio          || ''
    });
    setEditing(true);
    setMsg({ text: '', type: '' });
  };

  const handleSave = async () => {
    if (form.phone && (!/^\d{10}$/.test(form.phone))) {
      setMsg({ text: 'Phone must be a 10-digit number', type: 'error' });
      return;
    }
    setLoading(true);
    const h = await getHeaders(isAuthenticated, getAccessTokenSilently);
    const d = await updateProfile(form, h);
    setLoading(false);
    if (d.status === 'success') {
      setProfile(d.data);
      setEditing(false);
      setMsg({ text: 'Profile updated successfully ✅', type: 'success' });
    } else {
      setMsg({ text: d.message || 'Failed to update', type: 'error' });
    }
  };

  const handleVerifyEmail = async () => {
    setVerifyLoading(true);
    setVerifyMsg('');
    const h = await getHeaders(isAuthenticated, getAccessTokenSilently);
    const d = await sendVerificationEmail(h);
    setVerifyLoading(false);
    if (d.status === 'success') {
      setVerifyMsg('✅ Verification email sent! Check your inbox.');
    } else {
      setVerifyMsg(d.message || 'Failed to send verification email.');
    }
  };

  const displayName = profile.display_name || user.name;

  const infoRow = (label, value) => (
    <div style={{
      display: 'flex', justifyContent: 'space-between', alignItems: 'center',
      padding: '14px 0', borderBottom: '1px solid rgba(255,255,255,0.06)'
    }}>
      <span style={{ fontSize: '0.85rem', opacity: 0.5, textTransform: 'uppercase', letterSpacing: '0.05em' }}>{label}</span>
      <span style={{ fontSize: '0.95rem', fontWeight: 500 }}>{value || '—'}</span>
    </div>
  );

  const inp = (key, label, placeholder, type = 'text') => (
    <div style={{ marginBottom: '14px' }}>
      <label style={{ display: 'block', fontSize: '0.78rem', opacity: 0.55, marginBottom: '4px' }}>{label}</label>
      <input
        type={type}
        value={form[key]}
        onChange={e => setForm(f => ({ ...f, [key]: e.target.value }))}
        placeholder={placeholder}
        style={{
          width: '100%', padding: '10px 14px', boxSizing: 'border-box',
          background: 'rgba(255,255,255,0.07)', border: '1px solid rgba(255,255,255,0.15)',
          borderRadius: '8px', color: '#fff', fontSize: '0.9rem'
        }}
      />
    </div>
  );

  return (
    <div style={{ maxWidth: '600px', margin: '0 auto', padding: '40px 24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '32px' }}>
        <h2 style={{ fontSize: '1.6rem', margin: 0 }}>My Profile</h2>
        {!editing && (
          <button onClick={startEdit} style={{
            padding: '8px 18px', background: 'rgba(255,255,255,0.07)',
            border: '1px solid rgba(255,255,255,0.15)', borderRadius: '8px',
            color: '#fff', cursor: 'pointer', fontSize: '0.85rem'
          }}>✏️ Edit Profile</button>
        )}
      </div>

      {msg.text && (
        <p style={{ color: msg.type === 'error' ? '#ef4444' : '#10b981', marginBottom: '16px', fontSize: '0.85rem' }}>
          {msg.text}
        </p>
      )}

      {/* Avatar + name */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: '20px', marginBottom: '28px',
        padding: '24px', background: 'rgba(255,255,255,0.04)',
        borderRadius: '16px', border: '1px solid rgba(255,255,255,0.08)'
      }}>
        <img src={user.picture} alt={displayName}
          style={{ width: '72px', height: '72px', borderRadius: '50%', objectFit: 'cover', border: '2px solid rgba(255,255,255,0.15)' }} />
        <div>
          <h3 style={{ margin: '0 0 4px', fontSize: '1.2rem', fontWeight: 700 }}>{displayName}</h3>
          <p style={{ margin: '0 0 4px', opacity: 0.5, fontSize: '0.85rem' }}>{user.email}</p>
          {profile.bio && <p style={{ margin: 0, opacity: 0.45, fontSize: '0.82rem', fontStyle: 'italic' }}>{profile.bio}</p>}
        </div>
      </div>

      {/* Edit form */}
      {editing && (
        <div style={{
          background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.1)',
          borderRadius: '14px', padding: '20px', marginBottom: '24px'
        }}>
          <h4 style={{ margin: '0 0 16px', fontSize: '0.95rem' }}>Edit Profile</h4>
          {inp('display_name', 'Display Name', user.name || 'Your name')}
          {inp('phone',        'Phone Number', '10-digit mobile number', 'tel')}
          {inp('bio',          'Bio',          'A short bio about yourself')}
          <p style={{ fontSize: '0.75rem', opacity: 0.35, margin: '0 0 14px', lineHeight: 1.5 }}>
            Display name and bio are stored in MyStore. Email and profile picture are managed by your identity provider ({user.sub?.split('|')[0]}).
          </p>
          <div style={{ display: 'flex', gap: '10px' }}>
            <button className="btn-primary" onClick={handleSave} disabled={loading}
              style={{ width: 'auto', padding: '10px 20px', fontSize: '0.9rem' }}>
              {loading ? 'Saving...' : 'Save Changes'}
            </button>
            <button onClick={() => setEditing(false)} disabled={loading}
              style={{
                padding: '10px 16px', background: 'transparent',
                border: '1px solid rgba(255,255,255,0.2)', borderRadius: '8px',
                color: 'rgba(255,255,255,0.6)', cursor: 'pointer', fontSize: '0.9rem'
              }}>Cancel</button>
          </div>
        </div>
      )}

      {/* Info rows */}
      <div style={{
        background: 'rgba(255,255,255,0.03)', borderRadius: '12px',
        padding: '0 20px', border: '1px solid rgba(255,255,255,0.07)'
      }}>
        {infoRow('Display Name',  profile.display_name || user.name)}
        {infoRow('Phone',         profile.phone)}
        {infoRow('Bio',           profile.bio)}
        {infoRow('Email',         user.email)}
        <div style={{
          display: 'flex', justifyContent: 'space-between', alignItems: 'center',
          padding: '14px 0', borderBottom: '1px solid rgba(255,255,255,0.06)'
        }}>
          <span style={{ fontSize: '0.85rem', opacity: 0.5, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Email Verified</span>
          <span style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            {user.email_verified ? (
              <span style={{ fontSize: '0.95rem', fontWeight: 500 }}>✅ Verified</span>
            ) : (
              <>
                <span style={{ fontSize: '0.95rem', color: '#ef4444' }}>❌ Not verified</span>
                <button
                  onClick={handleVerifyEmail}
                  disabled={verifyLoading}
                  style={{
                    padding: '4px 12px', background: 'rgba(245,158,11,0.15)',
                    border: '1px solid rgba(245,158,11,0.4)', borderRadius: '6px',
                    color: '#f59e0b', cursor: 'pointer', fontSize: '0.78rem',
                    opacity: verifyLoading ? 0.5 : 1
                  }}
                >
                  {verifyLoading ? 'Sending...' : 'Send Verification Email'}
                </button>
              </>
            )}
          </span>
        </div>
        {verifyMsg && (
          <p style={{ padding: '8px 0', fontSize: '0.82rem', color: verifyMsg.startsWith('✅') ? '#10b981' : '#ef4444' }}>
            {verifyMsg}
          </p>
        )}
        {infoRow('Auth Provider', user.sub?.split('|')[0])}
      </div>

      {/* Danger zone */}
      <div style={{
        marginTop: '32px', padding: '20px',
        background: 'rgba(239,68,68,0.05)', border: '1px solid rgba(239,68,68,0.15)',
        borderRadius: '12px'
      }}>
        <h4 style={{ margin: '0 0 8px', fontSize: '0.9rem', color: '#ef4444' }}>Account Actions</h4>
        <p style={{ margin: '0 0 14px', fontSize: '0.82rem', opacity: 0.5 }}>
          Logging out will end your current session on this device.
        </p>
        <button
          onClick={() => logout({ logoutParams: { returnTo: window.location.origin } })}
          style={{
            padding: '9px 18px', background: 'rgba(239,68,68,0.1)',
            border: '1px solid rgba(239,68,68,0.3)', borderRadius: '8px',
            color: '#ef4444', cursor: 'pointer', fontSize: '0.85rem'
          }}>🚪 Log Out</button>
      </div>
    </div>
  );
}

export default ProfilePage;
