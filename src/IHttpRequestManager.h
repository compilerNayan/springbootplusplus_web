#ifndef I_HTTP_REQUEST_MANAGER_H
#define I_HTTP_REQUEST_MANAGER_H

#include <StandardDefines.h>
#include <IHttpRequest.h>
#include <IServer.h>

// Forward declarations
DefineStandardPointers(IHttpRequestManager)
class IHttpRequestManager {

    Public Virtual ~IHttpRequestManager() = default;

    // ============================================================================
    // HTTP REQUEST MANAGEMENT OPERATIONS
    // ============================================================================
    
    /**
     * @brief Retrieves a request from the server and adds it to the queue if available
     * @return true if a request was retrieved and added to the queue, false otherwise
     */
    Public Virtual Bool RetrieveRequest() = 0;
    
    /**
     * @brief Processes all requests from the queue using the request processor
     * @return true if at least one request was processed, false if queue was empty
     */
    Public Virtual Bool ProcessRequest() = 0;
    
    /**
     * @brief Processes all responses from the queue using the response processor
     * @return true if at least one response was processed, false if queue was empty
     */
    Public Virtual Bool ProcessResponse() = 0;
    
    /**
     * @brief Starts the server
     * @param port Port number to listen on (default: DEFAULT_SERVER_PORT)
     * @return true if server started successfully, false otherwise
     */
    Public Virtual Bool StartServer(CUInt port = DEFAULT_SERVER_PORT) = 0;
    
    /**
     * @brief Stops the server
     */
    Public Virtual Void StopServer() = 0;
};

#endif // I_HTTP_REQUEST_MANAGER_H

