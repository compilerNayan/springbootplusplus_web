#ifndef ENDPOINT_SECURITY_CONFIG_H
#define ENDPOINT_SECURITY_CONFIG_H

#include <StandardDefines.h>
#include <HttpMethod.h>
#include <mutex>

#include "IEndpointSecurityConfig.h"
#include "IAuthorizationFilterFactory.h"
#include "PrimaryAuthorizationFilter.h"

/**
 * Associates (URL path, HTTP method) pairs with an IAuthorizationFilter.
 * If no rule is registered for a path and method, IsAllowed returns true (no authorization required).
 *
 * Register filters with AddRule<T>(url, method, ...).
 */
/* @Component */
class EndpointSecurityConfig : public IEndpointSecurityConfig {

    Private StdMap<StdString, StdMap<HttpMethod, IAuthorizationFilterPtr>> rules;
    Private IAuthorizationFilterPtr primaryAuthorizationFilter;
    Private mutable std::mutex rulesMutex;

    /* @Autowired */
    Private IAuthorizationFilterFactoryPtr authorizationFilterFactory;

    Public EndpointSecurityConfig() {
        primaryAuthorizationFilter = authorizationFilterFactory->GetFilter<PrimaryAuthorizationFilter>();
    };

    Public ~EndpointSecurityConfig() override = default;

    Protected Void AddRuleImpl(CStdString& url,
                               HttpMethod method,
                               std::function<IAuthorizationFilterPtr()> resolveAuthorizer) override {
        std::lock_guard<std::mutex> lock(rulesMutex);
        IAuthorizationFilterPtr authorizer = resolveAuthorizer();
        rules[StdString(url)][method] = authorizer;
    }

    Protected NoDiscard std::pair<Bool, optional<ResponseEntity<StdString>>> IsAllowed(
        CStdString& url, HttpMethod method, const JwtAuthenticationToken& token) const override {
        std::lock_guard<std::mutex> lock(rulesMutex);
        Val pathIt = rules.find(StdString(url));
        if (pathIt == rules.end()) {
            return {true, {}};
        }
        Val methodIt = pathIt->second.find(method);
        if (methodIt == pathIt->second.end()) {
            return {true, {}};
        }
        auto response = primaryAuthorizationFilter->Authorize(token);
        if(response.first == false) {
            return response;
        }
        
        IAuthorizationFilterPtr filter = methodIt->second;
        if (!filter) {
            return {true, {}};
        }
        return filter->Authorize(token);
    }
};

#endif // ENDPOINT_SECURITY_CONFIG_H
