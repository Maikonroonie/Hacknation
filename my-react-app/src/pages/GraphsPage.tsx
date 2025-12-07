import Layout from '../components/Layout';
// Pamiętaj: Dwie kropki (..), bo wychodzimy z folderu 'pages' do 'src'
import BFSVisualizer from '../components/BFSVisualizer'; 

const GraphsPage = () => {
  return (
    <Layout>
      <div className="flex flex-col gap-6">
        {/* Nagłówek sekcji */}
        <div>
          <h2 className="text-2xl font-bold text-pko-navy">Grafy Powiązań (BFS)</h2>
          <p className="text-sm text-gray-500 mt-1">
            Wizualizacja algorytmu przeszukiwania wszerz dla powiązań międzysektorowych.
          </p>
        </div>

        {/* Kontener na Wykres - zabezpieczony przed wchodzeniem na Header */}
        <div className="bg-white p-4 rounded-xl shadow-lg border border-gray-200 relative z-0 overflow-hidden min-h-[600px]">
          
          {/* Tutaj ładuje się Twój komponent wizualizacji */}
          {/* Ustawiamy mu pełną wysokość i szerokość kontenera */}
          <div className="w-full h-full">
            <BFSVisualizer />
          </div>

        </div>
      </div>
    </Layout>
  );
};

export default GraphsPage;