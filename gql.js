(async () => {
  try {
    const body = JSON.stringify({
      operationName: "createService",
      query: "mutation createService($input: CreateServiceInput!) { createService(input: $input) { service { id name serviceUrl } } }",
      variables: {
        input: {
          type: "web_service",
          name: "eu-trend-bot",
          ownerId: "tea-d80fhcj7uimc73fg50sg",
          serviceDetails: {
            runtime: "node",
            repo: "https://github.com/Sayonara466/eu-trend-bot",
            branch: "main",
            buildCommand: "npm install",
            startCommand: "node server.js",
            plan: "starter",
            region: "oregon",
            envSpecificDetails: {
              envVars: [{ key: "TELEGRAM_BOT_TOKEN", value: "8792613395:AAGquGo3aZ1fbFjToatyR5hSLJiYR0Bs9s8" }]
            }
          }
        }
      }
    });
    const r = await fetch("/graphql", { method: "POST", headers: { "Content-Type": "application/json" }, body });
    const text = await r.text();
    return "Status: " + r.status + " | Body: " + text.substring(0, 1000);
  } catch (e) {
    return "Error: " + e.message;
  }
})();
