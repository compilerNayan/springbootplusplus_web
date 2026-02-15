#ifndef HTTP_REQUEST_QUEUE_H
#define HTTP_REQUEST_QUEUE_H

#include "IHttpRequestQueue.h"
#include <queue>
#include <mutex>

/* @Component */
class HttpRequestQueue final : public IHttpRequestQueue {
    Private std::queue<IHttpRequestPtr> requestQueue;
    Private mutable std::mutex queueMutex;

    Public HttpRequestQueue() = default;

    Public ~HttpRequestQueue() override = default;

    // ============================================================================
    // HTTP Request Queue Operations (thread-safe)
    // ============================================================================

    Public Void EnqueueRequest(IHttpRequestPtr request) override {
        if (request == nullptr) {
            return;
        }
        std::lock_guard<std::mutex> lock(queueMutex);
        requestQueue.push(request);
    }

    Public IHttpRequestPtr DequeueRequest() override {
        std::lock_guard<std::mutex> lock(queueMutex);
        if (requestQueue.empty()) {
            return nullptr;
        }
        IHttpRequestPtr request = requestQueue.front();
        requestQueue.pop();
        return request;
    }

    Public Bool IsEmpty() const override {
        std::lock_guard<std::mutex> lock(queueMutex);
        return requestQueue.empty();
    }

    Public Bool HasRequests() const override {
        std::lock_guard<std::mutex> lock(queueMutex);
        return !requestQueue.empty();
    }
};

#endif // HTTP_REQUEST_QUEUE_H

