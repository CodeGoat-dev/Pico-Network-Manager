// Goat - Time API
// Version 1.0.0
// Used by Goat applications to provide date and time synchronisation.

// Import dependencies
const api = require("./api/api.js");

process.on("SIGINT", async () => {
  console.log("Shutting down server...");
  process.exit();
});

// Start listening for connections
api();
