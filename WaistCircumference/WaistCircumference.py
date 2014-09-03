import os
import unittest
from __main__ import vtk, qt, ctk, slicer
import Editor
import EditorLib
import SimpleITK as sitk
import sitkUtils as su
import csv

#
# WaistCircumference
#

class WaistCircumference:
  def __init__(self, parent):
    parent.title = "WaistCircumference"
    parent.categories = ["Testing.TestCases"]
    parent.dependencies = []
    parent.contributors = ["Jessica Forbes (University of Iowa)"]
    parent.helpText = """This module provides the user with a quick semi-automated
    method to calculate the waist circumference. The user selects a file to contain
    the results. If the files does not exist, the module creates a new csv file with
    an appropriate header row. This file with contain the circumference results which
    are appended when the user selects the "Save and Next" button. The user also
    selects a file containing a list of absolute paths to the scan locations. The
    file should be formatted so that each row contains only one file path. No commas
    or quotations are required. Once this file is selected, the first scan will
    automatically open. Then the user can select Editor tools to create a label map
    of the waist. The user can scroll through the image slices using the middle mouse
    button. Then select the "Apply" button to calculate the waist circumference of the
    selected labels in all slices. The user should select "Save and Next" when satisfied
    with label selections. This will save the data in the display table to the output
    results file, save the mrml scene to a folder named from the master volume's name,
    and then open the next scan in the input "Image List" file.
    Useful shortcut keys include: 'l' - selects the Editor Level Tracing
    Effect, 'a' - selects the "Apply" button, 's' - selects the "Save and Next" button,
    'o' - toggles on/off the outline of labels.
    """
    parent.acknowledgementText = """
    This file was originally developed by Jessica Forbes of the SINAPSE Lab
     at the University of Iowa."""
    # replace with organization, grant and thanks.
    self.parent = parent

    # Add this test to the SelfTest module's list for discovery when the module
    # is created.  Since this module may be discovered before SelfTests itself,
    # create the list if it doesn't already exist.
    try:
      slicer.selfTests
    except AttributeError:
      slicer.selfTests = {}
    slicer.selfTests['WaistCircumference'] = self.runTest

  def runTest(self):
    tester = WaistCircumferenceTest()
    tester.runTest()

#
# WaistCircumferenceWidget
#

