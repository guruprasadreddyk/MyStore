import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { Auth0Provider } from '@auth0/auth0-react';
import './index.css';
import App from './App';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <Auth0Provider
  domain="dev-sjgq3v6pvbgxs6mb.us.auth0.com"
  clientId="hZwfuIDn9Bsh8W6mI95fboh5Tqbbn94x"
  authorizationParams={{
    redirect_uri: window.location.origin,
    audience: "https://api.mystore.com"
  }}
  cacheLocation="localstorage" 
  useRefreshTokens={true}     
>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </Auth0Provider>
  </React.StrictMode>
);