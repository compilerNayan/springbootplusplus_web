#ifndef HTTP_REQUEST_DISPATCHER_H
#define HTTP_REQUEST_DISPATCHER_H

#include <unordered_map>
#include <NayanSerializer.h>
#include "EndpointTrie.h"
#include <StandardDefines.h>
#include <sstream>
#include <stdexcept>
#include <type_traits>
#include <algorithm>
#include <cctype>
#include <iomanip>

#ifdef ARDUINO
    #include <Arduino.h>
    #define std_print(x) Serial.print(x)
    #define std_println(x) Serial.println(x)
#else
    #include <iostream>
    #define std_print(x) std::cout << x
    #define std_println(x) std::cout << x << std::endl
#endif

#include "IHttpRequestDispatcher.h"
#include <IHttpResponse.h>
#include "ResponseEntityToHttpResponse.h"

/* @Component */
class HttpRequestDispatcher : public IHttpRequestDispatcher {

    Private UnorderedStdMap<StdString, std::function<IHttpResponsePtr(CStdString, StdMap<StdString, StdString>)>> getMappings;
    Private UnorderedStdMap<StdString, std::function<IHttpResponsePtr(CStdString, StdMap<StdString, StdString>)>> postMappings;
    Private UnorderedStdMap<StdString, std::function<IHttpResponsePtr(CStdString, StdMap<StdString, StdString>)>> putMappings;
    Private UnorderedStdMap<StdString, std::function<IHttpResponsePtr(CStdString, StdMap<StdString, StdString>)>> patchMappings;
    Private UnorderedStdMap<StdString, std::function<IHttpResponsePtr(CStdString, StdMap<StdString, StdString>)>> deleteMappings;
    Private UnorderedStdMap<StdString, std::function<IHttpResponsePtr(CStdString, StdMap<StdString, StdString>)>> optionsMappings;
    Private UnorderedStdMap<StdString, std::function<IHttpResponsePtr(CStdString, StdMap<StdString, StdString>)>> headMappings;
    Private UnorderedStdMap<StdString, std::function<IHttpResponsePtr(CStdString, StdMap<StdString, StdString>)>> traceMappings;
    Private UnorderedStdMap<StdString, std::function<IHttpResponsePtr(CStdString, StdMap<StdString, StdString>)>> connectMappings;

    Private EndpointTrie endpointTrie;

    Public HttpRequestDispatcher() {
        InitializeMappings();
        InsertMappingsToTrie();
    }

    Public ~HttpRequestDispatcher() = default;