class WaistCircumferenceWidget:
  def __init__(self, parent = None):
    if not parent:
      self.parent = slicer.qMRMLWidget()
      self.parent.setLayout(qt.QVBoxLayout())
      self.parent.setMRMLScene(slicer.mrmlScene)
    else:
      self.parent = parent
    self.layout = self.parent.layout()
    self.imageFileListDialog = None
    self.resultsFileDialog = None
    self.imageFileListPath = '/scratch/WaistCircumference/volumesList.csv'
    self.logic = WaistCircumferenceLogic()
    if not parent:
      self.setup()
      self.parent.show()

  def setup(self):
    # Instantiate and connect widgets ...

    #
    # Reload and Test area
    #
    reloadCollapsibleButton = ctk.ctkCollapsibleButton()
    reloadCollapsibleButton.text = "Reload && Test"
    self.layout.addWidget(reloadCollapsibleButton)
    reloadFormLayout = qt.QFormLayout(reloadCollapsibleButton)

    # reload button
    # (use this during development, but remove it when delivering
    #  your module to users)
    self.reloadButton = qt.QPushButton("Reload")
    self.reloadButton.toolTip = "Reload this module."
    self.reloadButton.name = "WaistCircumference Reload"
    reloadFormLayout.addWidget(self.reloadButton)
    self.reloadButton.connect('clicked()', self.onReload)

    # reload and test button
    # (use this during development, but remove it when delivering
    #  your module to users)
    self.reloadAndTestButton = qt.QPushButton("Reload and Test")
    self.reloadAndTestButton.toolTip = "Reload this module and then run the self tests."
    reloadFormLayout.addWidget(self.reloadAndTestButton)
    self.reloadAndTestButton.connect('clicked()', self.onReloadAndTest)

    #
    # Parameters Area
    #
    parametersCollapsibleButton = ctk.ctkCollapsibleButton()
    parametersCollapsibleButton.text = "Parameters"
    self.layout.addWidget(parametersCollapsibleButton)

    # Layout within the dummy collapsible button
    parametersFormLayout = qt.QFormLayout(parametersCollapsibleButton)

    #
    # check box to trigger taking screen shots for later use in tutorials
    #
    self.enableScreenshotsFlagCheckBox = qt.QCheckBox()
    self.enableScreenshotsFlagCheckBox.checked = 0
    self.enableScreenshotsFlagCheckBox.setToolTip("If checked, take screen shots for tutorials. Use Save Data to write them to disk.")
    parametersFormLayout.addRow("Enable Screenshots", self.enableScreenshotsFlagCheckBox)

    #
    # scale factor for screen shots
    #
    self.screenshotScaleFactorSliderWidget = ctk.ctkSliderWidget()
    self.screenshotScaleFactorSliderWidget.singleStep = 1.0
    self.screenshotScaleFactorSliderWidget.minimum = 1.0
    self.screenshotScaleFactorSliderWidget.maximum = 50.0
    self.screenshotScaleFactorSliderWidget.value = 1.0
    self.screenshotScaleFactorSliderWidget.setToolTip("Set scale factor for the screen shots.")
    parametersFormLayout.addRow("Screenshot scale factor", self.screenshotScaleFactorSliderWidget)

    #
    # Select results file button
    #
    self.selectResultsFileButton = qt.QPushButton("Select Results File")
    self.selectResultsFileButton.toolTip = "Select a csv file for output"
    parametersFormLayout.addRow(self.selectResultsFileButton)

    #
    # Select Image List Button
    #
    self.selectImageListButton = qt.QPushButton("Select Image List")
    self.selectImageListButton.toolTip = "Select an image list in the form of absolute paths"
    parametersFormLayout.addRow(self.selectImageListButton)

    #
    # Creates and adds the custom Editor Widget to the module
    #
    self.localEditorWidget = Editor.EditorWidget(parent=self.parent, showVolumesFrame=True)
    self.localEditorWidget.setup()
    self.localEditorWidget.enter()
    self.installShortcutKeys()
    self.setHelper()

    #
    # Measurements Area
    #
    measurementsCollapsibleButton = ctk.ctkCollapsibleButton()
    measurementsCollapsibleButton.text = "Measurements"
    self.layout.addWidget(measurementsCollapsibleButton)

    # Layout within the Measurements collapsible button
    measurementsFormLayout = qt.QFormLayout(measurementsCollapsibleButton)

    #
    # Apply Button
    #
    self.applyButton = qt.QPushButton("Apply")
    self.applyButton.toolTip = "Run the algorithm."
    self.applyButton.enabled = False
    measurementsFormLayout.addRow(self.applyButton)

    # model and view for stats table
    self.view = qt.QTableView()
    self.view.sortingEnabled = True
    measurementsFormLayout.addWidget(self.view)

    #
    # Save Button
    #
    self.saveButton = qt.QPushButton("Save and Next")
    self.saveButton.toolTip = "Save statistics to csv and save mrml scene."
    self.saveButton.enabled = False
    measurementsFormLayout.addRow(self.saveButton)

    # connections
    self.selectImageListButton.connect('clicked(bool)', self.onSelectImageList)
    self.selectResultsFileButton.connect('clicked(bool)', self.onSelectResultsFile)
    self.applyButton.connect('clicked(bool)', self.onApplyButton)
    self.saveButton.connect('clicked(bool)', self.onSave)
    self.helper.masterSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)

    # Add vertical spacer
    self.layout.addStretch(1)

  def cleanup(self):
    self.localEditorWidget.exit()
    self.removeShortcutKeys()

    # clears the mrml scene
    slicer.mrmlScene.Clear(0)

  def onSelect(self):
    self.applyButton.enabled = self.helper.masterSelector.currentNode()

  def onApplyButton(self):
    self.localEditorWidget.toolsBox.selectEffect("DefaultTool")
    enableScreenshotsFlag = self.enableScreenshotsFlagCheckBox.checked
    screenshotScaleFactor = int(self.screenshotScaleFactorSliderWidget.value)
    print("Run the algorithm")
    self.logic.run(self.helper.master, self.helper.merge,
                   enableScreenshotsFlag, screenshotScaleFactor)
    self.populateStats()
    self.saveButton.enabled = True

  def populateStats(self):
    if not self.logic:
      return
    displayNode = self.helper.merge.GetDisplayNode()
    colorNode = displayNode.GetColorNode()
    lut = colorNode.GetLookupTable()
    self.items = []
    self.model = qt.QStandardItemModel()
    self.view.setModel(self.model)
    self.view.verticalHeader().visible = False
    row = 0
    for (slice, i) in self.logic.labelStats["Labels"]:
      color = qt.QColor()
      rgb = lut.GetTableValue(i)
      color.setRgb(rgb[0]*255,rgb[1]*255,rgb[2]*255)
      item = qt.QStandardItem()
      item.setData(color,qt.Qt.DecorationRole)
      item.setToolTip(colorNode.GetColorName(i))
      self.model.setItem(row,0,item)
      self.items.append(item)
      col = 1
      for k in self.logic.keys:
        item = qt.QStandardItem()
        if k == "Image Name":
          item.setData(self.logic.labelStats[slice,i,k],qt.Qt.DisplayRole)
        else:
          # set data as float with Qt::DisplayRole
          item.setData(float(self.logic.labelStats[slice,i,k]),qt.Qt.DisplayRole)
        item.setToolTip(colorNode.GetColorName(i))
        self.model.setItem(row,col,item)
        self.items.append(item)
        col += 1
      row += 1

    self.view.setColumnWidth(0,30)
    self.model.setHeaderData(0,1," ")
    col = 1
    for k in self.logic.keys:
      self.view.setColumnWidth(col,10*len(k))
      self.model.setHeaderData(col,1,k)
      col += 1

  def setHelper(self):
    self.helper = self.localEditorWidget.helper
    self.logic.helper = self.localEditorWidget.helper

  def onSelectImageList(self):
    """load the file containing a list absolute paths to images
    """
    if not self.imageFileListDialog:
      self.imageFileListDialog = qt.QFileDialog(self.parent)
      self.imageFileListDialog.options = self.imageFileListDialog.DontUseNativeDialog
      self.imageFileListDialog.acceptMode = self.imageFileListDialog.AcceptOpen
      self.imageFileListDialog.defaultSuffix = "csv"
      self.imageFileListDialog.setNameFilter("Comma Separated Values (*.csv)")
      self.imageFileListDialog.connect("fileSelected(QString)", self.onImageListFileSelected)
    self.imageFileListDialog.show()

  def onImageListFileSelected(self, fileName):
    self.imageFileListPath = fileName
    self.logic.readImageFileList(fileName)
    self.logic.startFirstImage()

  def onSelectResultsFile(self):
    """load the file containing a list absolute paths to images
    """
    if not self.resultsFileDialog:
      self.resultsFileDialog = qt.QFileDialog(self.parent)
      self.resultsFileDialog.options = self.resultsFileDialog.DontUseNativeDialog
      self.resultsFileDialog.acceptMode = self.resultsFileDialog.AcceptOpen
      self.resultsFileDialog.defaultSuffix = "csv"
      self.resultsFileDialog.setNameFilter("Comma Separated Values (*.csv)")
      self.resultsFileDialog.connect("fileSelected(QString)", self.onResultsFileSelected)
    self.resultsFileDialog.show()

  def onResultsFileSelected(self, fileName):
    self.resultsFilePath = fileName
    if os.path.exists(self.resultsFilePath):
      self.logic.readResultCSV(self.resultsFilePath)
    else:
      self.logic.createNewResultCSV(self.resultsFilePath)

  def onSave(self):
    """save the label statistics
    """
    self.onApplyButton() #selects Apply in case it is accidentally not pressed
    self.logic.takeScreenshot('Slice-label','slice',slicer.qMRMLScreenShotDialog().Red)
    baseDir = os.path.dirname(self.resultsFilePath)
    folderName = self.helper.master.GetName()
    dirName = os.path.join(baseDir, folderName)
    if not os.path.exists(dirName):
      os.mkdir(dirName)
    l = slicer.app.applicationLogic()
    l.SaveSceneToSlicerDataBundleDirectory(dirName, None)

    # saves the csv files to selected folder
    csvFileName = os.path.join(dirName, "{0}_waist_circumference.csv".format(folderName))
    self.logic.saveStats(csvFileName)
    self.logic.appendStats(self.resultsFilePath)
    self.resetTableModel()
    self.logic.startNextImage()

  def resetTableModel(self):
    self.model = None

  def installShortcutKeys(self):
    """Turn on module-wide shortcuts.  These are active independent
    of the currently selected effect."""
    self.shortcuts = []
    keysAndCallbacks = (
        ('l', lambda : self.localEditorWidget.toolsBox.selectEffect('LevelTracingEffect')),
        ('a', lambda : self.onApplyButton()),
        ('s', lambda : self.onSave()),
        )
    for key,callback in keysAndCallbacks:
      shortcut = qt.QShortcut(slicer.util.mainWindow())
      shortcut.setKey( qt.QKeySequence(key) )
      shortcut.connect( 'activated()', callback )
      self.shortcuts.append(shortcut)

  def removeShortcutKeys(self):
    for shortcut in self.shortcuts:
      shortcut.disconnect('activated()')
      shortcut.setParent(None)
    self.shortcuts = []

  def onReload(self,moduleName="WaistCircumference"):
    """Generic reload method for any scripted module.
    ModuleWizard will subsitute correct default moduleName.
    """
    self.cleanup()
    globals()[moduleName] = slicer.util.reloadScriptedModule(moduleName)

  def onReloadAndTest(self,moduleName="WaistCircumference"):
    try:
      self.onReload()
      evalString = 'globals()["%s"].%sTest()' % (moduleName, moduleName)
      tester = eval(evalString)
      tester.runTest()
    except Exception, e:
      import traceback
      traceback.print_exc()
      qt.QMessageBox.warning(slicer.util.mainWindow(),
          "Reload and Test", 'Exception!\n\n' + str(e) + "\n\nSee Python Console for Stack Trace")


