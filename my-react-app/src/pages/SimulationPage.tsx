import Layout from '../components/Layout';

const SimulationPage = () => (
  <Layout>
    <h1 className="text-2xl font-bold text-pko-navy mb-4">Symulator Rynkowy</h1>
    <div className="bg-white p-10 rounded-lg shadow border border-gray-200 text-center text-gray-500">
      Tu będziesz mógł zmieniać parametry (np. inflację) i patrzeć jak to wpłynie na PKO Score.
    </div>
  </Layout>
);
export default SimulationPage;