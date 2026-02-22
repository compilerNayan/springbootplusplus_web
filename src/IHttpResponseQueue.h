#ifndef I_HTTP_RESPONSE_QUEUE_H
#define I_HTTP_RESPONSE_QUEUE_H

#include <StandardDefines.h>
#include <IHttpResponse.h>

// Forward declarations
DefineStandardPointers(IHttpResponseQueue)
class IHttpResponseQueue {

    Public Virtual ~IHttpResponseQueue() = default;

    // ============================================================================
    // HTTP RESPONSE QUEUE OPERATIONS
    // ============================================================================
    
    /**
     * @brief Enqueues an HTTP response into the queue. Routes by response->GetRequestSource():
     *        LocalServer -> local queue, CloudServer -> cloud queue.
     * @param response Pointer to the HTTP response to enqueue
     */
    Public Virtual Void EnqueueResponse(IHttpResponsePtr response) = 0;
    
    /**
     * @brief Gets and removes the front HTTP response from the local queue. Thread-safe.
     * @return Pointer to the HTTP response, or nullptr if local queue is empty
     */
    Public Virtual IHttpResponsePtr DequeueLocalResponse() = 0;

    /**
     * @brief Gets and removes the front HTTP response from the cloud queue. Thread-safe.
     * @return Pointer to the HTTP response, or nullptr if cloud queue is empty
     */
    Public Virtual IHttpResponsePtr DequeueCloudResponse() = 0;

    /**
     * @brief Check if the queue is empty
     * @return true if queue is empty, false otherwise
     */
    Public Virtual Bool IsEmpty() const = 0;
    
    /**
     * @brief Check if the queue has items
     * @return true if queue has items, false if empty
     */
    Public Virtual Bool HasResponses() const = 0;
};

#endif // I_HTTP_RESPONSE_QUEUE_H

