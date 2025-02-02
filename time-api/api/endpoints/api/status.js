module.exports = async (app) => {
  // Endpoint to get the status of the time synchronisation API
  app.get("/api/status", async (req, res) => {
    try {
      res.json({
        status: "Online"
      });
    } catch (error) {
      app.log("Error fetching time API status information:", error.message);
      res.status(500)
        .json({ error: "An error occurred while processing the request." });
    }
  });
};
