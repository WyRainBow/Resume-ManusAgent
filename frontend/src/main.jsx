import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import SophiaChat from './pages/SophiaChat.jsx'
import ErrorBoundary from './ErrorBoundary.jsx'
import './index.css'

// 简单的路由系统：基于 hash
// - #sophia 或 #/sophia -> SophiaChat 页面
// - 其他 -> 原始 App

function getRouteFromHash() {
  const hash = decodeURIComponent(window.location.hash || '').toLowerCase();
  return hash;
}

function Router() {
  const [route, setRoute] = React.useState(getRouteFromHash);
  
  React.useEffect(() => {
    const handleHashChange = () => {
      const newRoute = getRouteFromHash();
      console.log('[Router] Hash changed to:', newRoute);
      setRoute(newRoute);
    };
    
    window.addEventListener('hashchange', handleHashChange);
    
    // 初始化时也检查一次
    const initialRoute = getRouteFromHash();
    console.log('[Router] Initial route:', initialRoute);
    if (initialRoute !== route) {
      setRoute(initialRoute);
    }
    
    return () => window.removeEventListener('hashchange', handleHashChange);
  }, []);
  
  // 检查是否包含 sophia
  const isSophiaRoute = route.includes('sophia');
  console.log('[Router] Rendering:', isSophiaRoute ? 'SophiaChat' : 'App', '| route:', route);
  
  if (isSophiaRoute) {
    return <SophiaChat />;
  }
  
  return <App />;
}

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <ErrorBoundary>
      <Router />
    </ErrorBoundary>
  </React.StrictMode>,
)
