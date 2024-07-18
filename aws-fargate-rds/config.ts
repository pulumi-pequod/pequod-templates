
import { Config, getOrganization, getProject, getStack, interpolate } from "@pulumi/pulumi";
import { RandomPassword } from "@pulumi/random";

const config = new Config();

// name base for naming conventions
export let nameBase = config.get("nameBase") || `pqd-ecs-${getStack()}`;
nameBase = nameBase.substring(0,22) // make sure the name isn't too long for AWS (once various suffixes are added)

// Get db info
export const dbName = config.get("dbName") || "backend";
export const dbUser = config.get("dbUser") || "admin";
// Get secretified password from config or create one using the "random" package
export let dbPassword = config.getSecret("dbPassword");
if (!dbPassword) {
  dbPassword = new RandomPassword("dbPassword", {
    length: 16,
    special: false,
  }).result;
}

// DataDog key to allow ESC agent to send info to DataDog 
export const datadogApiKey = config.requireSecret("datadogApiKey")

// drift management setting. 
export const driftManagement = config.get("driftManagement") || "Correct"

