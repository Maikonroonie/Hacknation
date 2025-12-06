import { BrowserRouter, Routes, Route } from 'react-router-dom';
import RankingPage from './pages/RankingPage';
import IndustryPage from './pages/IndustryPage';
import GraphsPage from './pages/GraphsPage';
import ChartsPage from './pages/ChartsPage';
import SimulationPage from './pages/SimulationPage';

function App() {
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

export default App;