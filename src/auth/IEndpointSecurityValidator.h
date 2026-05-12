#ifndef I_ENDPOINT_SECURITY_VALIDATOR_H
#define I_ENDPOINT_SECURITY_VALIDATOR_H

#include <StandardDefines.h>
#include <HttpMethod.h>

#include "JwtAuthenticationToken.h"

DefineStandardPointers(IEndpointSecurityValidator)

class IEndpointSecurityValidator {

    Public Virtual ~IEndpointSecurityValidator() = default;

    Public Virtual NoDiscard Bool IsAllowed(CStdString& url, HttpMethod method, const JwtAuthenticationToken& token) const = 0;
};

#endif // I_ENDPOINT_SECURITY_VALIDATOR_H
