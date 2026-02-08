#ifndef HTTP_REQUEST_QUEUE_H
#define HTTP_REQUEST_QUEUE_H

#include "IHttpRequestQueue.h"
#include <queue>

/* @Component */
class HttpRequestQueue final : public IHttpRequestQueue {
    Private std::queue<IHttpRequestPtr> requestQueue;

    Public HttpRequestQueue() = default;
    
    Public ~HttpRequestQueue() override = default;

    // ============================================================================
    // HTTP Request Queue Operations
    // ============================================================================
    
    Public Void EnqueueRequest(IHttpRequestPtr request) override {
        if (request == nullptr) {
            return;
        }
        
        requestQueue.push(request);
    }
    
    Public IHttpRequestPtr DequeueRequest() override {
        if (requestQueue.empty()) {
            return nullptr;
        }
        
        IHttpRequestPtr request = requestQueue.front();
        requestQueue.pop();
        return request;
    }
    
    Public Bool IsEmpty() const override {
        return requestQueue.empty();
    }
    
    Public Bool HasRequests() const override {
        return !requestQueue.empty();
    }
};

#endif // HTTP_REQUEST_QUEUE_H

