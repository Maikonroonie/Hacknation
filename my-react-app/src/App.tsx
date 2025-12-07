import { BrowserRouter, Routes, Route, useLocation } from 'react-router-dom';
import Header from './components/Header';
import RankingPage from './pages/RankingPage';
import IndustryPage from './pages/IndustryPage';
import GraphsPage from './pages/GraphsPage';
import ChartsPage from './pages/ChartsPage';
import SimulationPage from './pages/SimulationPage';


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
      <ScrollToTop />
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