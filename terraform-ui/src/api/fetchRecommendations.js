const API_URL = "https://uzai3qn10d.execute-api.ap-south-1.amazonaws.com/prod"; // Replace this with actual endpoint

async function fetchRecommendations() {
  try {
    const response = await fetch(API_URL);
    const data = await response.json();
    return data.recommendations || [];
  } catch (error) {
    console.error("Failed to fetch recommendations", error);
    return [];
  }
}

export default fetchRecommendations;
