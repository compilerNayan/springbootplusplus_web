#ifndef I_AUTHORIZATION_FILTER_FACTORY_H
#define I_AUTHORIZATION_FILTER_FACTORY_H

#include <StandardDefines.h>
#include <functional>
#include <tuple>
#include <type_traits>
#include <typeindex>
#include <utility>

#include "IAuthorizationFilter.h"

DefineStandardPointers(IAuthorizationFilterFactory)

/**
 * Polymorphic factory for IAuthorizationFilter instances (cached per std::type_index).
 *
 * Same pattern as IThreadPool: GetFilter<T>(...) is a non-virtual template on this interface that forwards
 * to the virtual GetFilterImpl; concrete classes implement GetFilterImpl only.
 */
class IAuthorizationFilterFactory {

    Protected IAuthorizationFilterFactory() = default;

    Public Virtual ~IAuthorizationFilterFactory() = default;

    IAuthorizationFilterFactory(const IAuthorizationFilterFactory&) = delete;
    IAuthorizationFilterFactory& operator=(const IAuthorizationFilterFactory&) = delete;

    /**
     * Returns the cached filter for filterType, or invokes createIfMissing once (under lock) to create
     * and cache it. createIfMissing must be copyable so it can be stored in std::function.
     */
    Public Virtual IAuthorizationFilterPtr GetFilterImpl(
        const std::type_index& filterType,
        std::function<IAuthorizationFilterPtr()> createIfMissing) = 0;

    /**
     * @tparam T Concrete filter type (must derive from IAuthorizationFilter)
     * @return Shared cached instance for T; first call constructs T with args, later calls ignore args
     */
    Public template<typename T, typename... Args>
    IAuthorizationFilterPtr GetFilter(Args&&... args) {
        static_assert(std::is_base_of<IAuthorizationFilter, T>::value,
                      "IAuthorizationFilterFactory::GetFilter<T>: T must derive from IAuthorizationFilter");
        auto tup = std::make_tuple(std::forward<Args>(args)...);
        return GetFilterImpl(std::type_index(typeid(T)), [tup]() mutable -> IAuthorizationFilterPtr {
            return std::apply(
                [](auto&&... a) -> IAuthorizationFilterPtr {
                    return make_ptr<T>(std::forward<decltype(a)>(a)...);
                },
                std::move(tup));
        });
    }
};

#endif // I_AUTHORIZATION_FILTER_FACTORY_H
