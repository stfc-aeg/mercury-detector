set(CMAKE_INCLUDE_CURRENT_DIR on)
ADD_DEFINITIONS(-DBOOST_TEST_DYN_LINK)

include_directories(
        ${FRAMEPROCESSOR_DIR}/include
        ${ODINDATA_INCLUDE_DIRS}
        ${ODINDATA_INCLUDE_DIR}/dpdk
        ${Boost_INCLUDE_DIRS}
        ${LOG4CXX_INCLUDE_DIRS}/..
        ${ZEROMQ_INCLUDE_DIRS}
        ${BLOSC_INCLUDE_DIR}
)

# Add library for BabydDetectorPlugin
add_library(BabydDetectorPlugin SHARED
        HexitecMhzPlugin.cpp
)

target_compile_options(BabydDetectorPlugin PRIVATE ${LIBDPDK_CFLAGS})
target_link_directories(BabydDetectorPlugin PRIVATE ${ODINDATA_LIBRARY_DIR} ${LIBDPDK_LIBRARY_DIRS})
target_link_libraries(BabydDetectorPlugin
        PRIVATE OdinDataDpdk rte_eal rte_kvargs rte_telemetry
        ${LIBDPDK_LDFLAGS} ${BLOSC_LIBRARIES}
)

get_target_property(PLUGIN_INSTALL_RPATH BabydDetectorPlugin INSTALL_RPATH)


set_target_properties(BabydDetectorPlugin PROPERTIES
  INSTALL_RPATH "${PLUGIN_INSTALL_RPATH}:${LIBDPDK_LIBRARY_DIRS}"
)

# SET(CMAKE_INSTALL_RPATH "${INSTALL_RPATH}:${LIBDPDK_LIBRARY_DIRS}")

install(TARGETS BabydDetectorPlugin LIBRARY DESTINATION lib)
