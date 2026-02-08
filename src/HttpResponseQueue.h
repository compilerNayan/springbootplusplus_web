#ifndef HTTP_RESPONSE_QUEUE_H
#define HTTP_RESPONSE_QUEUE_H

#include "IHttpResponseQueue.h"
#include <queue>

/* @Component */
class HttpResponseQueue final : public IHttpResponseQueue {
    Private std::queue<IHttpResponsePtr> responseQueue;

    Public HttpResponseQueue() = default;
    
    Public ~HttpResponseQueue() override = default;

    // ============================================================================
    // HTTP Response Queue Operations
    // ============================================================================
    
    Public Void EnqueueResponse(IHttpResponsePtr response) override {
        if (response == nullptr) {
            return;
        }
        
        responseQueue.push(response);
    }
    
    Public IHttpResponsePtr DequeueResponse() override {
        if (responseQueue.empty()) {
            return nullptr;
        }
        
        IHttpResponsePtr response = responseQueue.front();
        responseQueue.pop();
        return response;
    }
    
    Public Bool IsEmpty() const override {
        return responseQueue.empty();
    }
    
    Public Bool HasResponses() const override {
        return !responseQueue.empty();
    }
};

#endif // HTTP_RESPONSE_QUEUE_H