#
# WaistCircumferenceLogic
#

class WaistCircumferenceLogic:
  """This class should implement all the actual
  computation done by your module.  The interface
  should be such that other python code can import
  this class and make use of the functionality without
  requiring an instance of the Widget
  """
  def __init__(self):
    self.keys = ("Index", "Image Name", "Slice", "Circumference (mm)", "Circumference (in)")
    self.labelStats = {}
    self.labelStats['Labels'] = []
    self.helper = None
    self.imageFileList = []
    self.imageFileListCounter = 0

  def hasImageData(self,volumeNode):
    """This is a dummy logic method that
    returns true if the passed in volume
    node has valid image data
    """
    if not volumeNode:
      print('no volume node')
      return False
    if volumeNode.GetImageData() == None:
      print('no image data')
      return False
    return True

  def delayDisplay(self,message,msec=1000):
    #
    # logic version of delay display
    #
    print(message)
    self.info = qt.QDialog()
    self.infoLayout = qt.QVBoxLayout()
    self.info.setLayout(self.infoLayout)
    self.label = qt.QLabel(message,self.info)
    self.infoLayout.addWidget(self.label)
    qt.QTimer.singleShot(msec, self.info.close)
    self.info.exec_()

  def takeScreenshot(self,name,description,type=-1):
    # show the message even if not taking a screen shot
    self.delayDisplay(description)

    if self.enableScreenshots == 0:
      return

    lm = slicer.app.layoutManager()
    # switch on the type to get the requested window
    widget = 0
    if type == -1:
      # full window
      widget = slicer.util.mainWindow()
    elif type == slicer.qMRMLScreenShotDialog().FullLayout:
      # full layout
      widget = lm.viewport()
    elif type == slicer.qMRMLScreenShotDialog().ThreeD:
      # just the 3D window
      widget = lm.threeDWidget(0).threeDView()
    elif type == slicer.qMRMLScreenShotDialog().Red:
      # red slice window
      widget = lm.sliceWidget("Red")
    elif type == slicer.qMRMLScreenShotDialog().Yellow:
      # yellow slice window
      widget = lm.sliceWidget("Yellow")
    elif type == slicer.qMRMLScreenShotDialog().Green:
      # green slice window
      widget = lm.sliceWidget("Green")

    # grab and convert to vtk image data
    qpixMap = qt.QPixmap().grabWidget(widget)
    qimage = qpixMap.toImage()
    imageData = vtk.vtkImageData()
    slicer.qMRMLUtils().qImageToVtkImageData(qimage,imageData)

    annotationLogic = slicer.modules.annotations.logic()
    annotationLogic.CreateSnapShot(name, description, type, self.screenshotScaleFactor, imageData)

  def rasToXY(self, rasPoint, sliceLogic):
    sliceNode = sliceLogic.GetSliceNode()
    rasToXY = vtk.vtkMatrix4x4()
    rasToXY.DeepCopy(sliceNode.GetXYToRAS())
    rasToXY.Invert()
    xyzw = rasToXY.MultiplyPoint(rasPoint + (1,))
    return (int(round(xyzw[0])), int(round(xyzw[1])))

  def xyToIJK(self, xy, sliceLogic):
    labelLogic = sliceLogic.GetLabelLayer()
    XYToIJK = labelLogic.GetXYToIJKTransform()
    ijk = XYToIJK.TransformDoublePoint(xy + (0,))
    ijk = map(lambda v: int(round(v)), ijk)
    return ijk

  def getRASFromSliceOffset(self, sliceLogic):
    labelLogic = sliceLogic.GetLabelLayer()
    labelNode = labelLogic.GetSliceNode()
    sliceOffset = labelNode.GetSliceOffset()
    ras = (0, 0, sliceOffset)
    return ras

  def getCurrentSlice(self):
    lm = slicer.app.layoutManager()
    sliceWidget = lm.sliceWidget('Red')
    sliceLogic = sliceWidget.sliceLogic()

    ras = self.getRASFromSliceOffset(sliceLogic)
    xy = self.rasToXY(ras, sliceLogic)
    ijk = self.xyToIJK(xy, sliceLogic)

    currentSlice = ijk[2]
    return currentSlice

  def calculateCircumference(self, merge):
    self.labelStats = {}
    self.labelStats['Labels'] = []
    label3D = su.PullFromSlicer(merge.GetName())
    # currentSlice = self.getCurrentSlice()
    indexRange = range(0, label3D.GetSize()[2])
    for sliceIndex in indexRange:
      img2D = label3D[:, :, sliceIndex]
      filter2D = sitk.LabelShapeStatisticsImageFilter()
      filter2D.Execute(img2D)
      labels = filter2D.GetLabels()
      if len(labels) == 0:
        continue
      for labelValue in labels:
        self.labelStats["Labels"].append((sliceIndex, int(labelValue)))
        self.labelStats[sliceIndex, int(labelValue), "Index"] = int(labelValue)
        self.labelStats[sliceIndex, int(labelValue), "Image Name"] = self.helper.master.GetName()
        self.labelStats[sliceIndex, int(labelValue), "Slice"] = sliceIndex
        self.labelStats[sliceIndex, int(labelValue), "Circumference (mm)"] = filter2D.GetPerimeter(labelValue)
        self.labelStats[sliceIndex, int(labelValue), "Circumference (in)"] = self.mmToInch(filter2D.GetPerimeter(labelValue))
        print self.labelStats

  def mmToInch(self, val):
    return val * 0.03937

  def readImageFileList(self, fileName):
    if os.path.exists(fileName):
      self.imageFileList = list()
      with open(fileName, 'rU') as imageList:
        for row in imageList:
          self.imageFileList.append(row.rstrip())
      print self.imageFileList

  def startFirstImage(self):
    self.imageFileListCounter = 0
    self.importAndCreateVolumes()

  def startNextImage(self):
    slicer.mrmlScene.Clear(0)
    self.imageFileListCounter += 1
    self.importAndCreateVolumes()

  def checkCounter(self):
    return self.imageFileListCounter < len(self.imageFileList)

  def importAndCreateVolumes(self):
    if self.checkCounter():
      path = self.imageFileList[self.imageFileListCounter]
      if os.path.exists(path):
        self.loadImage(path)
        pattern = self.getNodePatternFromPath(path)
        masterVolumeNode = slicer.util.getNode(pattern=pattern)
        self.helper.master = masterVolumeNode
        self.createMerge()
        mergeVolumeNode = slicer.util.getNode(pattern="{0}-label".format(pattern))
        self.helper.setVolumes(masterVolumeNode, mergeVolumeNode)
    else:
      qt.QMessageBox.warning(slicer.util.mainWindow(),
          "End of image list", "You have reached the end of the image "
                               "list!\n\nYou can now close Slicer")

  def getNodePatternFromPath(self, path):
    _, fileName = os.path.split(path)
    pattern, _ = fileName.split('.')
    return pattern

  def loadImage(self, path):
    if os.path.exists(path):
      slicer.util.loadVolume(path)

  def createMerge(self):
    try:
      self.helper.createMerge() # an error will be thrown:
      # AttributeError: 'HelperBox' object has no attribute 'colorSelector'
      # but it will still still create the merge image
    except Exception, e:
      import traceback
      traceback.print_exc()
      # qt.QMessageBox.warning(slicer.util.mainWindow(),
      #     "Create merge throwing error", 'Exception!\n\n' + str(e) + "\n\nSee Python Console for Stack Trace")

  def createNewResultCSV(self, fileName):
    with open(fileName, 'wb') as csvfile:
      resultsWriter = csv.writer(csvfile, delimiter=',',
                                 quotechar='"', quoting=csv.QUOTE_ALL)
      resultsWriter.writerow(self.keys)

  def readResultCSV(self, fileName):
    self.resultsDict = dict()
    with open(fileName, 'rU') as csvfile:
      resultsReader = csv.reader(csvfile, delimiter=',', quotechar='"')
      for row in resultsReader:
        imageID = row[1]
        if imageID != "Image Name": #skips header row
          self.resultsDict[imageID] = row[2:]
    print self.resultsDict

  def statsAsCSV(self):
    """
    print comma separated value file with header keys in quotes
    """
    csv = ""
    header = ""
    for k in self.keys[:-1]:
      header += "\"%s\"" % k + ","
    header += "\"%s\"" % self.keys[-1] + "\n"
    csv = header
    for (slice, i) in self.labelStats["Labels"]:
      line = ""
      for k in self.keys[:-1]:
        line += str(self.labelStats[slice, i, k]) + ","
      line += str(self.labelStats[slice, i, self.keys[-1]]) + "\n"
      csv += line
    return csv

  def saveStats(self,fileName):
    fp = open(fileName, "w")
    fp.write(self.statsAsCSV())
    fp.close()

  def appendStats(self, fileName):
    with open(fileName, 'a') as csvfile:
      resultsWriter = csv.writer(csvfile, delimiter=',',
                                 quotechar='"', quoting=csv.QUOTE_ALL)
      for (slice, i) in self.labelStats["Labels"]:
        row = list()
        for k in self.keys:
          row.append(self.labelStats[slice, int(i), k])
        resultsWriter.writerow(row)

  def run(self, master, merge, enableScreenshots=0, screenshotScaleFactor=1):
    """
    Run the actual algorithm
    """

    self.delayDisplay('Running the aglorithm')

    self.enableScreenshots = enableScreenshots
    self.screenshotScaleFactor = screenshotScaleFactor

    self.calculateCircumference(merge)

    return True

