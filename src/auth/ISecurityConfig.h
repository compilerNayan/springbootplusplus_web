#ifndef I_SECURITY_CONFIG_H
#define I_SECURITY_CONFIG_H

#include <StandardDefines.h>

#include "IEndpointSecurityRuleManager.h"

DefineStandardPointers(ISecurityConfig)

class ISecurityConfig {

    Public Virtual ~ISecurityConfig() = default;

    Public Virtual Void Configure(IEndpointSecurityRuleManagerPtr endpointSecurityRuleManager) = 0;
};

#endif // I_SECURITY_CONFIG_H
