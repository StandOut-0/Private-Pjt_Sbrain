import { createRoot } from 'react-dom/client';
import { QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
import { getPayload } from './api';
import { PageRouter } from './pages/AllPages';
import { queryClient } from './api';
import { AppShell } from './components/AppShell';
import './styles.css';

const mount = document.getElementById('root');
if (mount) {
  const payload = getPayload();
  const page = <PageRouter payload={payload}/>;
  const content = ['login', 'demo-login', 'face-auth'].includes(payload.page)
    ? page
    : <AppShell payload={payload}>{page}</AppShell>;
  createRoot(mount).render(<QueryClientProvider client={queryClient}><BrowserRouter>{content}</BrowserRouter></QueryClientProvider>);
}
