cmake_minimum_required(VERSION 2.8.9)

project(WaistCircumference)

#-----------------------------------------------------------------------------
# Extension meta-information
set(EXTENSION_HOMEPAGE "https://github.com/BRAINSia/WaistCircumference")
set(EXTENSION_CATEGORY "Segmentation")
set(EXTENSION_CONTRIBUTORS "Jessica Forbes (University of Iowa), Hans Johnson (University of Iowa)")
set(EXTENSION_DESCRIPTION "This module provides a quick semi-automated method to calculate and save the waist circumference from multiple abdominal images.")
set(EXTENSION_ICONURL "https://github.com/BRAINSia/WaistCircumference/blob/master/WaistCircumference/Resources/Icons/WaistCircumference.png")
set(EXTENSION_SCREENSHOTURLS "https://github.com/BRAINSia/WaistCircumference/blob/master/WC_module.png https://github.com/BRAINSia/WaistCircumference/blob/master/WC_multiple_measures.png https://github.com/BRAINSia/WaistCircumference/blob/master/WC_level_tracing_effect_Editor.png https://github.com/BRAINSia/WaistCircumference/blob/master/WC_axial_slice_to_measure.png https://github.com/BRAINSia/WaistCircumference/blob/master/WC_example_input_imageList.png https://github.com/BRAINSia/WaistCircumference/blob/master/WC_example_results.png")

#-----------------------------------------------------------------------------
# Extension dependencies
find_package(Slicer REQUIRED)
include(${Slicer_USE_FILE})

#-----------------------------------------------------------------------------
# Extension modules
add_subdirectory(WaistCircumference)
## NEXT_MODULE

#-----------------------------------------------------------------------------
include(${Slicer_EXTENSION_CPACK})
