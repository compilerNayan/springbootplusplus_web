#ifndef RESPONSEENTITY_H
#define RESPONSEENTITY_H

#include "StandardDefines.h"
#include "HttpStatus.h"
#include <NayanSerializer.h>

/**
 * ResponseEntity class similar to Spring Boot's ResponseEntity
 * Wraps a response body with HTTP status code and headers
 * 
 * @tparam T The type of the response body
 * 
 * Example usage:
 *   ResponseEntity<WifiCredentials> response = ResponseEntity<WifiCredentials>::ok(credentials);
 *   ResponseEntity<StdString> error = ResponseEntity<StdString>::badRequest("Invalid input");
 *   ResponseEntity<Void> noContent = ResponseEntity<Void>::noContent();
 */
template<typename T>
class ResponseEntity {
    Private HttpStatus status_;
    Private Map<StdString, StdString> headers_;
    Private T body_;

public:
    /**
     * Default constructor - creates ResponseEntity with OK status and default-constructed body
     */
    ResponseEntity() 
        : status_(HttpStatus::OK), headers_(), body_() {
    }

    /**
     * Constructor with status and body
     */
    ResponseEntity(HttpStatus status, const T& body) 
        : status_(status), headers_(), body_(body) {
    }

    /**
     * Constructor with status, body, and headers
     */
    ResponseEntity(HttpStatus status, const T& body, const Map<StdString, StdString>& headers) 
        : status_(status), headers_(headers), body_(body) {
    }

    /**
     * Copy constructor
     */
    ResponseEntity(const ResponseEntity& other) 
        : status_(other.status_), headers_(other.headers_), body_(other.body_) {
    }

    /**
     * Assignment operator
     */
    ResponseEntity& operator=(const ResponseEntity& other) {
        if (this != &other) {
            status_ = other.status_;
            headers_ = other.headers_;
            body_ = other.body_;
        }
        return *this;
    }

    /**
     * Get the HTTP status code
     */
    HttpStatus GetStatus() const {
        return status_;
    }

    /**
     * Get the response body
     */
    const T& GetBody() const {
        return body_;
    }

    /**
     * Get the response body (non-const)
     */
    T& GetBody() {
        return body_;
    }

    /**
     * Get all headers
     */
    const Map<StdString, StdString>& GetHeaders() const {
        return headers_;
    }

    /**
     * Get a specific header value
     */
    StdString GetHeader(CStdString& name) const {
        auto it = headers_.find(StdString(name));
        if (it != headers_.end()) {
            return it->second;
        }
        return "";
    }

    /**
     * Check if a header exists
     */
    Bool HasHeader(CStdString& name) const {
        return headers_.find(StdString(name)) != headers_.end();
    }

    /**
     * Add or set a header
     */
    Void AddHeader(CStdString& name, CStdString& value) {
        headers_[StdString(name)] = StdString(value);
    }

    /**
     * Add or set a header (fluent/chaining method)
     * Returns reference to self for method chaining
     */
    ResponseEntity<T>& WithHeader(CStdString& name, CStdString& value) {
        headers_[StdString(name)] = StdString(value);
        return *this;
    }

    /**
     * Set the status code
     */
    Void SetStatus(HttpStatus status) {
        status_ = status;
    }

    /**
     * Set the status code (fluent/chaining method)
     * Returns reference to self for method chaining
     */
    ResponseEntity<T>& WithStatus(HttpStatus status) {
        status_ = status;
        return *this;
    }

    /**
     * Set the body
     */
    Void SetBody(const T& body) {
        body_ = body;
    }

    /**
     * Set the body (fluent/chaining method)
     * Returns reference to self for method chaining
     */
    ResponseEntity<T>& WithBody(const T& body) {
        body_ = body;
        return *this;
    }

    /**
     * Set headers (replaces all existing headers)
     */
    Void SetHeaders(const Map<StdString, StdString>& headers) {
        headers_ = headers;
    }

    /**
     * Set headers (fluent/chaining method)
     * Returns reference to self for method chaining
     */
    ResponseEntity<T>& WithHeaders(const Map<StdString, StdString>& headers) {
        headers_ = headers;
        return *this;
    }