    Public IHttpResponsePtr DispatchRequest(IHttpRequestPtr request) override {
        CStdString url = request->GetPath();
        CStdString payload = request->GetBody();
        
        EndpointMatchResult result = endpointTrie.Search(url);
        if(result.found == false) {
            // Return 404 Not Found
            StdString errorJson = "{\"error\":\"Not Found\",\"message\":\"No pattern matched for URL: " + url + "\"}";
            ResponseEntity<StdString> errorResponse = ResponseEntity<StdString>::NotFound(errorJson);
            IHttpResponsePtr response = ResponseEntityConverter::ToHttpResponse<StdString>(errorResponse);
            StdString requestId = StdString(request->GetRequestId());
            if (!requestId.empty()) {
                response->SetRequestId(requestId);
            }
            return response;
        }
        
        Val variables = result.variables;
        Val patternUrl = result.pattern;
        
        // Get request ID from the request
        StdString requestId = StdString(request->GetRequestId());

        try {
            IHttpResponsePtr response = nullptr;
            
            switch (request->GetMethod()) {
                case HttpMethod::GET:
                    if (getMappings.find(patternUrl) == getMappings.end()) {
                        return nullptr;
                    }
                    response = getMappings[patternUrl](payload, variables);
                    break;
                case HttpMethod::POST:
                    if (postMappings.find(patternUrl) == postMappings.end()) {
                        return nullptr;
                    }
                    response = postMappings[patternUrl](payload, variables);
                    break;
                case HttpMethod::PUT:
                    if (putMappings.find(patternUrl) == putMappings.end()) {
                        return nullptr;
                    }
                    response = putMappings[patternUrl](payload, variables);
                    break;
                case HttpMethod::PATCH:
                    if (patchMappings.find(patternUrl) == patchMappings.end()) {
                        return nullptr;
                    }
                    response = patchMappings[patternUrl](payload, variables);
                    break;
                case HttpMethod::DELETE:
                    if (deleteMappings.find(patternUrl) == deleteMappings.end()) {
                        return nullptr;
                    }
                    response = deleteMappings[patternUrl](payload, variables);
                    break;
                case HttpMethod::OPTIONS:
                    if (optionsMappings.find(patternUrl) == optionsMappings.end()) {
                        return nullptr;
                    }
                    response = optionsMappings[patternUrl](payload, variables);
                    break;
                case HttpMethod::HEAD:
                    if (headMappings.find(patternUrl) == headMappings.end()) {
                        return nullptr;
                    }
                    response = headMappings[patternUrl](payload, variables);
                    break;
                case HttpMethod::TRACE:
                    if (traceMappings.find(patternUrl) == traceMappings.end()) {
                        return nullptr;
                    }
                    response = traceMappings[patternUrl](payload, variables);
                    break;
                case HttpMethod::CONNECT:
                    if (connectMappings.find(patternUrl) == connectMappings.end()) {
                        return nullptr;
                    }
                    response = connectMappings[patternUrl](payload, variables);
                    break;
            }
            
            // If response was created without request ID, set it now
            if (response != nullptr && !requestId.empty() && response->GetRequestId().empty()) {
                response->SetRequestId(requestId);
            }
            
            return response;
    
        } catch (const std::exception& e) {
            // Create proper error response using ResponseEntity (Spring Boot style)
            StdString errorMessage = StdString(e.what());
            StdString errorJson = "{\"error\":\"Internal Server Error\",\"message\":\"" + errorMessage + "\"}";
            ResponseEntity<StdString> errorResponse = ResponseEntity<StdString>::InternalServerError(errorJson);
            IHttpResponsePtr response = ResponseEntityConverter::ToHttpResponse<StdString>(errorResponse);
            if (response != nullptr && !requestId.empty()) {
                response->SetRequestId(requestId);
            }
            return response;
        } catch (...) {
            // Handle any other exception type (not derived from std::exception)
            StdString errorJson = "{\"error\":\"Internal Server Error\",\"message\":\"Unknown exception occurred\"}";
            ResponseEntity<StdString> errorResponse = ResponseEntity<StdString>::InternalServerError(errorJson);
            IHttpResponsePtr response = ResponseEntityConverter::ToHttpResponse<StdString>(errorResponse);
            if (response != nullptr && !requestId.empty()) {
                response->SetRequestId(requestId);
            }
            return response;
        }

    }

    Private Void InitializeMappings() {

    }

    Private Void InsertMappingsToTrie() {
        for (const auto& pair : getMappings) {
            endpointTrie.Insert(pair.first);
        }
        for (const auto& pair : postMappings) {
            endpointTrie.Insert(pair.first);
        }
        for (const auto& pair : putMappings) {
            endpointTrie.Insert(pair.first);
        }
        for (const auto& pair : patchMappings) {
            endpointTrie.Insert(pair.first);
        }
        for (const auto& pair : deleteMappings) {
            endpointTrie.Insert(pair.first);
        }
        for (const auto& pair : optionsMappings) {
            endpointTrie.Insert(pair.first);
        }
        for (const auto& pair : headMappings) {
            endpointTrie.Insert(pair.first);
        }
        for (const auto& pair : traceMappings) {
            endpointTrie.Insert(pair.first);
        }
        for (const auto& pair : connectMappings) {
            endpointTrie.Insert(pair.first);
        }
    }

