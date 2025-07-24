import { useEffect, useState } from 'react';
import RecommendationCard from './components/RecommendationCard';
import fetchRecommendations from './api/fetchRecommendations';

function App() {
  const [recommendations, setRecommendations] = useState([]);

  useEffect(() => {
    async function loadData() {
      const data = await fetchRecommendations();
      setRecommendations(data);
    }
    loadData();
  }, []);

  return (
    <div className="min-h-screen bg-gray-950 text-white p-6">
      <h1 className="text-3xl font-bold mb-6 text-center">Terraform Script Generator</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {recommendations.length === 0 ? (
          <p className="text-center w-full">No recommendations found.</p>
        ) : (
          recommendations.map((item, idx) => (
            <RecommendationCard key={idx} resource={item} />
          ))
        )}
      </div>
    </div>
  );
}

export default App;
