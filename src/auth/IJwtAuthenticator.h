#ifndef I_JWT_AUTHENTICATOR_H
#define I_JWT_AUTHENTICATOR_H

#include <StandardDefines.h>
#include <string>

#include "JwtAuthenticationToken.h"

DefineStandardPointers(IJwtAuthenticator)

class IJwtAuthenticator {

    Public Virtual ~IJwtAuthenticator() = default;

    Public Virtual JwtAuthenticationToken GetAuthenticationToken(const std::string& bearerToken) = 0;
};

#endif // I_JWT_AUTHENTICATOR_H