    /**
     * URL decode helper function
     * Decodes percent-encoded strings (e.g., %20 -> space, %21 -> !)
     * 
     * @param str The URL-encoded string to decode
     * @return The decoded string
     */
    Private Static StdString UrlDecode(CStdString str) {
        StdString result;
        result.reserve(str.length()); // Reserve space for efficiency
        
        for (size_t i = 0; i < str.length(); ++i) {
            if (str[i] == '%' && i + 2 < str.length()) {
                // Check if we have a valid percent-encoded sequence (%XX)
                char c1 = str[i + 1];
                char c2 = str[i + 2];
                
                // Check if both characters are hexadecimal digits
                if (std::isxdigit(c1) && std::isxdigit(c2)) {
                    // Convert hex digits to integer
                    int value;
                    std::istringstream hexStream(StdString(1, c1) + StdString(1, c2));
                    hexStream >> std::hex >> value;
                    
                    // Add the decoded character
                    result += static_cast<char>(value);
                    i += 2; // Skip the next two characters (already processed)
                } else {
                    // Invalid percent encoding, keep the % as-is
                    result += str[i];
                }
            } else if (str[i] == '+') {
                // + is often used to represent space in URLs (though more common in query strings)
                result += ' ';
            } else {
                // Regular character, add as-is
                result += str[i];
            }
        }
        
        return result;
    }   
    /**
     * Template function to convert a string to a given type.
     * 
     * - If Type is string-related (StdString, CStdString, std::string, string), returns as-is
     * - If Type is a primitive type (int, Int, long, Long, float, double, bool, etc.), converts from string
     * - Handles types from StandardDefines.h (Int, Long, UInt, ULong, Bool, etc.)
     * 
     * @tparam Type The target type to convert to
     * @param str The input string to convert
     * @return The converted value of type Type
     */
    Public template<typename Type>
    Static Type ConvertToType(CStdString str) {
        // Handle string types - URL decode first, then return
        if constexpr (std::is_same_v<Type, StdString> || 
                      std::is_same_v<Type, CStdString> ||
                      std::is_same_v<Type, std::string> ||
                      std::is_same_v<Type, const std::string>) {
            // URL decode the string (e.g., %20 -> space, My%20Name -> My Name)
            return UrlDecode(str);
        }
        // Handle boolean types (bool, Bool, CBool)
        else if constexpr (std::is_same_v<Type, bool> || 
                          std::is_same_v<Type, Bool> || 
                          std::is_same_v<Type, CBool>) {
            StdString lower = str;
            std::transform(lower.begin(), lower.end(), lower.begin(), ::tolower);
            if (lower == "true" || lower == "1") {
                return true;
            } else if (lower == "false" || lower == "0") {
                return false;
            } else {
                throw std::invalid_argument("Invalid boolean value: " + StdString(str));
            }
        }
        // Handle signed integer types (int, Int, CInt, long, Long, CLong, etc.)
        else if constexpr (std::is_integral_v<Type> && std::is_signed_v<Type>) {
            try {
                if constexpr (sizeof(Type) <= sizeof(int)) {
                    return static_cast<Type>(std::stoi(str));
                } else if constexpr (sizeof(Type) <= sizeof(long)) {
                    return static_cast<Type>(std::stol(str));
                } else {
                    return static_cast<Type>(std::stoll(str));
                }
            } catch (const std::exception& e) {
                throw std::invalid_argument("Invalid signed integer value: " + StdString(str));
            }
        }
        // Handle unsigned integer types (unsigned int, UInt, CUInt, unsigned long, ULong, CULong, etc.)
        else if constexpr (std::is_integral_v<Type> && std::is_unsigned_v<Type>) {
            try {
                if constexpr (sizeof(Type) <= sizeof(unsigned int)) {
                    return static_cast<Type>(std::stoul(str));
                } else if constexpr (sizeof(Type) <= sizeof(unsigned long)) {
                    return static_cast<Type>(std::stoul(str));
                } else {
                    return static_cast<Type>(std::stoull(str));
                }
            } catch (const std::exception& e) {
                throw std::invalid_argument("Invalid unsigned integer value: " + StdString(str));
            }
        }
        // Handle floating point types (float, double, long double)
        else if constexpr (std::is_floating_point_v<Type>) {
            try {
                if constexpr (std::is_same_v<Type, float>) {
                    return std::stof(str);
                } else if constexpr (std::is_same_v<Type, double>) {
                    return std::stod(str);
                } else {
                    return std::stold(str);
                }
            } catch (const std::exception& e) {
                throw std::invalid_argument("Invalid floating point value: " + StdString(str));
            }
        }
        // Handle character types (char, Char, CChar, unsigned char, UChar, CUChar, UInt8)
        else if constexpr (std::is_same_v<Type, char> || 
                          std::is_same_v<Type, Char> || 
                          std::is_same_v<Type, CChar> ||
                          std::is_same_v<Type, unsigned char> || 
                          std::is_same_v<Type, UChar> || 
                          std::is_same_v<Type, CUChar> ||
                          std::is_same_v<Type, UInt8>) {
            if (str.length() == 1) {
                return static_cast<Type>(str[0]);
            } else if (str.length() == 0) {
                return static_cast<Type>(0);
            } else {
                // Try to parse as integer for character types
                try {
                    return static_cast<Type>(std::stoi(str));
                } catch (const std::exception& e) {
                    throw std::invalid_argument("Invalid character value: " + StdString(str));
                }
            }
        }
        // Fallback: for non-primitive, non-string types, use SerializationUtility::Deserialize
        else {
            return nayan::serializer::SerializationUtility::Deserialize<Type>(str);
        }
    }

};

#endif // HTTP_REQUEST_DISPATCHER_H