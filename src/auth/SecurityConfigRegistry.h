#ifndef SECURITY_CONFIG_REGISTRY_H
#define SECURITY_CONFIG_REGISTRY_H

#include <StandardDefines.h>

#include "IEndpointSecurityRuleManager.h"
#include "ISecurityConfigRegistry.h"

/**
 * Applies each ISecurityConfig by invoking Configure on the shared IEndpointSecurityRuleManager.
 */
/* @Component */
class SecurityConfigRegistry : public ISecurityConfigRegistry {

    /* @Autowired */
    Private IEndpointSecurityRuleManagerPtr endpointSecurityRuleManager;

    Public SecurityConfigRegistry() {
        RegisterAllSecurityConfigs();
    };

    Public ~SecurityConfigRegistry() override = default;

    Public Void Register(ISecurityConfigPtr securityConfig) override {
        if (!securityConfig || !endpointSecurityRuleManager) {
            return;
        }
        securityConfig->Configure(endpointSecurityRuleManager);
    }

    Private Void RegisterAllSecurityConfigs() {
        //PLACEHOLDER FOR SECURITY CONFIG REGISTRATIONS
    }
};

#endif // SECURITY_CONFIG_REGISTRY_H
