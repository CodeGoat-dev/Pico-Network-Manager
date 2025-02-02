// Goat - Time Synchronisation API
// Used by various applications to provide time and date synchronisation.

// Import modules
const fs = require("fs");
const url = require("url");
const path = require("path");
const express = require("express");
const passport = require("passport");
const session = require("express-session");
const ejs = require("ejs");
const bodyParser = require("body-parser");
const https = require("https");
const moment = require("moment");

// Instantiate express app and the session store
const app = express();
const MemoryStore = require("memorystore")(session);

// Import configuration
const config = require("../data/settings.json");

// Export the api as a function which we call in ready event
module.exports = async () => {
  // Declare absolute paths
  const dataDir = path.resolve(`${process.cwd()}${path.sep}time-api`); // Absolute path of API directory.
  const templateDir = path.resolve(`${dataDir}${path.sep}templates`); // Absolute path of ./templates directory.

  // Deserializing and serializing users without any additional logic
  passport.serializeUser((user, done) => done(null, user));
  passport.deserializeUser((obj, done) => done(null, obj));

  // Initialize the memorystore middleware with our express app
  app.use(
    session({
      store: new MemoryStore({ checkPeriod: 86400000 }),
      secret: "#@%#&^$^$%@$^$&%#$%@#$%$^%&$%^#$%@#$%#E%#%@$FEErfgr3g#%GT%536c53cc6%5%tv%4y4hrgrggrgrgf4n",
      resave: false,
      saveUninitialized: false,
      cookie: {
        secure: true,
        maxAge: 86400000,
        httpOnly: false
      }
    })
  );

  // Initialize passport middleware
  app.use(passport.initialize());
  app.use(passport.session());

  // Configure header caching and access restrictions
  app.use((req, res, next) => {
    res.setHeader("Cache-Control", "public, max-age=1");
    next();
  });

  // Bind the domain
  app.locals.domain = config.api.sslDomain.split("//")[1];

  // Set templating engine
  app.engine("ejs", ejs.renderFile);
  app.set("view engine", "ejs");

  // Initialize body-parser middleware to be able to read forms
  app.use(bodyParser.json());
  app.use(
    bodyParser.urlencoded({
      extended: true
    })
  );

  // Configure Express to serve static content
  app.use(express.static(path.join(__dirname, "public")));

  // Configure Express to handle invalid requests
  app.use((err, req, res, next) => {
    if (err instanceof URIError) {
      console.error("Invalid URL encoding:", req.url);
      res.status(400)
        .send("Bad Request");
    } else {
      next(err);
    }
  });

  // Declare a logging function for all web requests
  app.log = async (message) => {
    const logger = fs.createWriteStream(config.logging.webLog, {
      flags: "a"
    });
    console.log(`[${moment()
      .format("YYYY-MM-DD HH:mm:ss")}] ${message}`);
    logger.write(`[${moment()
      .format("YYYY-MM-DD HH:mm:ss")}] ${message}\n`);
    logger.close();
  };

  // Declare a function to ensure all requests are redirected to secure HTTP
  function ensureSecure(req, res, next) {
    if (!config.api.enableSSL) {
      return next();
    }
    if (!config.api.requireSSL) {
      return next();
    }

    if (req.secure) {
      return next();
    }

    res.redirect("https://" + req.hostname + req.url);
  }

  // Declare a renderTemplate function to make rendering of a template in a route as easy as possible
  const renderTemplate = (res, req, template, data = {}) => {
    // Default base data which passed to the ejs template by default.
    const baseData = {
      path: req.path
    };
    // Render template using the absolute path of the template and merged default data with the additional data provided
    res.render(path.resolve(`${templateDir}${path.sep}${template}`), Object.assign(baseData, data));
  };

  // Configure secure HTTP redirection
  if (config.api.enableSSL) {
    app.all("*", ensureSecure);
  }

  // Require all endpoints
  const statusEndpoint = require("./endpoints/api/status.js");
  const timeEndpoint = require("./endpoints/api/time.js");

  // Call all endpoint functions
  statusEndpoint(app);
  timeEndpoint(app);

  // Listen for HTTP connections
  app.listen(config.api.port, null, null, async () => app.log(`Goat - Time Synchronisation API is up and running on port: ${config.api.port}`));

  // Listen for secure HTTP connections
  if (config.api.enableSSL) {
    https
      .createServer(
        {
          key: fs.readFileSync(config.api.sslKey),
          cert: fs.readFileSync(config.api.sslCertificate),
          ca: fs.readFileSync(config.api.sslCa)
        },
        app
      )
      .listen(config.api.sslPort, async () => {
        app.log(`Goat - Time Synchronisation API is up and running on port: ${config.api.sslPort}`);
      });
  }
};
