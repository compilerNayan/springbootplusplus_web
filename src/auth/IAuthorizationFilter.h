#ifndef I_AUTHORIZATION_FILTER_H
#define I_AUTHORIZATION_FILTER_H

#include <StandardDefines.h>
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
     * @return true if the request is allowed to continue to the endpoint handler.
     * @return false if the request must be rejected; the caller should send an appropriate response (e.g. 401 Unauthorized or 403 Forbidden).
     */
    Public Virtual Bool Authorize(const JwtAuthenticationToken& authenticationToken) = 0;
};

#endif // I_AUTHORIZATION_FILTER_H
