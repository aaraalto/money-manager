const API_URL = "/api/view";

export interface DashboardData {
    // define specific properties based on actual API response
    [key: string]: unknown;
}

export async function fetchDashboardData(): Promise<DashboardData> {
    const response = await fetch(API_URL);
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
}

