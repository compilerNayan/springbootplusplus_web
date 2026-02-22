#ifndef RESPONSEENTITY_TO_HTTPRESPONSE_H
#define RESPONSEENTITY_TO_HTTPRESPONSE_H

#include "ResponseEntity.h"
#include "HttpStatus.h"
#include <IHttpResponse.h>
#include <SimpleHttpResponse.h>
#include <NayanSerializer.h>

/**
 * Utility functions to convert ResponseEntity<T> to IHttpResponse
 * 
 * This utility provides template functions to convert ResponseEntity objects
 * to IHttpResponse objects, handling primitive types, strings, and complex types.
 */

namespace ResponseEntityConverter {

    /**
     * Type trait to check if a type is a primitive type.
     * Matches the logic from SerializationUtility::is_primitive_type
     */
    template<typename T>
    struct is_primitive_type {
        static constexpr bool value = 
            std::is_same_v<T, int> || std::is_same_v<T, unsigned int> ||
            std::is_same_v<T, long> || std::is_same_v<T, unsigned long> ||
            std::is_same_v<T, short> || std::is_same_v<T, unsigned short> ||
            std::is_same_v<T, char> || std::is_same_v<T, unsigned char> ||
            std::is_same_v<T, bool> || std::is_same_v<T, float> ||
            std::is_same_v<T, double> || std::is_same_v<T, size_t> ||
            // StandardDefines types
            std::is_same_v<T, Int> || std::is_same_v<T, CInt> ||
            std::is_same_v<T, UInt> || std::is_same_v<T, CUInt> ||
            std::is_same_v<T, Long> || std::is_same_v<T, CLong> ||
            std::is_same_v<T, ULong> || std::is_same_v<T, CULong> ||
            std::is_same_v<T, UInt8> ||
            std::is_same_v<T, Char> || std::is_same_v<T, CChar> ||
            std::is_same_v<T, UChar> || std::is_same_v<T, CUChar> ||
            std::is_same_v<T, Bool> || std::is_same_v<T, CBool> ||
            std::is_same_v<T, Size> || std::is_same_v<T, CSize> ||
            std::is_same_v<T, StdString> || std::is_same_v<T, CStdString>;
    };
    
    template<typename T>
    inline constexpr bool is_primitive_type_v = is_primitive_type<T>::value;

    /**
     * Convert ResponseEntity<T> to IHttpResponse (without request ID)
     * Handles primitive types, strings, and complex types
     * Request ID can be set later using SetRequestId() method
     * 
     * @tparam T The type of the response body
     * @param entity The ResponseEntity<T> to convert
     * @return IHttpResponsePtr (shared_ptr)
     */
    template<typename T>
    inline IHttpResponsePtr ToHttpResponse(const ResponseEntity<T>& entity) {
        // Get status code and message
        HttpStatus status = entity.GetStatus();
        UInt statusCode = StatusToInt(status);
        StdString statusMessage = GetStatusMessage(status);
        
        // Get headers
        StdMap<StdString, StdString> headers = entity.GetHeaders();
        
        // Convert body to string
        StdString bodyStr;
        
        // Special handling for Void - no body
        if constexpr (std::is_same_v<T, Void>) {
            bodyStr = "";
        } else {
            // Convert body to string based on type
            using namespace nayan::serializer;
            
            // Check if T is primitive type (includes strings from StandardDefines)
            if constexpr (is_primitive_type_v<T>) {
                // Primitive type or string (StdString, CStdString) - convert directly to string
                bodyStr = SerializationUtility::Serialize<T>(entity.GetBody());
            } else if constexpr (std::is_same_v<T, std::string> ||
                                 std::is_same_v<T, const char*> ||
                                 std::is_same_v<T, char*>) {
                // Standard string types - use as-is
                const T& body = entity.GetBody();
                bodyStr = StdString(body);
            } else {
                // Complex type - call Serialize() method via SerializationUtility
                bodyStr = SerializationUtility::Serialize<T>(entity.GetBody());
            }
        }
        
        // Create SimpleHttpResponse with status, headers, and body (empty requestId)
        StdString emptyRequestId = "";
        IHttpResponsePtr response = make_ptr<SimpleHttpResponse>(emptyRequestId, RequestSource::LocalServer, statusCode, statusMessage, headers, bodyStr);
        return response;
    }

