import React from 'react';
import ReactDOM from 'react-dom/client';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Dashboard } from './pages/Dashboard';
import './styles.css';
const client = new QueryClient({defaultOptions:{queries:{retry:1}}});
ReactDOM.createRoot(document.getElementById('root')!).render(<React.StrictMode><QueryClientProvider client={client}><Dashboard/></QueryClientProvider></React.StrictMode>);
