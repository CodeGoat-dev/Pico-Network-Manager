const axios = require("axios");
const moment = require("moment-timezone");

module.exports = async (app) => {
  // Endpoint to get the current time and timezone offset
  app.get("/api/time", async (req, res) => {
    try {
      const clientIP = req.socket.remoteAddress;
      // Fetch IP information from ip-api
      const ipInfoResponse = await axios.get(`http://ip-api.com/json/${clientIP}`);
      const ipInfo = ipInfoResponse.data;

      if (ipInfo.status !== "success") {
        const timezone = "UTC";
        const currentTime = moment()
          .tz(timezone); // Get the current time in the default timezone
        const offsetSeconds = currentTime.utcOffset() * 60; // UTC offset in seconds
        res.json({
          timezone,
          currentTime: currentTime.format("YYYY-MM-DD HH:mm:ss"), // Formatted current time
          offsetSeconds
        });
      }

      const defaultTimezone = "UTC";
      const timezone = ipInfo.timezone || defaultTimezone;
      const currentTime = moment()
        .tz(timezone); // Get the current time in the user's timezone
      const offsetSeconds = currentTime.utcOffset() * 60; // UTC offset in seconds

      res.json({
        timezone,
        currentTime: currentTime.format("YYYY-MM-DD HH:mm:ss"), // Formatted current time
        offsetSeconds
      });
    } catch (error) {
      app.log("Error fetching timezone information:", error.message);
    }
  });
};
