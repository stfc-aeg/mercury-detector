
set(CMAKE_INCLUDE_CURRENT_DIR on)
ADD_DEFINITIONS(-DBOOST_TEST_DYN_LINK)

include_directories(${FRAMEPROCESSOR_DIR}/include ${ODINDATA_INCLUDE_DIRS}
	${Boost_INCLUDE_DIRS} ${LOG4CXX_INCLUDE_DIRS}/.. ${ZEROMQ_INCLUDE_DIRS})

# Add library for each mercury plugin
add_library(MercuryTemplatePlugin SHARED MercuryTemplatePlugin.cpp)
add_library(MercuryProcessorPlugin SHARED MercuryProcessorPlugin.cpp)
add_library(MercuryReorderPlugin SHARED MercuryReorderPlugin.cpp)
add_library(MercuryAdditionPlugin SHARED MercuryAdditionPlugin.cpp)
add_library(MercuryCalibrationPlugin SHARED MercuryCalibrationPlugin.cpp)

install(TARGETS MercuryTemplatePlugin LIBRARY DESTINATION lib)
install(TARGETS MercuryProcessorPlugin LIBRARY DESTINATION lib)
install(TARGETS MercuryReorderPlugin LIBRARY DESTINATION lib)
install(TARGETS MercuryAdditionPlugin LIBRARY DESTINATION lib)
install(TARGETS MercuryCalibrationPlugin LIBRARY DESTINATION lib)
