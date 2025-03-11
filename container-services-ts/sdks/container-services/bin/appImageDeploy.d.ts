import * as pulumi from "@pulumi/pulumi";
export declare class AppImageDeploy extends pulumi.ComponentResource {
    /**
     * Returns true if the given object is an instance of AppImageDeploy.  This is designed to work even
     * when multiple copies of the Pulumi SDK have been loaded into the same process.
     */
    static isInstance(obj: any): obj is AppImageDeploy;
    readonly loadbalancerDnsName: pulumi.Output<string>;
    /**
     * Create a AppImageDeploy resource with the given unique name, arguments, and options.
     *
     * @param name The _unique_ name of the resource.
     * @param args The arguments to use to populate this resource's properties.
     * @param opts A bag of options that control this resource's behavior.
     */
    constructor(name: string, args?: AppImageDeployArgs, opts?: pulumi.ComponentResourceOptions);
}
/**
 * The set of arguments for constructing a AppImageDeploy resource.
 */
export interface AppImageDeployArgs {
    cpu?: number;
    memory?: number;
}
