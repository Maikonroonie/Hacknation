// src/components/Layout.tsx
/*
import { ReactNode } from 'react';
import Header from './Header';

const Layout = ({ children }: { children: ReactNode }) => (
  <div className="min-h-screen bg-gray-50 flex flex-col font-sans text-pko-text">
    <Header />
    <main className="flex-grow container mx-auto px-4 py-8">{children}</main>
  </div>
);

export default Layout; */

import { ReactNode } from 'react';
import { motion } from 'framer-motion';

interface LayoutProps {
  children: ReactNode;
}

const Layout = ({ children }: LayoutProps) => {
  return (
    <div className="min-h-screen bg-[#F9FAFB]">
      {/* Tu już NIE MA Headera. 
         Header będzie w App.tsx, żeby nie mrugał przy zmianie stron.
      */}

      {/* Kontener z treścią - animowany */}
      <main className="container mx-auto px-4 py-8">
        <motion.div
          initial={{ opacity: 0, y: 10 }} // Start: lekko niżej i niewidoczny
          animate={{ opacity: 1, y: 0 }}  // Koniec: na miejscu i widoczny
          exit={{ opacity: 0, y: -10 }}
          transition={{ duration: 0.4, ease: "easeOut" }} // Czas trwania animacji
        >
          {children}
        </motion.div>
      </main>
    </div>
  );
};

export default Layout;