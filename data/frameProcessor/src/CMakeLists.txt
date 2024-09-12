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

# Add library for HexitecMhzDetectorPlugin
add_library(HexitecMhzDetectorPlugin SHARED
        HexitecMhzPlugin.cpp
)

target_compile_options(HexitecMhzDetectorPlugin PRIVATE ${LIBDPDK_CFLAGS})
target_link_directories(HexitecMhzDetectorPlugin PRIVATE ${ODINDATA_LIBRARY_DIR} ${LIBDPDK_LIBRARY_DIRS})
target_link_libraries(HexitecMhzDetectorPlugin
        PRIVATE OdinDataDpdk rte_eal rte_kvargs rte_telemetry
        ${LIBDPDK_LDFLAGS} ${BLOSC_LIBRARIES}
)

get_target_property(PLUGIN_INSTALL_RPATH HexitecMhzDetectorPlugin INSTALL_RPATH)


set_target_properties(HexitecMhzDetectorPlugin PROPERTIES
  INSTALL_RPATH "${PLUGIN_INSTALL_RPATH}:${LIBDPDK_LIBRARY_DIRS}"
)

# SET(CMAKE_INSTALL_RPATH "${INSTALL_RPATH}:${LIBDPDK_LIBRARY_DIRS}")

install(TARGETS HexitecMhzDetectorPlugin LIBRARY DESTINATION lib)
