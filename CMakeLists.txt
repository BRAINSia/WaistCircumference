cmake_minimum_required(VERSION 2.8.9)

project(WaistCircumference)

#-----------------------------------------------------------------------------
# Extension meta-information
set(EXTENSION_HOMEPAGE "http://www.example.com/Slicer/Extensions/WaistCircumference")
set(EXTENSION_CATEGORY "Examples")
set(EXTENSION_CONTRIBUTORS "Jessica Forbes (University of Iowa), Hans Johnson (University of Iowa)")
set(EXTENSION_DESCRIPTION "This module calculates the waist circumference from an abdominal CT scan.  The user scrolls through the scan to find a slice containing the belly button. The user then hovers over the edge of the waist perimeter to create an outline of the waist. When satisfied with the waist outilne, the user clicks and a labelmap is created containing a label.  The user selects Apply and the perimeter of the label shape is calculated and displayed.  Most commonly the spacing units of the image will be calculated in mm. The perimeter is will be calculated with the same unit as the image spacing.")
set(EXTENSION_ICONURL "http://www.example.com/Slicer/Extensions/WaistCircumference.png")
set(EXTENSION_SCREENSHOTURLS "http://www.example.com/Slicer/Extensions/WaistCircumference/Screenshots/1.png")

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
