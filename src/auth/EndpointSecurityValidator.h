#ifndef ENDPOINT_SECURITY_VALIDATOR_H
#define ENDPOINT_SECURITY_VALIDATOR_H

#include <StandardDefines.h>

#include "IEndpointSecurityRuleManager.h"
#include "IEndpointSecurityValidator.h"

/* @Component */
class EndpointSecurityValidator : public IEndpointSecurityValidator {

    /* @Autowired */
    Private IEndpointSecurityRuleManagerPtr endpointSecurityConfig;

    Public EndpointSecurityValidator() = default;

    Public ~EndpointSecurityValidator() override = default;

    Public NoDiscard std::pair<Bool, optional<ResponseEntity<StdString>>> IsAllowed(
        CStdString& url, HttpMethod method, const JwtAuthenticationToken& token) const override {
        if (!endpointSecurityConfig) {
            return {
                false,
                ResponseEntity<StdString>::InternalServerError("EndpointSecurityConfig is not available")
            };
        }
        return endpointSecurityConfig->IsAllowed(url, method, token);
    }
};

#endif // ENDPOINT_SECURITY_VALIDATOR_H
