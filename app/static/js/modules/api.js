const API_URL = "/api/view";

export async function fetchDashboardData() {
    const response = await fetch(API_URL);
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
}

