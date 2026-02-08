#ifndef DISPATCHER_H
#define DISPATCHER_H

#include "01-framework/06-event/01-input/01-interface/01-IEvent.h"
#include "type/DIDef.h"

DEFINE_STANDARD_POINTERS(IEventDispatcher)
class IEventDispatcher {

    Public Virtual ~IEventDispatcher() = default;

    Public Virtual StdString DispatchEvent(IEventPtr event) = 0;

};

#endif // DISPATCHER_H