var t="/api/view";async function r(){let a=await fetch(t);if(!a.ok)throw new Error(`HTTP error! status: ${a.status}`);return await a.json()}export{r as fetchDashboardData};
