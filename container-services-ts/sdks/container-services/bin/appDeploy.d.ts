import * as pulumi from "@pulumi/pulumi";
export declare class AppDeploy extends pulumi.ComponentResource {
    /**
     * Returns true if the given object is an instance of AppDeploy.  This is designed to work even
     * when multiple copies of the Pulumi SDK have been loaded into the same process.
     */
    static isInstance(obj: any): obj is AppDeploy;
    readonly loadbalancerDnsName: pulumi.Output<string>;
    /**
     * Create a AppDeploy resource with the given unique name, arguments, and options.
     *
     * @param name The _unique_ name of the resource.
     * @param args The arguments to use to populate this resource's properties.
     * @param opts A bag of options that control this resource's behavior.
     */
    constructor(name: string, args: AppDeployArgs, opts?: pulumi.ComponentResourceOptions);
}
/**
 * The set of arguments for constructing a AppDeploy resource.
 */
export interface AppDeployArgs {
    accessCidr?: string;
    cpu?: number;
    imageReference: pulumi.Input<string>;
    memory?: number;
}
