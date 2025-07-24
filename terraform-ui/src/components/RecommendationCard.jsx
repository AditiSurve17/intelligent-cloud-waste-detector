function RecommendationCard({ resource }) {
  const handleGenerate = () => {
    const tfBlock = `
resource "${resource.resourceType}" "${resource.resourceName}" {
  # Terraform delete block
}
`;
    navigator.clipboard.writeText(tfBlock);
    alert("Terraform block copied to clipboard!");
  };

  const handleGenerateFromAPI = async () => {
    try {
      const response = await fetch("https://uzai3qn10d.execute-api.ap-south-1.amazonaws.com/prod/terraform", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          resourceType: resource.resourceType,
          resourceName: resource.resourceName,
        }),
      });

      const data = await response.json();

      if (data.terraform) {
        navigator.clipboard.writeText(data.terraform);
        alert("Terraform block generated from backend and copied to clipboard!");
      } else {
        alert("No Terraform block returned.");
      }
    } catch (error) {
      console.error("Error:", error);
      alert("Failed to generate Terraform block from backend.");
    }
  };

  return (
    <div className="bg-gray-800 p-4 rounded-xl shadow-md">
      <h2 className="text-xl font-semibold">{resource.resourceName}</h2>
      <p className="text-sm text-gray-300">Type: {resource.resourceType}</p>
      <p className="text-sm text-gray-400 mb-2">Reason: {resource.reason}</p>
      <div className="flex gap-2">
        <button
          onClick={handleGenerate}
          className="bg-red-600 hover:bg-red-700 px-4 py-2 rounded-md text-sm"
        >
          Generate Locally
        </button>
        <button
          onClick={handleGenerateFromAPI}
          className="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded-md text-sm"
        >
          Generate via API
        </button>
      </div>
    </div>
  );
}

export default RecommendationCard;
