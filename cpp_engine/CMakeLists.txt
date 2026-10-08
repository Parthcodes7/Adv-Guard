cmake_minimum_required(VERSION 3.10)
project(AdvGuard)

set(CMAKE_CXX_STANDARD 17)

include_directories(include)

add_executable(advguard_engine 
    src/main.cpp 
    src/KDTree.cpp 
    src/MaxHeap.cpp 
    src/LSH.cpp 
    src/AdvGuardEngine.cpp
)
