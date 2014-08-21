import os
import unittest
from __main__ import vtk, qt, ctk, slicer
import Editor
import SimpleITK as sitk
import sitkUtils as su

#
# WaistCircumference
#

class WaistCircumference:
  def __init__(self, parent):
    parent.title = "WaistCircumference" # TODO make this more human readable by adding spaces
    parent.categories = ["Testing.TestCases"]
    parent.dependencies = []
    parent.contributors = ["Jessica Forbes (University of Iowa)"] # replace with "Firstname Lastname (Organization)"
    parent.helpText = """
    This is an example of scripted loadable module bundled in an extension.
    """
    parent.acknowledgementText = """
    This file was originally developed by Jean-Christophe Fillion-Robin, Kitware Inc.
    and Steve Pieper, Isomics, Inc. and was partially funded by NIH grant 3P41RR013218-12S1.
""" # replace with organization, grant and thanks.
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
    self.fileDialog = None
    self.imageFileListPath = '/scratch/WaistCircumference/volumesList.csv'
    self.dirDialog = None
    self.logic = None
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
    self.helper = self.localEditorWidget.helper

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
    self.saveButton = qt.QPushButton("Save")
    self.saveButton.toolTip = "Save statistics to csv and save mrml scene."
    self.saveButton.enabled = False
    measurementsFormLayout.addRow(self.saveButton)

    # connections
    self.selectImageListButton.connect('clicked(bool)', self.onSelectImageList)
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
    self.logic = WaistCircumferenceLogic()
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
    for i in self.logic.labelStats["Labels"]:
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
        # set data as float with Qt::DisplayRole
        item.setData(float(self.logic.labelStats[i,k]),qt.Qt.DisplayRole)
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

  def onSelectImageList(self):
    """load the file containing a list absolute paths to images
    """
    if not self.fileDialog:
      self.fileDialog = qt.QFileDialog(self.parent)
      self.fileDialog.options = self.fileDialog.DontUseNativeDialog
      self.fileDialog.acceptMode = self.fileDialog.AcceptOpen
      self.fileDialog.defaultSuffix = "csv"
      self.fileDialog.setNameFilter("Comma Separated Values (*.csv)")
      self.fileDialog.connect("fileSelected(QString)", self.onFileSelected)
    self.fileDialog.show()

  def onFileSelected(self, fileName):
    self.imageFileListPath = fileName
    self.readImageFileList()
    for path in self.imageFileList[:1]:
      self.loadImage(path)
      pattern = self.getNodePatternFromPath(path)
      masterVolumeNode = slicer.util.getNode(pattern=pattern)
      self.helper.master = masterVolumeNode
      self.createMerge()
      mergeVolumeNode = slicer.util.getNode(pattern="{0}-label".format(pattern))
      self.helper.setVolumes(masterVolumeNode, mergeVolumeNode)

  def readImageFileList(self):
    if self.imageFileListPath:
      self.imageFileList = list()
      with open(self.imageFileListPath, 'rU') as imageList:
        for row in imageList:
          self.imageFileList.append(row.rstrip())
      print self.imageFileList

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
      qt.QMessageBox.warning(slicer.util.mainWindow(),
          "Create merge throwing error", 'Exception!\n\n' + str(e) + "\n\nSee Python Console for Stack Trace")

  def onSave(self):
    """save the label statistics
    """
    if not self.dirDialog:
      self.dirDialog = qt.QFileDialog(self.parent)
      self.dirDialog.options = self.dirDialog.DontUseNativeDialog
      self.dirDialog.acceptMode = self.dirDialog.AcceptOpen
      self.dirDialog.fileMode = self.dirDialog.DirectoryOnly
      self.dirDialog.connect("fileSelected(QString)", self.onDirSelected)
    self.dirDialog.show()

  def onDirSelected(self, dirName):
    # saves the current scene to selected folder
    l = slicer.app.applicationLogic()
    l.SaveSceneToSlicerDataBundleDirectory(dirName, None)

    # saves the csv files to selected folder
    csvFileName = os.path.join(dirName, "{0}_waist_circumference.csv".format(os.path.split(dirName)[1]))
    self.logic.saveStats(csvFileName)

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
    self.keys = ("Index", "Circumference (mm)", "Circumference (in)")
    self.labelStats = {}
    self.labelStats['Labels'] = []

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
    label3D = su.PullFromSlicer(merge.GetName())
    currentSlice = self.getCurrentSlice()
    img2D = label3D[:, :, currentSlice]
    filter2D = sitk.LabelShapeStatisticsImageFilter()
    filter2D.Execute(img2D)
    self.labelStats['Labels'] = filter2D.GetLabels()
    for labelValue in self.labelStats['Labels']:
      self.labelStats[int(labelValue), self.keys[0]] = int(labelValue)
      self.labelStats[int(labelValue), self.keys[1]] = filter2D.GetPerimeter(labelValue)
      self.labelStats[int(labelValue), self.keys[2]] = self.mmToInch(filter2D.GetPerimeter(labelValue))

  def mmToInch(self, val):
    return val * 0.03937

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
    for i in self.labelStats["Labels"]:
      line = ""
      for k in self.keys[:-1]:
        line += str(self.labelStats[i,k]) + ","
      line += str(self.labelStats[i,self.keys[-1]]) + "\n"
      csv += line
    return csv

  def saveStats(self,fileName):
    fp = open(fileName, "w")
    fp.write(self.statsAsCSV())
    fp.close()

  def run(self, master, merge, enableScreenshots=0, screenshotScaleFactor=1):
    """
    Run the actual algorithm
    """

    self.delayDisplay('Running the aglorithm')

    self.enableScreenshots = enableScreenshots
    self.screenshotScaleFactor = screenshotScaleFactor

    self.takeScreenshot('WaistCircumference-Start','Start',-1)
    
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
    # self.test_WaistCircumference1()
    # self.test_WaistCircumference2()
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
      imagePath = "/scratch/WaistCircumference/2AbdPelvis5.nrrd"
      labelPath = "/Shared/johnsonhj/HDNI/20140527_WaistCircumfrenceProject/20140529_Jessica_Test_Data/2AbdPelvis5-label.nrrd"
      slicer.util.loadVolume(imagePath)
      slicer.util.loadLabelVolume(labelPath)

      volumeNode = slicer.util.getNode(pattern="2AbdPelvis5")
      logic = WaistCircumferenceLogic()
      self.assertTrue( logic.hasImageData(volumeNode) )
      self.delayDisplay('Test volume image loaded')

      labelNode = slicer.util.getNode(pattern="2AbdPelvis5-label")
      logic = WaistCircumferenceLogic()
      self.assertTrue( logic.hasImageData(labelNode) )
      self.delayDisplay('Test label image loaded')

      widget = slicer.modules.WaistCircumferenceWidget
      widget.helper.setMasterVolume(volumeNode)
      self.delayDisplay('Test label image set as Master Volume')
      self.delayDisplay('Test 1 passed!')
    except Exception, e:
      import traceback
      traceback.print_exc()
      self.delayDisplay('Test caused exception!\n' + str(e))

  def test_WaistCircumference2(self):
    self.delayDisplay("Starting Test 2")
    try:
      widget = slicer.modules.WaistCircumferenceWidget
      self.delayDisplay("Opened WaistCircumferenceWidget")

      widget.onApplyButton()
      self.delayDisplay("Apply button selected")

      self.delayDisplay('Test 2 passed!')
    except Exception, e:
      import traceback
      traceback.print_exc()
      self.delayDisplay('Test caused exception!\n' + str(e))

  def test_WaistCircumference3(self):
    self.delayDisplay("Starting Test 3")
    try:
      imagePath = "/scratch/WaistCircumference/2AbdPelvis5.nrrd"
      widget = slicer.modules.WaistCircumferenceWidget
      widget.loadImage(imagePath)
      self.delayDisplay('Opened image, created label, set input volumes')
    except Exception, e:
      import traceback
      traceback.print_exc()
      self.delayDisplay('Test caused exception!\n' + str(e))