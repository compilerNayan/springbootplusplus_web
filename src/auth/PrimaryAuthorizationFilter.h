#ifndef PRIMARY_AUTHORIZATION_FILTER_H
#define PRIMARY_AUTHORIZATION_FILTER_H

#include <utility>

#include "IAuthorizationFilter.h"
#include "../HttpStatus.h"

/**
 * First-line authorization: allows the request only when JWT authentication succeeded.
 * On failure, returns an HTTP response whose body includes the reason from claims[kJwtAuthFailureClaimKey]
 * (set by JwtAuthenticator), with status 401 for typical auth failures or another code when appropriate
 * (e.g. 503 when device time is not set).
 */
class PrimaryAuthorizationFilter : public IAuthorizationFilter {

    Public Virtual ~PrimaryAuthorizationFilter() override = default;

    Public Virtual std::pair<Bool, optional<ResponseEntity<StdString>>> Authorize(
        const JwtAuthenticationToken& authenticationToken) override {
        if (authenticationToken.authenticated) {
            return {true, std::nullopt};
        }

        StdString reason = ResolveFailureReason(authenticationToken);
        HttpStatus status = HttpStatusForReason(reason);
        StdString body = BuildErrorJson(reason);
        return {false, ResponseEntity<StdString>::Status(status, body)};
    }

    Private Static StdString ResolveFailureReason(const JwtAuthenticationToken& token) {
        Val failIt = token.claims.find(kJwtAuthFailureClaimKey);
        if (failIt != token.claims.end()) {
            return StdString(failIt->second);
        }
        Val errIt = token.claims.find("error");
        if (errIt != token.claims.end()) {
            return StdString(errIt->second);
        }
        return StdString("Authentication failed");
    }

    /**
     * Maps known JwtAuthenticator messages to HTTP statuses; everything else stays 401.
     */
    Private Static HttpStatus HttpStatusForReason(const StdString& reason) {
        if (reason == StdString("Device time not set")) {
            return HttpStatus::SERVICE_UNAVAILABLE;
        }
        return HttpStatus::UNAUTHORIZED;
    }

    Private Static StdString JsonEscape(const StdString& s) {
        StdString out;
        out.reserve(s.size() + 8);
        for (unsigned char c : s) {
            if (c == '"' || c == '\\') {
                out.push_back('\\');
            }
            out.push_back(static_cast<char>(c));
        }
        return out;
    }

    Private Static StdString BuildErrorJson(const StdString& reason) {
        return StdString("{\"error\":\"Authentication failed\",\"message\":\"") + JsonEscape(reason)
            + StdString("\"}");
    }
};

#endif // PRIMARY_AUTHORIZATION_FILTER_H
