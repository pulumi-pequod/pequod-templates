import * as aws from "@pulumi/aws";
import { StackSettings } from "@pulumi-pequod/stackmgmt";
import * as pulumi from "@pulumi/pulumi";

const config = new pulumi.Config()

const bucket = new aws.s3.Bucket("main", {
    acl: "private",
    forceDestroy: true,
    tags: { "Owner": pulumi.getOrganization() },
});

bucket.onObjectCreated("logger", new aws.lambda.CallbackFunction<aws.s3.BucketEvent, void>("loggerFn", {
    memorySize: 128,
    callback: (e) => {
        for (const rec of e.Records || []) {
            const [buck, key] = [rec.s3.bucket.name, rec.s3.object.key];
            console.log(`Object created: ${buck}/${key}`);
        }
    },
}));

// Handle stack management settings for deployments, tags, etc.
const stackmgmt = new StackSettings(`stackmgmt`, {driftManagement: config.get("driftManagement")})

export const bucketName = bucket.bucket;


