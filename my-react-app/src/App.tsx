import { BrowserRouter, Routes, Route, useLocation } from 'react-router-dom';
import Header from './components/Header'; // Importujemy Header tutaj

import RankingPage from './pages/RankingPage';
import IndustryPage from './pages/IndustryPage';
import GraphsPage from './pages/GraphsPage';
import ChartsPage from './pages/ChartsPage';
import SimulationPage from './pages/SimulationPage';

/*function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<RankingPage />} />
        <Route path="/industry/:pkdId" element={<IndustryPage />} />
        <Route path="/graphs" element={<GraphsPage />} />
        <Route path="/charts" element={<ChartsPage />} />
        <Route path="/simulation" element={<SimulationPage />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;*/


// Komponent pomocniczy, żeby przewijać na górę przy zmianie strony
import { useEffect } from 'react';

const ScrollToTop = () => {
  const { pathname } = useLocation();
  useEffect(() => {
    window.scrollTo(0, 0);
  }, [pathname]);
  return null;
};

function App() {
  return (
    <BrowserRouter>
      {/* To sprawia, że przy zmianie strony wracamy na górę */}
      <ScrollToTop />

      {/* HEADER JEST TERAZ TUTAJ - POZA ROUTAMI */}
      {/* Dzięki temu nie mruga i nie przeładowuje się przy klikaniu */}
      <Header />

      <Routes>
        <Route path="/" element={<RankingPage />} />
        <Route path="/graphs" element={<GraphsPage />} />
        <Route path="/charts" element={<ChartsPage />} />
        <Route path="/simulation" element={<SimulationPage />} />
        <Route path="/industry/:pkdId" element={<IndustryPage />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;