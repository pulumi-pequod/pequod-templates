package myproject;

import com.pulumi.Pulumi;
import com.pulumi.core.Output;
import com.pulumipequod.containerservices.AppImageDeploy;
import com.pulumipequod.containerservices.AppImageDeployArgs;
import com.pulumipequod.stackmgmt.StackSettings;

public class App {
    public static void main(String[] args) {
        Pulumi.run(ctx -> {
            // Get stack config if provided, otherwise use default values.
            var config = ctx.config();
            double cpu = config.getDouble("cpu").orElse(256.0);
            double memory = config.getDouble("memory").orElse(512.0);

            // Use component abstraction to create docker image, push to ECR and deploy
            // to ECS.
            var appDeployment = new AppImageDeploy("appDeployment",
                    AppImageDeployArgs.builder()
                            .dockerFilePath("./app")
                            .cpu(cpu)
                            .memory(memory)
                            .build());

            // Manage stack settings in Pulumi Cloud.
            var stackmgmt = new StackSettings("stackmgmt");

            // The URL at which the container's HTTP endpoint will be available.
            ctx.export("appUrl",
                    appDeployment.loadbalancerDnsName().applyValue(dns -> "http://" + dns));
        });
    }
}
