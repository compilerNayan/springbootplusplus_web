cmake_minimum_required(VERSION 3.14)
project(springbootplusplus_web VERSION 1.0.0 LANGUAGES CXX)

# Set C++ standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Fetch dependencies FIRST, before pre-build script
# This ensures dependencies are available when the pre-build script runs
include(FetchContent)

# Fetch serializationlib
FetchContent_Declare(
    serializationlib
    GIT_REPOSITORY https://github.com/compilerNayan/serializationlib.git
    GIT_TAG        main
)

# Fetch serverlib
FetchContent_Declare(
    serverlib
    GIT_REPOSITORY https://github.com/compilerNayan/arduinolibserver.git
    GIT_TAG        main
)

# Fetch server-posix
FetchContent_Declare(
    server-posix
    GIT_REPOSITORY https://github.com/compilerNayan/arduinodesktopserver.git
    GIT_TAG        main
)

FetchContent_MakeAvailable(serializationlib serverlib server-posix)

# Run pre-build script during configuration (runs even if client creates own library)
# This will run whenever this CMakeLists.txt is processed
# Note: All dependencies are now available since FetchContent_MakeAvailable was called above
find_program(PYTHON_EXECUTABLE python3 python)
if(PYTHON_EXECUTABLE AND EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/springbootplusplus_web_scripts/springbootplusplus_web_pre_build.py")
    # Get the client project directory (CMAKE_SOURCE_DIR is the top-level project source directory)
    # When this library is included via FetchContent, CMAKE_SOURCE_DIR points to the client project
    set(CLIENT_PROJECT_DIR ${CMAKE_SOURCE_DIR})
    
    # Set environment variable for the script
    set(ENV{CMAKE_PROJECT_DIR} ${CLIENT_PROJECT_DIR})
    
    execute_process(
        COMMAND ${PYTHON_EXECUTABLE} 
            "${CMAKE_CURRENT_SOURCE_DIR}/springbootplusplus_web_scripts/springbootplusplus_web_pre_build.py"
        WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
        RESULT_VARIABLE PRE_BUILD_RESULT
        OUTPUT_VARIABLE PRE_BUILD_OUTPUT
        ERROR_VARIABLE PRE_BUILD_ERROR
        OUTPUT_STRIP_TRAILING_WHITESPACE
        ERROR_STRIP_TRAILING_WHITESPACE
    )
    if(PRE_BUILD_OUTPUT)
        message(STATUS "springbootplusplus_web pre-build output:\n${PRE_BUILD_OUTPUT}")
    endif()
    if(PRE_BUILD_ERROR)
        message(STATUS "springbootplusplus_web pre-build errors (expected in non-PlatformIO environment):\n${PRE_BUILD_ERROR}")
    endif()
    if(PRE_BUILD_RESULT AND NOT PRE_BUILD_RESULT EQUAL "0")
        message(STATUS "springbootplusplus_web pre-build script exited with code ${PRE_BUILD_RESULT} (this is expected in non-PlatformIO CMake builds)")
    endif()
endif()

# Create header-only library (INTERFACE library)
add_library(springbootplusplus_web INTERFACE)

# Set target properties
set_target_properties(springbootplusplus_web PROPERTIES
    VERSION ${PROJECT_VERSION}
)

# Set include directories
target_include_directories(springbootplusplus_web INTERFACE
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/src>
    $<INSTALL_INTERFACE:include>
)

# Link serializationlib (header-only library)
# Try the namespaced target first, fallback to non-namespaced
if(TARGET serializationlib::serializationlib)
    target_link_libraries(springbootplusplus_web INTERFACE serializationlib::serializationlib)
elseif(TARGET serializationlib)
    target_link_libraries(springbootplusplus_web INTERFACE serializationlib)
else()
    # Fallback: manually add include directory if target doesn't exist
    FetchContent_GetProperties(serializationlib)
    if(serializationlib_SOURCE_DIR)
        target_include_directories(springbootplusplus_web INTERFACE
            $<BUILD_INTERFACE:${serializationlib_SOURCE_DIR}/src>
            $<INSTALL_INTERFACE:include>
        )
    endif()
endif()

# Link serverlib (header-only library)
# Try the namespaced target first, fallback to non-namespaced
if(TARGET serverlib::serverlib)
    target_link_libraries(springbootplusplus_web INTERFACE serverlib::serverlib)
elseif(TARGET serverlib)
    target_link_libraries(springbootplusplus_web INTERFACE serverlib)
else()
    # Fallback: manually add include directory if target doesn't exist
    FetchContent_GetProperties(serverlib)
    if(serverlib_SOURCE_DIR)
        target_include_directories(springbootplusplus_web INTERFACE
            $<BUILD_INTERFACE:${serverlib_SOURCE_DIR}/include>
            $<INSTALL_INTERFACE:include>
        )
    endif()
endif()

# Link server-posix (header-only library)
# Note: CMake target name is server_posix (no hyphen allowed in target names)
# Try the namespaced target first, fallback to non-namespaced
if(TARGET server_posix::server_posix)
    target_link_libraries(springbootplusplus_web INTERFACE server_posix::server_posix)
elseif(TARGET server_posix)
    target_link_libraries(springbootplusplus_web INTERFACE server_posix)
else()
    # Fallback: manually add include directory if target doesn't exist
    FetchContent_GetProperties(server-posix)
    if(server-posix_SOURCE_DIR)
        target_include_directories(springbootplusplus_web INTERFACE
            $<BUILD_INTERFACE:${server-posix_SOURCE_DIR}/include>
            $<INSTALL_INTERFACE:include>
        )
    endif()
endif()

# Note: For INTERFACE libraries, we don't need to add header files to target_sources
# The include directories are sufficient for consumers to find the headers

# Add pre-build script execution
# Note: This script requires PlatformIO environment to run properly
find_program(PYTHON_EXECUTABLE python3 python REQUIRED)

# Create a custom target that runs the pre-build script
# Set the project directory environment variable for the script
if(CMAKE_SOURCE_DIR)
    set(CLIENT_PROJECT_DIR ${CMAKE_SOURCE_DIR})
else()
    # Fallback if CMAKE_SOURCE_DIR is not available
    get_filename_component(CLIENT_PROJECT_DIR "${CMAKE_CURRENT_LIST_DIR}/.." ABSOLUTE)
endif()

add_custom_target(springbootplusplus_web_pre_build
    COMMAND ${CMAKE_COMMAND} -E env "CMAKE_PROJECT_DIR=${CLIENT_PROJECT_DIR}"
        ${PYTHON_EXECUTABLE} 
        "${CMAKE_CURRENT_SOURCE_DIR}/springbootplusplus_web_scripts/springbootplusplus_web_pre_build.py"
    WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
    COMMENT "Running springbootplusplus_web pre-build script"
    VERBATIM
)

# Make the library depend on the pre-build step
add_dependencies(springbootplusplus_web springbootplusplus_web_pre_build)

# Optional: Set up installation
include(GNUInstallDirs)

install(TARGETS springbootplusplus_web
    EXPORT springbootplusplus_webTargets
)

install(FILES src/NayanMath2.h
    DESTINATION ${CMAKE_INSTALL_INCLUDEDIR}
)

install(EXPORT springbootplusplus_webTargets
    FILE springbootplusplus_webTargets.cmake
    NAMESPACE springbootplusplus_web::
    DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/springbootplusplus_web
)

# Optional: Create a config file for find_package support
if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/cmake/springbootplusplus_webConfig.cmake.in")
    include(CMakePackageConfigHelpers)

    configure_package_config_file(
        "${CMAKE_CURRENT_SOURCE_DIR}/cmake/springbootplusplus_webConfig.cmake.in"
        "${CMAKE_CURRENT_BINARY_DIR}/springbootplusplus_webConfig.cmake"
        INSTALL_DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/springbootplusplus_web
    )

    write_basic_package_version_file(
        "${CMAKE_CURRENT_BINARY_DIR}/springbootplusplus_webConfigVersion.cmake"
        VERSION ${PROJECT_VERSION}
        COMPATIBILITY AnyNewerVersion
    )

    install(FILES
        "${CMAKE_CURRENT_BINARY_DIR}/springbootplusplus_webConfig.cmake"
        "${CMAKE_CURRENT_BINARY_DIR}/springbootplusplus_webConfigVersion.cmake"
        DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/springbootplusplus_web
    )
endif()

