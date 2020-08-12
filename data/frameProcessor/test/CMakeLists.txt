
set(CMAKE_INCLUDE_CURRENT_DIR on)
ADD_DEFINITIONS(-DBOOST_TEST_DYN_LINK)
ADD_DEFINITIONS(-DBUILD_DIR="${CMAKE_BINARY_DIR}")

include_directories(${FRAMEPROCESSOR_DIR}/include ${ODINDATA_INCLUDE_DIRS} 
	${Boost_INCLUDE_DIRS} ${LOG4CXX_INCLUDE_DIRS}/.. ${ZEROMQ_INCLUDE_DIRS})

# Build list of test source files from current dir
file(GLOB TEST_SOURCES *.cpp)

# Add test and project source files to executable


# Define libraries to link against
