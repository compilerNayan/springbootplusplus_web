#ifndef I_ENDPOINT_SECURITY_CONFIG_H
#define I_ENDPOINT_SECURITY_CONFIG_H

#include <StandardDefines.h>
#include <HttpMethod.h>

#include "IAuthorizationFilter.h"

DefineStandardPointers(IEndpointSecurityConfig)

class IEndpointSecurityConfig {

    Public Virtual ~IEndpointSecurityConfig() = default;

    Public Virtual Void AddRule(CStdString& url, HttpMethod method, IAuthorizationFilterPtr authorizer) = 0;

    Public Virtual NoDiscard Bool IsAllowed(CStdString& url, HttpMethod method, const JwtAuthenticationToken& token) const = 0;
};

#endif // I_ENDPOINT_SECURITY_CONFIG_H
