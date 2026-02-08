#ifndef HTTP_REQUEST_PROCESSOR_H
#define HTTP_REQUEST_PROCESSOR_H

#include "IHttpRequestProcessor.h"
#include "IHttpRequestQueue.h"
#include "IHttpRequestDispatcher.h"
#include "IHttpResponseQueue.h"
#include <IHttpResponse.h>

/* @Component */
class HttpRequestProcessor final : public IHttpRequestProcessor {

    /* @Autowired */
    Private IHttpRequestQueuePtr requestQueue;

    /* @Autowired */
    Private IHttpRequestDispatcherPtr dispatcher;

    /* @Autowired */
    Private IHttpResponseQueuePtr responseQueue;

    Public HttpRequestProcessor() = default;
    
    Public ~HttpRequestProcessor() override = default;

    // ============================================================================
    // HTTP Request Processing Operations
    // ============================================================================
    
    Public Bool ProcessRequest() override {
        if (requestQueue->IsEmpty()) {
            return false;
        }
        
        IHttpRequestPtr request = requestQueue->DequeueRequest();
        if (request == nullptr) {
            return false;
        }
        
        // Enqueue response into response queue
        responseQueue->EnqueueResponse(dispatcher->DispatchRequest(request));
        
        return true;
    }
};

#endif // HTTP_REQUEST_PROCESSOR_H

