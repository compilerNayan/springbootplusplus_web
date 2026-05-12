#ifndef AUTHORIZATION_FILTER_FACTORY_H
#define AUTHORIZATION_FILTER_FACTORY_H

#include <StandardDefines.h>
#include <mutex>
#include <typeindex>

#include "IAuthorizationFilterFactory.h"

/**
 * Thread-safe cache of authorization filters keyed by concrete type (std::type_index).
 *
 * Use IAuthorizationFilterFactory::GetFilter<T>(...) from a pointer to this interface or concrete type.
 */
/* @Component */
class AuthorizationFilterFactory : public IAuthorizationFilterFactory {

    Private StdUnorderedMap<std::type_index, IAuthorizationFilterPtr> instances;
    Private std::mutex instancesMutex;

    Public AuthorizationFilterFactory() = default;

    Public ~AuthorizationFilterFactory() override = default;

    AuthorizationFilterFactory(const AuthorizationFilterFactory&) = delete;
    AuthorizationFilterFactory& operator=(const AuthorizationFilterFactory&) = delete;

    Public IAuthorizationFilterPtr GetFilterImpl(
        const std::type_index& filterType,
        std::function<IAuthorizationFilterPtr()> createIfMissing) override {
        std::lock_guard<std::mutex> lock(instancesMutex);
        Val existing = instances.find(filterType);
        if (existing != instances.end()) {
            return existing->second;
        }
        IAuthorizationFilterPtr created = createIfMissing();
        instances[filterType] = created;
        return created;
    }
};

#endif // AUTHORIZATION_FILTER_FACTORY_H