    /**
     * Convert to JSON string for HTTP response
     * Serializes the body and includes status code and headers
     */
    StdString ToJsonString() const {
        // Use SerializationUtility to serialize the body
        StdString bodyJson = nayan::serializer::SerializationUtility::Serialize<T>(body_);
        
        // Build response JSON with status, headers, and body
        JsonDocument doc;
        doc["statusCode"] = StatusToInt(status_);
        doc["statusMessage"] = GetStatusMessage(status_).c_str();
        
        // Add headers
        JsonObject headersObj = doc["headers"].to<JsonObject>();
        for (const auto& pair : headers_) {
            headersObj[pair.first.c_str()] = pair.second.c_str();
        }
        
        // Parse body JSON and add it
        if (!bodyJson.empty()) {
            JsonDocument bodyDoc;
            DeserializationError error = deserializeJson(bodyDoc, bodyJson);
            if (error == DeserializationError::Ok) {
                doc["body"] = bodyDoc.as<JsonObject>();
            } else {
                // If body is not valid JSON, add it as a string
                doc["body"] = bodyJson.c_str();
            }
        } else {
            doc["body"] = JsonObject();
        }
        
        StdString result;
        serializeJson(doc, result);
        return result;
    }

    // ========== Static Factory Methods ==========

    /**
     * Create ResponseEntity with OK (200) status
     */
    Static ResponseEntity<T> Ok(const T& body) {
        return ResponseEntity<T>(HttpStatus::OK, body);
    }

    /**
     * Create ResponseEntity with OK (200) status and headers
     */
    Static ResponseEntity<T> Ok(const T& body, const Map<StdString, StdString>& headers) {
        return ResponseEntity<T>(HttpStatus::OK, body, headers);
    }

    /**
     * Create ResponseEntity with CREATED (201) status
     */
    Static ResponseEntity<T> Created(const T& body) {
        return ResponseEntity<T>(HttpStatus::CREATED, body);
    }

    /**
     * Create ResponseEntity with CREATED (201) status and headers
     */
    Static ResponseEntity<T> Created(const T& body, const Map<StdString, StdString>& headers) {
        return ResponseEntity<T>(HttpStatus::CREATED, body, headers);
    }

    /**
     * Create ResponseEntity with ACCEPTED (202) status
     */
    Static ResponseEntity<T> Accepted(const T& body) {
        return ResponseEntity<T>(HttpStatus::ACCEPTED, body);
    }

    /**
     * Create ResponseEntity with NO_CONTENT (204) status
     */
    Static ResponseEntity<T> NoContent() {
        return ResponseEntity<T>(HttpStatus::NO_CONTENT, T());
    }

    /**
     * Create ResponseEntity with BAD_REQUEST (400) status
     */
    Static ResponseEntity<T> BadRequest(const T& body) {
        return ResponseEntity<T>(HttpStatus::BAD_REQUEST, body);
    }

    /**
     * Create ResponseEntity with UNAUTHORIZED (401) status
     */
    Static ResponseEntity<T> Unauthorized(const T& body) {
        return ResponseEntity<T>(HttpStatus::UNAUTHORIZED, body);
    }

    /**
     * Create ResponseEntity with FORBIDDEN (403) status
     */
    Static ResponseEntity<T> Forbidden(const T& body) {
        return ResponseEntity<T>(HttpStatus::FORBIDDEN, body);
    }

    /**
     * Create ResponseEntity with NOT_FOUND (404) status
     */
    Static ResponseEntity<T> NotFound(const T& body) {
        return ResponseEntity<T>(HttpStatus::NOT_FOUND, body);
    }

    /**
     * Create ResponseEntity with METHOD_NOT_ALLOWED (405) status
     */
    Static ResponseEntity<T> MethodNotAllowed(const T& body) {
        return ResponseEntity<T>(HttpStatus::METHOD_NOT_ALLOWED, body);
    }

    /**
     * Create ResponseEntity with CONFLICT (409) status
     */
    Static ResponseEntity<T> Conflict(const T& body) {
        return ResponseEntity<T>(HttpStatus::CONFLICT, body);
    }

    /**
     * Create ResponseEntity with INTERNAL_SERVER_ERROR (500) status
     */
    Static ResponseEntity<T> InternalServerError(const T& body) {
        return ResponseEntity<T>(HttpStatus::INTERNAL_SERVER_ERROR, body);
    }

    /**
     * Create ResponseEntity with SERVICE_UNAVAILABLE (503) status
     */
    Static ResponseEntity<T> ServiceUnavailable(const T& body) {
        return ResponseEntity<T>(HttpStatus::SERVICE_UNAVAILABLE, body);
    }

    /**
     * Create ResponseEntity with custom status
     */
    Static ResponseEntity<T> Status(HttpStatus status, const T& body) {
        return ResponseEntity<T>(status, body);
    }

    /**
     * Create ResponseEntity with custom status and headers
     */
    Static ResponseEntity<T> Status(HttpStatus status, const T& body, const Map<StdString, StdString>& headers) {
        return ResponseEntity<T>(status, body, headers);
    }
};

/**
 * Specialization for ResponseEntity<Void> (no body)
 */
