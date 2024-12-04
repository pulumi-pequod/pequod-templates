import * as esc from "@pulumi/esc-sdk";
import express from "express";
import { open } from "fs";

const app = express();
const port = 8080;

// Initialize the message presented by the web server. 
let announcement = "Hello World!";
let whisper = "No environment was found."

// Get the Pulumi Access Token from the environment so that we can get the ESC environment
const PULUMI_ACCESS_TOKEN = process.env.PULUMI_ACCESS_TOKEN;

// Get the ESC environment name via environment variable and set up the client.
const escEnv = process.env.ESC_ENV_NAME 
const orgName =  escEnv.split("/")[0];
const projName = escEnv.split("/")[1];
const envName = escEnv.split("/")[2];
const config = new esc.Configuration({ accessToken: PULUMI_ACCESS_TOKEN });
const client = new esc.EscApi(config);

app.get("/", async (req, res) => {

  if (escEnv) {
    // Get the values from the environment
    const openEnv = await client.openAndReadEnvironment(orgName, projName, envName);
    announcement = openEnv.values?.messages?.announcement
    whisper = openEnv.values?.messages.whisper
  }

  const message = `<p><b>${announcement}</b></p><p><small>Psst: ${whisper}</small></p>`;
  res.send(message);
});

app.listen(port, () => {
  console.log(`Listening on port ${port}...`);
});
