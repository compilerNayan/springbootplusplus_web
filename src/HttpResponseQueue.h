#ifndef HTTP_RESPONSE_QUEUE_H
#define HTTP_RESPONSE_QUEUE_H

#include "IHttpResponseQueue.h"
#include <queue>
#include <mutex>

/* @Component */
class HttpResponseQueue final : public IHttpResponseQueue {
    Private std::queue<IHttpResponsePtr> localQueue_;
    Private mutable std::mutex localMutex_;
    Private std::queue<IHttpResponsePtr> cloudQueue_;
    Private mutable std::mutex cloudMutex_;

    Public HttpResponseQueue() = default;

    Public ~HttpResponseQueue() override = default;

    // ============================================================================
    // HTTP Response Queue Operations
    // ============================================================================

    Public Void EnqueueResponse(IHttpResponsePtr response) override {
        if (response == nullptr) return;
        RequestSource source = response->GetRequestSource();
        if (source == RequestSource::LocalServer) {
            std::lock_guard<std::mutex> lock(localMutex_);
            localQueue_.push(std::move(response));
        } else if (source == RequestSource::CloudServer) {
            std::lock_guard<std::mutex> lock(cloudMutex_);
            cloudQueue_.push(std::move(response));
        }
    }

    Public IHttpResponsePtr DequeueLocalResponse() override {
        std::lock_guard<std::mutex> lock(localMutex_);
        if (localQueue_.empty()) return nullptr;
        IHttpResponsePtr r = localQueue_.front();
        localQueue_.pop();
        return r;
    }

    Public IHttpResponsePtr DequeueCloudResponse() override {
        std::lock_guard<std::mutex> lock(cloudMutex_);
        if (cloudQueue_.empty()) return nullptr;
        IHttpResponsePtr r = cloudQueue_.front();
        cloudQueue_.pop();
        return r;
    }

    Public Bool IsEmpty() const override {
        std::lock_guard<std::mutex> lockLocal(localMutex_);
        std::lock_guard<std::mutex> lockCloud(cloudMutex_);
        return localQueue_.empty() && cloudQueue_.empty();
    }

    Public Bool HasResponses() const override {
        return !IsEmpty();
    }
};

#endif // HTTP_RESPONSE_QUEUE_H
