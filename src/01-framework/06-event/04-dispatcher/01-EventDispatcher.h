#ifndef EVENT_DISPATCHER_H
#define EVENT_DISPATCHER_H

#include <unordered_map>

#include "01-IEventDispatcher.h"
#include "02-boot/03-dto/02-TestDtoSerializer.h"
#include "02-boot/03-dto/04-RetDtoSerializer.h"


class EventDispatcher final : public IEventDispatcher {

    UnorderedMap<StdString, std::function<StdString(CStdString)>> getMappings;
    UnorderedMap<StdString, std::function<StdString(CStdString)>> postMappings;
    UnorderedMap<StdString, std::function<StdString(CStdString)>> putMappings;
    UnorderedMap<StdString, std::function<StdString(CStdString)>> patchMappings;
    UnorderedMap<StdString, std::function<StdString(CStdString)>> deleteMappings;

    Public EventDispatcher() {
        InitializeMappings();
    }

    Public StdString DispatchEvent(IEventPtr event) override {
        CStdString url = event->GetHttpUrl();
        CStdString payload = event->GetHttpPayload();
        switch (event->GetHttpMethod()) {
            case HttpMethod::Get:
                return getMappings[url](payload);
            case HttpMethod::Post:
                return postMappings[url](payload);
            case HttpMethod::Put:
                return putMappings[url](payload);
            case HttpMethod::Patch:
                return patchMappings[url](payload);
            case HttpMethod::Delete:
                return deleteMappings[url](payload);
        }
        return StdString();
    }

    Private Void InitializeMappings() {

    }

};

// Controller
/*
 * Class
 * Interface
 * BaseUrl
 * --
 * Loop in class now
 * Mapping Type (Get, Post, etc)
 * Method Url
 * Method Name
 * Method Return Type
 * Method Parameter Type
 * Method should have only 1 argument
 * Concatenate with base url
 * Sanitize Url
 * --
 * Put it into python memory
 * Interface Name,
 * Class Name,
 * Sanitized Url,
 * Http Method Type,
 * Method Name
 * Return Type
 * Param Type
 * --
 * In the dispatcher, in the initialize method,
 * go through all the memory map contents.
 * Check for HttpMethodType and select the map accordingly
 * Add details in this map.
 * e.g.
 * getMappings[sanitized_url] = [](CStdString payload) -> StdString {
    /* @Autowired */
    InterfaceNamePtr myInterface;
    ParamType inputDto = ParamType::Deserialize(payload);
    Val resultDto = myInterface->methodName(inputDto);
    return resultDto.Serialize();
* }
 *
 */
#endif // EVENT_DISPATCHER_H