    /**
     * Convert ResponseEntity<T> to IHttpResponse (with request ID)
     * Handles primitive types, strings, and complex types
     * 
     * @tparam T The type of the response body
     * @param requestId The unique request ID (GUID) for this response
     * @param entity The ResponseEntity<T> to convert
     * @return IHttpResponsePtr (shared_ptr)
     */
    template<typename T>
    inline IHttpResponsePtr ToHttpResponse(CStdString& requestId, const ResponseEntity<T>& entity) {
        // Get status code and message
        HttpStatus status = entity.GetStatus();
        UInt statusCode = StatusToInt(status);
        StdString statusMessage = GetStatusMessage(status);
        
        // Get headers
        StdMap<StdString, StdString> headers = entity.GetHeaders();
        
        // Convert body to string
        StdString bodyStr;
        
        // Special handling for Void - no body
        if constexpr (std::is_same_v<T, Void>) {
            bodyStr = "";
        } else {
            // Convert body to string based on type
            using namespace nayan::serializer;
            
            // Check if T is primitive type (includes strings from StandardDefines)
            if constexpr (is_primitive_type_v<T>) {
                // Primitive type or string (StdString, CStdString) - convert directly to string
                bodyStr = SerializationUtility::Serialize<T>(entity.GetBody());
            } else if constexpr (std::is_same_v<T, std::string> ||
                                 std::is_same_v<T, const char*> ||
                                 std::is_same_v<T, char*>) {
                // Standard string types - use as-is
                const T& body = entity.GetBody();
                bodyStr = StdString(body);
            } else {
                // Complex type - call Serialize() method via SerializationUtility
                bodyStr = SerializationUtility::Serialize<T>(entity.GetBody());
            }
        }
        
        // Create SimpleHttpResponse with status, headers, and body
        IHttpResponsePtr response = make_ptr<SimpleHttpResponse>(requestId, RequestSource::LocalServer, statusCode, statusMessage, headers, bodyStr);
        return response;
    }

    /**
     * Overload for ResponseEntity<Void> (no body, without request ID)
     */
    inline IHttpResponsePtr ToHttpResponse(const ResponseEntity<Void>& entity) {
        // Get status code and message
        HttpStatus status = entity.GetStatus();
        UInt statusCode = StatusToInt(status);
        StdString statusMessage = GetStatusMessage(status);
        
        // Get headers
        StdMap<StdString, StdString> headers = entity.GetHeaders();
        
        // Void has no body
        StdString bodyStr = "";
        
        // Create SimpleHttpResponse with status, headers, and empty body (empty requestId)
        StdString emptyRequestId = "";
        IHttpResponsePtr response = make_ptr<SimpleHttpResponse>(emptyRequestId, RequestSource::LocalServer, statusCode, statusMessage, headers, bodyStr);
        return response;
    }

    /**
     * Overload for ResponseEntity<Void> (no body, with request ID)
     */
    inline IHttpResponsePtr ToHttpResponse(CStdString& requestId, const ResponseEntity<Void>& entity) {
        // Get status code and message
        HttpStatus status = entity.GetStatus();
        UInt statusCode = StatusToInt(status);
        StdString statusMessage = GetStatusMessage(status);
        
        // Get headers
        StdMap<StdString, StdString> headers = entity.GetHeaders();
        
        // Void has no body
        StdString bodyStr = "";
        
        // Create SimpleHttpResponse with status, headers, and empty body
        IHttpResponsePtr response = make_ptr<SimpleHttpResponse>(requestId, RequestSource::LocalServer, statusCode, statusMessage, headers, bodyStr);
        return response;
    }

