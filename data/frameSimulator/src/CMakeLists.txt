
set(CMAKE_INCLUDE_CURRENT_DIR on)
ADD_DEFINITIONS(-DBOOST_TEST_DYN_LINK)

include_directories(${FRAMESIMULATOR_DIR}/include ${ODINDATA_INCLUDE_DIRS}
	${Boost_INCLUDE_DIRS} ${LOG4CXX_INCLUDE_DIRS}/.. ${ZEROMQ_INCLUDE_DIRS} ${PCAP_INCLUDE_DIR})

file(GLOB LIB_SOURCES MercuryFrameSimulatorPlugin.cpp MercuryFrame.cpp)

# Add library for Mercury plugin
add_library(MercuryFrameSimulatorPlugin SHARED ${LIB_SOURCES})

target_link_libraries(MercuryFrameSimulatorPlugin ${PCAP_LIBRARY})

install(TARGETS MercuryFrameSimulatorPlugin LIBRARY DESTINATION lib)
