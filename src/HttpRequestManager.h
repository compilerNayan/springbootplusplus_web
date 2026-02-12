#ifndef HTTP_REQUEST_MANAGER_H
#define HTTP_REQUEST_MANAGER_H

#include "IHttpRequestManager.h"
#include "IHttpRequestQueue.h"
#include "IHttpRequestProcessor.h"
#include "IHttpResponseProcessor.h"
#include <ServerProvider.h>

/* @Component */
class HttpRequestManager final : public IHttpRequestManager {

    /* @Autowired */
    Private IHttpRequestQueuePtr requestQueue;

    /* @Autowired */
    Private IHttpRequestProcessorPtr requestProcessor;

    /* @Autowired */
    Private IHttpResponseProcessorPtr responseProcessor;

    Private IServerPtr server;
    Private IServerPtr secondServer;

    Public HttpRequestManager() {
        server = ServerProvider::GetDefaultServer();
        secondServer = ServerProvider::GetSecondServer();
    }
    
    Public ~HttpRequestManager() override = default;

    // ============================================================================
    // HTTP Request Management Operations
    // ============================================================================
    
    Public Bool RetrieveRequest() override {
        if (server != nullptr) {
            IHttpRequestPtr request = server->ReceiveMessage();
            if (request != nullptr) {
                Serial.println("Received request from primary server");
                Serial.println(server->GetId().c_str());
                requestQueue->EnqueueRequest(request);
                ProcessRequest();
                ProcessResponse();
            }
        }
        Serial.println("Alive here");
        if (secondServer != nullptr) {
            Serial.println("Receiving request from secondary server");
            Serial.println(secondServer->GetId().c_str());
            IHttpRequestPtr request = secondServer->ReceiveMessage();
            if (request != nullptr) {
                Serial.println("Received request from secondary server");
                requestQueue->EnqueueRequest(request);
                ProcessRequest();
                ProcessResponse();
            }
        }
        return true;
    }
    
    Public Bool ProcessRequest() override {
        if (requestProcessor == nullptr) {
            return false;
        }
        
        Bool processedAny = false;
        while (requestQueue->HasRequests()) {
            if (requestProcessor->ProcessRequest()) {
                processedAny = true;
            } else {
                break;
            }
        }
        
        return processedAny;
    }
    
    Public Bool ProcessResponse() override {
        if (responseProcessor == nullptr) {
            return false;
        }
        
        Bool processedAny = false;
        // Process responses until queue is empty or processor returns false
        while (true) {
            if (responseProcessor->ProcessResponse()) {
                processedAny = true;
            } else {
                break;
            }
        }
        
        return processedAny;
    }
    
    Public Bool StartServer(CUInt port = DEFAULT_SERVER_PORT) override {
        if (server == nullptr) {
            return false;
        }
        Bool result = server->Start(port);
        if (result && secondServer != nullptr) {
            secondServer->Start(port);
        }
        return result;
    }
    
    Public Void StopServer() override {
        if (server != nullptr) {
            server->Stop();
        }
        if (secondServer != nullptr) {
            secondServer->Stop();
        }
    }
};

#endif // HTTP_REQUEST_MANAGER_H

