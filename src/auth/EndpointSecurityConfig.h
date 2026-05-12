#ifndef ENDPOINT_SECURITY_CONFIG_H
#define ENDPOINT_SECURITY_CONFIG_H

#include <StandardDefines.h>
#include <HttpMethod.h>
#include <mutex>

#include "IEndpointSecurityConfig.h"

/**
 * Associates (URL path, HTTP method) pairs with an IAuthorizationFilter.
 * If no rule is registered for a path and method, IsAllowed returns true (no authorization required).
 *
 * Register filters with AddRule<T>(url, method, ...).
 */
/* @Component */
class EndpointSecurityConfig : public IEndpointSecurityConfig {

    Private StdMap<StdString, StdMap<HttpMethod, IAuthorizationFilterPtr>> rules;
    Private mutable std::mutex rulesMutex;

    Public EndpointSecurityConfig() = default;

    Public ~EndpointSecurityConfig() override = default;

    Protected Void AddRuleImpl(CStdString& url,
                               HttpMethod method,
                               std::function<IAuthorizationFilterPtr()> resolveAuthorizer) override {
        std::lock_guard<std::mutex> lock(rulesMutex);
        IAuthorizationFilterPtr authorizer = resolveAuthorizer();
        rules[StdString(url)][method] = authorizer;
    }

    Protected NoDiscard Bool IsAllowed(CStdString& url, HttpMethod method, const JwtAuthenticationToken& token) const override {
        std::lock_guard<std::mutex> lock(rulesMutex);
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
