import { Link, useLocation } from 'react-router-dom';

const Header = () => {
  const location = useLocation();

  return (
    <header className="sticky top-0 z-50 bg-white/80 backdrop-blur-md border-b border-gray-100 transition-all duration-300">
      
      <div className="container mx-auto px-6 h-20 flex items-center justify-between relative">
        
        {/* 1. LOGO - Z dodaną płynną animacją */}
        <Link to="/" className="flex items-center gap-3 group">
          <div className="w-10 h-10 bg-pko-navy text-white flex items-center justify-center font-bold text-xl rounded-xl shadow-sm group-hover:bg-pko-red group-hover:scale-110 group-hover:rotate-3 transition-all duration-300 ease-out">
            PKO
          </div>
          <div className="flex flex-col">
            <span className="text-pko-navy font-bold text-base leading-none tracking-tight group-hover:text-pko-red transition-colors duration-300">Indeks Branż</span>
            <span className="text-[10px] text-gray-400 font-medium tracking-widest mt-1">ANALYTICS</span>
          </div>
        </Link>

        {/* 2. NAWIGACJA - Płynna Kapsułka */}
        <nav className="hidden md:flex items-center gap-1 p-1.5 bg-gray-100/50 border border-gray-200/60 rounded-full absolute left-1/2 -translate-x-1/2 backdrop-blur-sm shadow-sm transition-all hover:shadow-md duration-300">
          <NavLink to="/" current={location.pathname} label="Ranking" />
          <NavLink to="/graphs" current={location.pathname} label="Grafy" />
          <NavLink to="/charts" current={location.pathname} label="Wykresy" />
          <NavLink to="/simulation" current={location.pathname} label="Symulacja" />
        </nav>

        {/* 3. PUSTA PRAWA STRONA (z zachowaniem miejsca) */}
        <div className="w-[120px] flex justify-end items-center gap-4 opacity-0 md:opacity-100 transition-opacity duration-500">
           <span className="text-xs font-mono text-gray-300 border border-gray-200 px-2 py-1 rounded-md">
             v1.0.4
           </span>
        </div>
        
      </div>
    </header>
  );
};

// Komponent Linku z ulepszoną fizyką animacji
const NavLink = ({ to, current, label }: { to: string, current: string, label: string }) => {
  const isActive = current === to;
  
  return (
    <Link 
      to={to} 
      className={`
        relative px-6 py-2 rounded-full text-sm font-medium 
        transition-all duration-300 ease-out
        active:scale-95 
        ${isActive 
          ? 'bg-pko-navy text-white shadow-lg shadow-pko-navy/20 scale-100' // Stan aktywny
          : 'text-gray-500 hover:text-pko-navy hover:bg-white/80 hover:shadow-sm' // Stan nieaktywny
        }
      `}
    >
      {label}
    </Link>
  );
};

export default Header;