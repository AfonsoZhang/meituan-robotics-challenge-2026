cmake_minimum_required(VERSION 3.8)
project(meituan_sim)
find_package(ament_cmake REQUIRED)
find_package(Python3 REQUIRED COMPONENTS Interpreter)
execute_process(
  COMMAND "${Python3_EXECUTABLE}" "${CMAKE_CURRENT_SOURCE_DIR}/scripts/gen_scene.py"
          --output-dir "${CMAKE_CURRENT_BINARY_DIR}/generated"
  RESULT_VARIABLE scene_result)
if(NOT scene_result EQUAL 0)
  message(FATAL_ERROR "Failed to generate demo scene")
endif()
install(DIRECTORY urdf config launch DESTINATION share/${PROJECT_NAME}/)
install(DIRECTORY "${CMAKE_CURRENT_BINARY_DIR}/generated/worlds"
                  "${CMAKE_CURRENT_BINARY_DIR}/generated/models"
        DESTINATION share/${PROJECT_NAME}/)
install(PROGRAMS scripts/gen_scene.py DESTINATION lib/${PROJECT_NAME})
ament_package()
