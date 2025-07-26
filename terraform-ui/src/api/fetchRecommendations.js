const API_URL = "https://uzai3qn10d.execute-api.ap-south-1.amazonaws.com/prod/terraform";

async function fetchRecommendations() {
  try {
    console.log("Fetching recommendations from existing GET endpoint:", API_URL);
    
    const response = await fetch(API_URL, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      },
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    console.log("✅ API Response:", data);
    
    return data.recommendations || [];
  } catch (error) {
    console.error("❌ Failed to fetch recommendations:", error);
    // Return mock data for development/testing
    return [
      {
        resourceId: "i-1234567890abcdef0",
        resourceName: "test-ec2-instance",
        resourceType: "ec2",
        region: "us-east-1",
        reason: "Instance has been idle for 30+ days",
        cost_impact: 50.25,
        last_used: "2024-12-15"
      },
      {
        resourceId: "vol-0987654321fedcba",
        resourceName: "unused-ebs-volume",
        resourceType: "ebs",
        region: "us-east-1", 
        reason: "Volume not attached to any instance",
        cost_impact: 15.75,
        last_used: "2024-11-20"
      }
    ];
  }
}

export default fetchRecommendations;