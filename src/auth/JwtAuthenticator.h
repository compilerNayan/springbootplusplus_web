#ifndef JWT_AUTHENTICATOR_H
#define JWT_AUTHENTICATOR_H
#include <string>
#include <map>
#include <vector>
#include <sstream>
#include <algorithm>
#include <ctime>
#include <ArduinoJson.h>

#ifdef ARDUINO
  #include <Arduino.h>
  #include <mbedtls/pk.h>
  #include <mbedtls/md.h>
#else
  #include <iostream>
  #include <openssl/pem.h>
  #include <openssl/evp.h>
  #include <openssl/bio.h>
#endif

#include "JwtAuthenticationToken.h"
#include "IJwtAuthenticator.h"

/* @Component */
class JwtAuthenticator : public IJwtAuthenticator {
private:
    static constexpr long long MIN_VALID_UNIX_TIME = 946684800; // 2000-01-01 UTC

    const char* publicKeyPem = R"(-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAwpYzGK2w+VNbxcyZIOi5
nkSD3hub3jTM6hMVFTvqvI2HWnB780UUq+iT1fugyEuZ/w0KdAaxlI8hwPPTM9pb
wucxyhnXOwcvY5rIyELCbsakI/t5W6fnQ9ZDh45h6BbVd0NR2QMaufMDcc0PKq6m
8wVoUeA66CpYBN+VYkJgTouKeKDfyZVL7xCCQT8iA/PhN6yCanaQHgv1YWEBznbX
XVMy9jAutStkF+qlb8UdClnF/mRM9PiJIL5X2TVzGxDHLu9i6EB36UQXlnfHruUm
f2hKhqVPiEd80gv6aKcNFna0MilZ1GePm5JuClbMO8P/OEocZH2G2ZD90HesYiJG
UwIDAQAB
-----END PUBLIC KEY-----)";

    // Common Base64 URL decode
    std::string base64UrlDecode(const std::string& input) {
        std::string b64 = input;
        std::replace(b64.begin(), b64.end(), '-', '+');
        std::replace(b64.begin(), b64.end(), '_', '/');
        while (b64.size() % 4) b64.push_back('=');

        static const std::string base64_chars =
            "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            "abcdefghijklmnopqrstuvwxyz"
            "0123456789+/";

        std::vector<unsigned char> out;
        int val = 0, valb = -8;
        for (unsigned char c : b64) {
            if (isspace(c)) continue;
            if (c == '=') break;
            int idx = base64_chars.find(c);
            if (idx == std::string::npos) break;
            val = (val << 6) + idx;
            valb += 6;
            if (valb >= 0) {
                out.push_back((unsigned char)((val >> valb) & 0xFF));
                valb -= 8;
            }
        }
        return std::string(out.begin(), out.end());
    }

    std::vector<std::string> splitJwt(const std::string& jwt) {
        std::vector<std::string> parts;
        std::stringstream ss(jwt);
        std::string item;
        while (std::getline(ss, item, '.')) {
            parts.push_back(item);
        }
        return parts;
    }

    // Arduino-specific signature verification
    bool verifySignatureArduino(const std::string& headerPayload,
                                const std::string& signature) {
#ifdef ARDUINO
        mbedtls_pk_context pk;
        mbedtls_pk_init(&pk);
        if (mbedtls_pk_parse_public_key(&pk,
            (const unsigned char*)publicKeyPem,
            strlen(publicKeyPem) + 1) != 0) {
            return false;
        }

        unsigned char hash[32];
        mbedtls_md(mbedtls_md_info_from_type(MBEDTLS_MD_SHA256),
                   (const unsigned char*)headerPayload.data(),
                   headerPayload.size(), hash);

        int ret = mbedtls_pk_verify(&pk, MBEDTLS_MD_SHA256,
                                    hash, sizeof(hash),
                                    (const unsigned char*)signature.data(),
                                    signature.size());
        mbedtls_pk_free(&pk);
        return ret == 0;
#else
        return false;
#endif
    }

    // Desktop-specific signature verification
    bool verifySignatureDesktop(const std::string& headerPayload,
                                const std::string& signature) {
#ifndef ARDUINO
        BIO* bio = BIO_new_mem_buf(publicKeyPem, -1);
        EVP_PKEY* pubKey = PEM_read_bio_PUBKEY(bio, NULL, NULL, NULL);
        BIO_free(bio);

        EVP_MD_CTX* ctx = EVP_MD_CTX_new();
        EVP_DigestVerifyInit(ctx, NULL, EVP_sha256(), NULL, pubKey);
        int ret = EVP_DigestVerify(ctx,
                                   (const unsigned char*)signature.data(),
                                   signature.size(),
                                   (const unsigned char*)headerPayload.data(),
                                   headerPayload.size());
        EVP_MD_CTX_free(ctx);
        EVP_PKEY_free(pubKey);
        return ret == 1;
#else
        return false;
#endif
    }

    // Unified signature verification entry point
    bool verifySignature(const std::string& headerPayload,
                         const std::string& signatureB64) {
        std::string signature = base64UrlDecode(signatureB64);

#ifdef ARDUINO
        return verifySignatureArduino(headerPayload, signature);
#else
        return verifySignatureDesktop(headerPayload, signature);
#endif
    }

    // Generic print method
    void printMessage(const std::string& msg) {
#ifdef ARDUINO
        Serial.println(msg.c_str());
#else
        std::cout << msg << std::endl;
#endif
    }

    bool parseInt64Claim(const JsonVariantConst& value, long long& out) {
        if (value.is<long long>()) {
            out = value.as<long long>();
            return true;
        }
        if (value.is<const char*>()) {
            const char* raw = value.as<const char*>();
            if (raw == nullptr || *raw == '\0') return false;
            char* end = nullptr;
            long long parsed = strtoll(raw, &end, 10);
            if (end == raw || *end != '\0') return false;
            out = parsed;
            return true;
        }
        return false;
    }

    bool validateTimeClaims(const JsonDocument& doc, std::string& error) {
        const long long nowUtc = static_cast<long long>(time(nullptr));
        if (nowUtc < MIN_VALID_UNIX_TIME) {
            error = "Device time not set";
            return false;
        }

        if (doc["exp"].isNull()) {
            error = "Missing exp claim";
            return false;
        }

        long long exp = 0;
        if (!parseInt64Claim(doc["exp"], exp)) {
            error = "Invalid exp claim";
            return false;
        }
        if (nowUtc >= exp) {
            error = "Token expired";
            return false;
        }

        if (!doc["nbf"].isNull()) {
            long long nbf = 0;
            if (!parseInt64Claim(doc["nbf"], nbf)) {
                error = "Invalid nbf claim";
                return false;
            }
            if (nowUtc < nbf) {
                error = "Token not active yet";
                return false;
            }
        }

        return true;
    }