template<>
class ResponseEntity<Void> {
    Private HttpStatus status_;
    Private Map<StdString, StdString> headers_;

public:
    /**
     * Default constructor - creates ResponseEntity with OK status
     */
    ResponseEntity() 
        : status_(HttpStatus::OK), headers_() {
    }

    /**
     * Constructor with status
     */
    ResponseEntity(HttpStatus status) 
        : status_(status), headers_() {
    }

    /**
     * Constructor with status and headers
     */
    ResponseEntity(HttpStatus status, const Map<StdString, StdString>& headers) 
        : status_(status), headers_(headers) {
    }

    /**
     * Get the HTTP status code
     */
    HttpStatus GetStatus() const {
        return status_;
    }

    /**
     * Get all headers
     */
    const Map<StdString, StdString>& GetHeaders() const {
        return headers_;
    }

    /**
     * Get a specific header value
     */
    StdString GetHeader(CStdString& name) const {
        auto it = headers_.find(StdString(name));
        if (it != headers_.end()) {
            return it->second;
        }
        return "";
    }

    /**
     * Check if a header exists
     */
    Bool HasHeader(CStdString& name) const {
        return headers_.find(StdString(name)) != headers_.end();
    }

    /**
     * Add or set a header
     */
    Void AddHeader(CStdString& name, CStdString& value) {
        headers_[StdString(name)] = StdString(value);
    }

    /**
     * Add or set a header (fluent/chaining method)
     * Returns reference to self for method chaining
     */
    ResponseEntity<Void>& WithHeader(CStdString& name, CStdString& value) {
        headers_[StdString(name)] = StdString(value);
        return *this;
    }

    /**
     * Set the status code
     */
    Void SetStatus(HttpStatus status) {
        status_ = status;
    }

    /**
     * Set the status code (fluent/chaining method)
     * Returns reference to self for method chaining
     */
    ResponseEntity<Void>& WithStatus(HttpStatus status) {
        status_ = status;
        return *this;
    }

    /**
     * Set headers (replaces all existing headers)
     */
    Void SetHeaders(const Map<StdString, StdString>& headers) {
        headers_ = headers;
    }

    /**
     * Set headers (fluent/chaining method)
     * Returns reference to self for method chaining
     */
    ResponseEntity<Void>& WithHeaders(const Map<StdString, StdString>& headers) {
        headers_ = headers;
        return *this;
    }

    /**
     * Convert to JSON string for HTTP response
     * For Void type, only includes status code and headers
     */
    StdString ToJsonString() const {
        JsonDocument doc;
        doc["statusCode"] = StatusToInt(status_);
        doc["statusMessage"] = GetStatusMessage(status_).c_str();
        
        // Add headers
        JsonObject headersObj = doc["headers"].to<JsonObject>();
        for (const auto& pair : headers_) {
            headersObj[pair.first.c_str()] = pair.second.c_str();
        }
        
        // No body for Void type
        doc["body"] = JsonObject();
        
        StdString result;
        serializeJson(doc, result);
        return result;
    }

    // ========== Static Factory Methods ==========

    /**
     * Create ResponseEntity with OK (200) status
     */
    Static ResponseEntity<Void> Ok() {
        return ResponseEntity<Void>(HttpStatus::OK);
    }

    /**
     * Create ResponseEntity with OK (200) status and headers
     */
    Static ResponseEntity<Void> Ok(const Map<StdString, StdString>& headers) {
        return ResponseEntity<Void>(HttpStatus::OK, headers);
    }

    /**
     * Create ResponseEntity with NO_CONTENT (204) status
     */
    Static ResponseEntity<Void> NoContent() {
        return ResponseEntity<Void>(HttpStatus::NO_CONTENT);
    }

    /**
     * Create ResponseEntity with BAD_REQUEST (400) status
     */
    Static ResponseEntity<Void> BadRequest() {
        return ResponseEntity<Void>(HttpStatus::BAD_REQUEST);
    }

    /**
     * Create ResponseEntity with NOT_FOUND (404) status
     */
    Static ResponseEntity<Void> NotFound() {
        return ResponseEntity<Void>(HttpStatus::NOT_FOUND);
    }

    /**
     * Create ResponseEntity with INTERNAL_SERVER_ERROR (500) status
     */
    Static ResponseEntity<Void> InternalServerError() {
        return ResponseEntity<Void>(HttpStatus::INTERNAL_SERVER_ERROR);
    }

    /**
     * Create ResponseEntity with custom status
     */
    Static ResponseEntity<Void> Status(HttpStatus status) {
        return ResponseEntity<Void>(status);
    }

    /**
     * Create ResponseEntity with custom status and headers
     */
    Static ResponseEntity<Void> Status(HttpStatus status, const Map<StdString, StdString>& headers) {
        return ResponseEntity<Void>(status, headers);
    }
};

#endif // RESPONSEENTITY_H

