
set(CMAKE_INCLUDE_CURRENT_DIR on)
ADD_DEFINITIONS(-DBOOST_TEST_DYN_LINK)

include_directories(${FRAMEPROCESSOR_DIR}/include ${ODINDATA_INCLUDE_DIRS}
	${Boost_INCLUDE_DIRS} ${LOG4CXX_INCLUDE_DIRS}/.. ${ZEROMQ_INCLUDE_DIRS})

# Add library for each mercury plugin
add_library(MercuryTemplatePlugin SHARED MercuryTemplatePlugin.cpp)
add_library(MercuryReorderPlugin SHARED MercuryReorderPlugin.cpp)
add_library(MercuryAdditionPlugin SHARED MercuryAdditionPlugin.cpp)
add_library(MercuryCalibrationPlugin SHARED MercuryCalibrationPlugin.cpp)
add_library(MercuryDiscriminationPlugin SHARED MercuryDiscriminationPlugin.cpp)
add_library(MercuryHistogramPlugin SHARED MercuryHistogramPlugin.cpp)
add_library(MercuryNextFramePlugin SHARED MercuryNextFramePlugin.cpp)
add_library(MercuryThresholdPlugin SHARED MercuryThresholdPlugin.cpp)

install(TARGETS MercuryTemplatePlugin LIBRARY DESTINATION lib)
install(TARGETS MercuryReorderPlugin LIBRARY DESTINATION lib)
install(TARGETS MercuryAdditionPlugin LIBRARY DESTINATION lib)
install(TARGETS MercuryCalibrationPlugin LIBRARY DESTINATION lib)
install(TARGETS MercuryDiscriminationPlugin LIBRARY DESTINATION lib)
install(TARGETS MercuryHistogramPlugin LIBRARY DESTINATION lib)
install(TARGETS MercuryNextFramePlugin LIBRARY DESTINATION lib)
install(TARGETS MercuryThresholdPlugin LIBRARY DESTINATION lib)
