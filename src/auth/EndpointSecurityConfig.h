#ifndef ENDPOINT_SECURITY_CONFIG_H
#define ENDPOINT_SECURITY_CONFIG_H

#include <StandardDefines.h>
#include <HttpMethod.h>

#include "IEndpointSecurityConfig.h"

/**
 * Associates (URL path, HTTP method) pairs with an IAuthorizationFilter.
 * If no rule is registered for a path and method, IsAllowed returns true (no authorization required).
 */
/* @Component */
class EndpointSecurityConfig : public IEndpointSecurityConfig {

    Private StdMap<StdString, StdMap<HttpMethod, IAuthorizationFilterPtr>> rules;

    Public EndpointSecurityConfig() = default;

    Public ~EndpointSecurityConfig() override = default;

    Public Void AddRule(CStdString& url, HttpMethod method, IAuthorizationFilterPtr authorizer) override {
        rules[StdString(url)][method] = authorizer;
    }

    Public NoDiscard Bool IsAllowed(CStdString& url, HttpMethod method, const JwtAuthenticationToken& token) const override {
        Val pathIt = rules.find(StdString(url));
        if (pathIt == rules.end()) {
            return true;
        }
        Val methodIt = pathIt->second.find(method);
        if (methodIt == pathIt->second.end()) {
            return true;
        }
        IAuthorizationFilterPtr filter = methodIt->second;
        if (!filter) {
            return true;
        }
        return filter->Authorize(token);
    }
};

#endif // ENDPOINT_SECURITY_CONFIG_H
