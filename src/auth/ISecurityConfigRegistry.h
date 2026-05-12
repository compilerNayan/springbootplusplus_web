#ifndef I_SECURITY_CONFIG_REGISTRY_H
#define I_SECURITY_CONFIG_REGISTRY_H

#include <StandardDefines.h>

#include "ISecurityConfig.h"

DefineStandardPointers(ISecurityConfigRegistry)

/**
 * Collects ISecurityConfig implementations for later use (for example applying Configure to each rule manager).
 */
class ISecurityConfigRegistry {

    Public Virtual ~ISecurityConfigRegistry() = default;

    /** Registers a security config; the registry owns or retains it according to the concrete implementation. */
    Public Virtual Void Register(ISecurityConfigPtr securityConfig) = 0;
};

#endif // I_SECURITY_CONFIG_REGISTRY_H
