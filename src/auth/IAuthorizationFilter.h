#ifndef I_AUTHORIZATION_FILTER_H
#define I_AUTHORIZATION_FILTER_H

#include <StandardDefines.h>
#include <utility>

#include "../ResponseEntity.h"
#include "JwtAuthenticationToken.h"

DefineStandardPointers(IAuthorizationFilter)

/**
 * Runs before a request is dispatched to a route handler. Implementations may validate Bearer tokens,
 * roles, scopes, or other policy and decide whether the request may proceed.
 */
class IAuthorizationFilter {

    Public Virtual ~IAuthorizationFilter() = default;

    /**
     * @param authenticationToken The parsed JWT authentication token to evaluate for access.
     * @return pair.first true if the request is allowed to continue to the endpoint handler.
     * @return pair.first false if the request must be rejected.
     * @return pair.second optional response to send when rejected (e.g. 401/403 with message body).
     */
    Public Virtual std::pair<Bool, optional<ResponseEntity<StdString>>> Authorize(
        const JwtAuthenticationToken& authenticationToken) = 0;
};

#endif // I_AUTHORIZATION_FILTER_H
