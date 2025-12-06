import { Link, useLocation } from 'react-router-dom';

const Header = () => {
  const location = useLocation();

  // Funkcja pomocnicza do aktywnego linku
  const linkClass = (path: string) => 
    `text-sm font-medium transition-colors ${
      location.pathname === path 
        ? 'text-pko-red font-bold' 
        : 'text-pko-text hover:text-pko-navy'
    }`;

  return (
    <header className="sticky top-0 z-50 bg-white shadow-md border-b-2 border-pko-red">
      <div className="container mx-auto px-4 h-16 flex items-center justify-between">
        {/* LOGO */}
        <Link to="/" className="flex items-center gap-2 group">
          <div className="w-8 h-8 bg-pko-navy text-white flex items-center justify-center font-bold rounded-sm group-hover:bg-pko-red transition-colors">
            PKO
          </div>
          <div>
            <h1 className="text-pko-navy font-bold text-lg leading-tight">Indeks Branż</h1>
            <p className="text-xs text-gray-500 uppercase tracking-wider">Dashboard Analityczny</p>
          </div>
        </Link>

        {/* NAWIGACJA - NOWE LINKI */}
        <nav className="hidden md:flex gap-8">
          <Link to="/" className={linkClass('/')}>Ranking</Link>
          <Link to="/graphs" className={linkClass('/graphs')}>Grafy</Link>
          <Link to="/charts" className={linkClass('/charts')}>Wykresy</Link>
          <Link to="/simulation" className={linkClass('/simulation')}>Symulacja</Link>
        </nav>

        {/* PROFIL */}
        <div className="flex items-center gap-3">
          <div className="text-right hidden sm:block">
            <p className="text-xs font-bold text-pko-navy">Jan Kowalski</p>
            <p className="text-[10px] text-gray-500">Analityk Ryzyka</p>
          </div>
          <div className="w-8 h-8 rounded-full bg-gray-200 border border-gray-300"></div>
        </div>
      </div>
    </header>
  );
};

export default Header;