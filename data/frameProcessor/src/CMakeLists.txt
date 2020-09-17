
set(CMAKE_INCLUDE_CURRENT_DIR on)
ADD_DEFINITIONS(-DBOOST_TEST_DYN_LINK)

include_directories(${FRAMEPROCESSOR_DIR}/include ${ODINDATA_INCLUDE_DIRS}
	${Boost_INCLUDE_DIRS} ${LOG4CXX_INCLUDE_DIRS}/.. ${ZEROMQ_INCLUDE_DIRS})

# Add library for mercury plugin
add_library(MercuryTemplatePlugin SHARED MercuryTemplatePlugin.cpp)

install(TARGETS MercuryTemplatePlugin LIBRARY DESTINATION lib)
