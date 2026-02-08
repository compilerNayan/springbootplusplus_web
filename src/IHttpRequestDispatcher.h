#ifndef I_HTTP_REQUEST_DISPATCHER_H
#define I_HTTP_REQUEST_DISPATCHER_H

#include <StandardDefines.h>
#include <IHttpRequest.h>
#include <IHttpResponse.h>

DefineStandardPointers(IHttpRequestDispatcher)
class IHttpRequestDispatcher {

    Public Virtual ~IHttpRequestDispatcher() = default;

    Public Virtual IHttpResponsePtr DispatchRequest(IHttpRequestPtr request) = 0;

};

#endif // I_HTTP_REQUEST_DISPATCHER_H