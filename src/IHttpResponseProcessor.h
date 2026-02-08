#ifndef I_HTTP_RESPONSE_PROCESSOR_H
#define I_HTTP_RESPONSE_PROCESSOR_H

#include <StandardDefines.h>

// Forward declarations
DefineStandardPointers(IHttpResponseProcessor)
class IHttpResponseProcessor {

    Public Virtual ~IHttpResponseProcessor() = default;

    // ============================================================================
    // HTTP RESPONSE PROCESSING OPERATIONS
    // ============================================================================
    
    /**
     * @brief Processes a response
     * @return true if a response was processed, false otherwise
     */
    Public Virtual Bool ProcessResponse() = 0;
};

#endif // I_HTTP_RESPONSE_PROCESSOR_H