    /**
     * Create IHttpResponsePtr with 200 OK status from a primitive type or string (without request ID)
     * Handles: int, Int, float, double, bool, Bool, StdString, CStdString, std::string, const char*, char*
     * Request ID can be set later using SetRequestId() method
     * 
     * @tparam T The type of the body (primitive or string)
     * @param body The body value to convert
     * @return IHttpResponsePtr with 200 OK status
     */
    template<typename T>
    inline IHttpResponsePtr CreateOkResponse(const T& body) {
        using namespace nayan::serializer;
        
        // Convert body to string
        StdString bodyStr;
        
        // Check if T is primitive type (includes strings from StandardDefines)
        if constexpr (is_primitive_type_v<T>) {
            // Primitive type or string (StdString, CStdString) - convert directly to string
            bodyStr = SerializationUtility::Serialize<T>(body);
        } else if constexpr (std::is_same_v<T, std::string>) {
            // Standard string type
            bodyStr = StdString(body);
        } else if constexpr (std::is_same_v<T, const char*> || std::is_same_v<T, char*>) {
            // C-style string
            bodyStr = StdString(body);
        } else {
            // For other types, try to serialize
            bodyStr = SerializationUtility::Serialize<T>(body);
        }
        
        // Create SimpleHttpResponse with 200 OK status (empty requestId)
        StdString emptyRequestId = "";
        UInt statusCode = 200;
        StdString statusMessage = "OK";
        StdMap<StdString, StdString> headers;
        headers["Content-Type"] = "application/json";
        
        IHttpResponsePtr response = make_ptr<SimpleHttpResponse>(emptyRequestId, RequestSource::LocalServer, statusCode, statusMessage, headers, bodyStr);
        return response;
    }

    /**
     * Create IHttpResponsePtr with 200 OK status from a primitive type or string (with request ID)
     * Handles: int, Int, float, double, bool, Bool, StdString, CStdString, std::string, const char*, char*
     * 
     * @tparam T The type of the body (primitive or string)
     * @param requestId The unique request ID (GUID) for this response
     * @param body The body value to convert
     * @return IHttpResponsePtr with 200 OK status
     */
    template<typename T>
    inline IHttpResponsePtr CreateOkResponse(CStdString& requestId, const T& body) {
        using namespace nayan::serializer;
        
        // Convert body to string
        StdString bodyStr;
        
        // Check if T is primitive type (includes strings from StandardDefines)
        if constexpr (is_primitive_type_v<T>) {
            // Primitive type or string (StdString, CStdString) - convert directly to string
            bodyStr = SerializationUtility::Serialize<T>(body);
        } else if constexpr (std::is_same_v<T, std::string>) {
            // Standard string type
            bodyStr = StdString(body);
        } else if constexpr (std::is_same_v<T, const char*> || std::is_same_v<T, char*>) {
            // C-style string
            bodyStr = StdString(body);
        } else {
            // For other types, try to serialize
            bodyStr = SerializationUtility::Serialize<T>(body);
        }
        
        // Create SimpleHttpResponse with 200 OK status
        UInt statusCode = 200;
        StdString statusMessage = "OK";
        StdMap<StdString, StdString> headers;
        headers["Content-Type"] = "application/json";
        
        IHttpResponsePtr response = make_ptr<SimpleHttpResponse>(requestId, RequestSource::LocalServer, statusCode, statusMessage, headers, bodyStr);
        return response;
    }

    /**
     * Create IHttpResponsePtr with 200 OK status and no body (without request ID)
     * Used for Void responses or when no body is needed
     * Request ID can be set later using SetRequestId() method
     * 
     * @return IHttpResponsePtr with 200 OK status and empty body
     */
    inline IHttpResponsePtr CreateOkResponse() {
        // Create SimpleHttpResponse with 200 OK status (empty requestId, empty body)
        StdString emptyRequestId = "";
        UInt statusCode = 200;
        StdString statusMessage = "OK";
        StdMap<StdString, StdString> headers;
        StdString emptyBody = "";
        
        IHttpResponsePtr response = make_ptr<SimpleHttpResponse>(emptyRequestId, RequestSource::LocalServer, statusCode, statusMessage, headers, emptyBody);
        return response;
    }

    /**
     * Create IHttpResponsePtr with 200 OK status and no body (with request ID)
     * Used for Void responses or when no body is needed
     * 
     * @param requestId The unique request ID (GUID) for this response
     * @return IHttpResponsePtr with 200 OK status and empty body
     */
    inline IHttpResponsePtr CreateOkResponse(CStdString& requestId) {
        // Create SimpleHttpResponse with 200 OK status (empty body)
        UInt statusCode = 200;
        StdString statusMessage = "OK";
        StdMap<StdString, StdString> headers;
        StdString emptyBody = "";
        
        IHttpResponsePtr response = make_ptr<SimpleHttpResponse>(requestId, RequestSource::LocalServer, statusCode, statusMessage, headers, emptyBody);
        return response;
    }

} // namespace ResponseEntityConverter

#endif // RESPONSEENTITY_TO_HTTPRESPONSE_H

