import React from 'react'
import ReactDOM from 'react-dom/client'
import SophiaChat from './pages/SophiaChat'
import ErrorBoundary from './ErrorBoundary.jsx'
import './index.css'

// 简单的路由系统：基于 hash
// - 默认跳转到 #sophiapro
// - 其他路径也统一渲染 SophiaChat

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
    if (!initialRoute || initialRoute === '#') {
      window.location.hash = '#sophiapro';
      return;
    }
    if (initialRoute !== route) {
      setRoute(initialRoute);
    }

    return () => window.removeEventListener('hashchange', handleHashChange);
  }, []);

  const isSophiaRoute = route.includes('sophia');
  console.log('[Router] Rendering:', 'SophiaChat', '| route:', route);
  if (!isSophiaRoute) {
    window.location.hash = '#sophiapro';
  }
  return <SophiaChat />;
}

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <ErrorBoundary>
      <Router />
    </ErrorBoundary>
  </React.StrictMode>,
)