public:
    JwtAuthenticationToken GetAuthenticationToken(const std::string& bearerToken) override {
        JwtAuthenticationToken token;

        std::string jwt = bearerToken;
        if (jwt.rfind("Bearer ", 0) == 0) jwt = jwt.substr(7);

        auto parts = splitJwt(jwt);
        if (parts.size() != 3) {
            token.claims["error"] = "Invalid JWT format";
            return token;
        }

        std::string headerPayload = parts[0] + "." + parts[1];
        if (!verifySignature(headerPayload, parts[2])) {
            token.claims["error"] = "Invalid signature";
            return token;
        }

        std::string payloadJson = base64UrlDecode(parts[1]);
        DynamicJsonDocument doc(1024);
        auto err = deserializeJson(doc, payloadJson);
        if (err) {
            token.claims["error"] = "Failed to parse payload";
            return token;
        }

        std::string timeError;
        if (!validateTimeClaims(doc, timeError)) {
            token.claims["error"] = timeError;
            return token;
        }

        for (JsonPair kv : doc.as<JsonObject>()) {
            token.claims[kv.key().c_str()] = kv.value().as<std::string>();
        }

        // Set principal (subject or deviceId)
        if (token.claims.count("sub")) {
            token.principal = token.claims["sub"];
        } else if (token.claims.count("deviceId")) {
            token.principal = token.claims["deviceId"];
        }

        // Extract authorities (roles/scopes)
        if (token.claims.count("role")) {
            token.authorities.push_back("ROLE_" + token.claims["role"]);
        }
        if (token.claims.count("roles")) {
            // If roles is a comma-separated string
            std::stringstream ss(token.claims["roles"]);
            std::string role;
            while (std::getline(ss, role, ',')) {
                token.authorities.push_back("ROLE_" + role);
            }
        }

        token.authenticated = true;
        return token;
    }
};

#endif // JWT_AUTHENTICATOR_H