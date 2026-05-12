#ifndef JWT_AUTHENTICATION_TOKEN_H
#define JWT_AUTHENTICATION_TOKEN_H

#include <string>
#include <map>
#include <vector>

/** JwtAuthenticator stores failure details under this claims key when authenticated is false. */
inline constexpr const char kJwtAuthFailureClaimKey[] = "auth_failure_reason";

struct JwtAuthenticationToken {
    bool authenticated = false;
    std::map<std::string, std::string> claims;
    std::vector<std::string> authorities;
    std::string principal;
};

#endif // JWT_AUTHENTICATION_TOKEN_H