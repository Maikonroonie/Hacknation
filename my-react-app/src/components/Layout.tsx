// src/components/Layout.tsx
import { ReactNode } from 'react';
import Header from './Header';

const Layout = ({ children }: { children: ReactNode }) => (
  <div className="min-h-screen bg-gray-50 flex flex-col font-sans text-pko-text">
    <Header />
    <main className="flex-grow container mx-auto px-4 py-8">{children}</main>
  </div>
);

export default Layout;