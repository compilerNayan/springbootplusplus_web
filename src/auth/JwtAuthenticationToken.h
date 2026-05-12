#ifndef JWT_AUTHENTICATION_TOKEN_H
#define JWT_AUTHENTICATION_TOKEN_H

#include <string>
#include <map>
#include <vector>

struct JwtAuthenticationToken {
    bool authenticated = false;
    std::map<std::string, std::string> claims;
    std::vector<std::string> authorities;
    std::string principal; 
};

#endif // JWT_AUTHENTICATION_TOKEN_H