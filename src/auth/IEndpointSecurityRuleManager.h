#ifndef I_ENDPOINT_SECURITY_RULE_MANAGER_H
#define I_ENDPOINT_SECURITY_RULE_MANAGER_H

#include <StandardDefines.h>
#include <functional>
#include <HttpMethod.h>
#include <tuple>
#include <type_traits>
#include <utility>

#include "IAuthorizationFilter.h"

DefineStandardPointers(IEndpointSecurityRuleManager)

class EndpointSecurityValidator;

class IEndpointSecurityRuleManager {

    Public Virtual ~IEndpointSecurityRuleManager() = default;

    friend class EndpointSecurityValidator;

    Protected Virtual NoDiscard std::pair<Bool, optional<ResponseEntity<StdString>>> IsAllowed(
        CStdString& url, HttpMethod method, const JwtAuthenticationToken& token) const = 0;

    /**
     * Hook for subclasses; not callable on IEndpointSecurityRuleManager* from outside the hierarchy.
     * Under lock, resolves authorizer via resolveAuthorizer() and stores it for (url, method).
     */
    Protected Virtual Void AddRuleImpl(CStdString& url,
                                       HttpMethod method,
                                       std::function<IAuthorizationFilterPtr()> resolveAuthorizer) = 0;

    /**
     * Builds a TFilter with make_ptr and registers it (same tuple/apply pattern as IAuthorizationFilterFactory::GetFilter).
     */
    Public template<typename TFilter, typename... Args>
    Void AddRule(CStdString& url, HttpMethod method, Args&&... args) {
        static_assert(std::is_base_of<IAuthorizationFilter, TFilter>::value,
                      "IEndpointSecurityRuleManager::AddRule<TFilter>: TFilter must derive from IAuthorizationFilter");
        auto tup = std::make_tuple(std::forward<Args>(args)...);
        AddRuleImpl(url, method, [tup]() mutable -> IAuthorizationFilterPtr {
            return std::apply(
                [](auto&&... a) -> IAuthorizationFilterPtr {
                    return make_ptr<TFilter>(std::forward<decltype(a)>(a)...);
                },
                std::move(tup));
        });
    }
};

#endif // I_ENDPOINT_SECURITY_RULE_MANAGER_H
