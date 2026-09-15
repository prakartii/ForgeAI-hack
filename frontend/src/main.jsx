import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import { PortalApp } from './portal/PortalApp.jsx'
import './index.css'

const isPortal = window.location.pathname.startsWith('/users')

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    {isPortal ? <PortalApp /> : <App />}
  </React.StrictMode>,
)