class WaistCircumferenceTest(unittest.TestCase):
  """
  This is the test case for your scripted module.
  """

  def delayDisplay(self,message,msec=1000):
    """This utility method displays a small dialog and waits.
    This does two things: 1) it lets the event loop catch up
    to the state of the test so that rendering and widget updates
    have all taken place before the test continues and 2) it
    shows the user/developer/tester the state of the test
    so that we'll know when it breaks.
    """
    print(message)
    self.info = qt.QDialog()
    self.infoLayout = qt.QVBoxLayout()
    self.info.setLayout(self.infoLayout)
    self.label = qt.QLabel(message,self.info)
    self.infoLayout.addWidget(self.label)
    qt.QTimer.singleShot(msec, self.info.close)
    self.info.exec_()

  def setUp(self):
    """ Do whatever is needed to reset the state - typically a scene clear will be enough.
    """
    slicer.mrmlScene.Clear(0)

  def runTest(self):
    """Run as few or as many tests as needed here.
    """
    self.setUp()
    self.test_WaistCircumference1()
    self.test_WaistCircumference2()
    self.test_WaistCircumference3()

  def test_WaistCircumference1(self):
    """ Ideally you should have several levels of tests.  At the lowest level
    tests sould exercise the functionality of the logic with different inputs
    (both valid and invalid).  At higher levels your tests should emulate the
    way the user would interact with your code and confirm that it still works
    the way you intended.
    One of the most important features of the tests is that it should alert other
    developers when their changes will have an impact on the behavior of your
    module.  For example, if a developer removes a feature that you depend on,
    your test should break so they know that the feature is needed.
    """

    self.delayDisplay("Starting Test 1")
    #
    # first, get some data
    #
    import urllib
    # downloads = (
    #     ('http://slicer.kitware.com/midas3/download?items=5767', 'FA.nrrd', slicer.util.loadVolume),
    #     )
    #
    # for url,name,loader in downloads:
    #   filePath = slicer.app.temporaryPath + '/' + name
    #   if not os.path.exists(filePath) or os.stat(filePath).st_size == 0:
    #     print('Requesting download %s from %s...\n' % (name, url))
    #     urllib.urlretrieve(url, filePath)
    #   if loader:
    #     print('Loading %s...\n' % (name,))
    #     loader(filePath)
    # self.delayDisplay('Finished with download and loading\n')

    try:
      path = "/scratch/WaistCircumference/2AbdPelvis5.nrrd"
      widget = slicer.modules.WaistCircumferenceWidget
      widget.logic.loadImage(path)
      pattern = widget.logic.getNodePatternFromPath(path)
      masterVolumeNode = slicer.util.getNode(pattern=pattern)
      self.assertTrue( widget.logic.hasImageData(masterVolumeNode) )
      self.delayDisplay('Test master volume image loaded')

      widget.helper.master = masterVolumeNode
      widget.logic.createMerge()
      mergeVolumeNode = slicer.util.getNode(pattern="{0}-label".format(pattern))
      self.assertTrue( widget.logic.hasImageData(mergeVolumeNode) )
      self.delayDisplay('Test merge volume image loaded')

      widget.helper.setVolumes(masterVolumeNode, mergeVolumeNode)
      self.delayDisplay('Input volumes set')
    except Exception, e:
      import traceback
      traceback.print_exc()
      self.delayDisplay('Test caused exception!\n' + str(e))

  def test_WaistCircumference2(self):
    self.delayDisplay("Starting Test 2")

    try:
      self.delayDisplay("Paint a circle for label 1")
      editUtil = EditorLib.EditUtil.EditUtil()
      lm = slicer.app.layoutManager()
      paintEffect = EditorLib.PaintEffectOptions()
      paintEffect.setMRMLDefaults()
      paintEffect.__del__()
      sliceWidget = lm.sliceWidget('Red')
      paintTool = EditorLib.PaintEffectTool(sliceWidget)
      editUtil.setLabel(1)
      (x, y) = self.rasToXY((38,165,-122), sliceWidget)
      paintTool.paintAddPoint(x, y)
      paintTool.paintApply()
      self.delayDisplay("Paint a circle for label 2")
      editUtil.setLabel(2)
      (x, y) = self.rasToXY((12.5,171,-122), sliceWidget)
      paintTool.paintAddPoint(x, y)
      paintTool.paintApply()
      paintTool.cleanup()
      paintTool = None
      self.delayDisplay("Painted circles for labels 1 and 2")

      self.delayDisplay("Test 2 passed!\n")

    except Exception, e:
      import traceback
      traceback.print_exc()
      self.delayDisplay('Test caused exception!\n' + str(e))

  def rasToXY(self, rasPoint, sliceWidget):
    sliceLogic = sliceWidget.sliceLogic()
    sliceNode = sliceLogic.GetSliceNode()
    rasToXY = vtk.vtkMatrix4x4()
    rasToXY.DeepCopy(sliceNode.GetXYToRAS())
    rasToXY.Invert()
    xyzw = rasToXY.MultiplyPoint(rasPoint+(1,))
    x = int(round(xyzw[0]))
    y = int(round(xyzw[1]))
    return x, y

  def test_WaistCircumference3(self):
    self.delayDisplay("Starting Test 3")
    try:
      widget = slicer.modules.WaistCircumferenceWidget
      self.delayDisplay("Opened WaistCircumferenceWidget")

      widget.onApplyButton()
      self.delayDisplay("Apply button selected")

      self.delayDisplay('Test 3 passed!')
    except Exception, e:
      import traceback
      traceback.print_exc()
      self.delayDisplay('Test caused exception!\n' + str(e))
