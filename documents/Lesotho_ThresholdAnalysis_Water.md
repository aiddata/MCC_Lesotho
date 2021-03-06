## Extracting a time-series water masks using the optimal SWI values - Lesotho

In this tutorial, we will produce/output a bi-weekly time-series (2018-2021) of water masks with each band representing a binary water mask. The goal for generating this time-series water masks is to monitoring the water changes bi-weekly from 2018 to 2021. The satellite imageries are from sentinel 2. The study area is in the western region of Lesotho. To do so, we need satellite imagery of the study region for the bi-weekly image composite from 2018 to 2021.

### Load imagery

To understand the detail of this dataset we are using in this write-up, find the description [here](https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S2_SR#description).

This block of code is to load the bi-weekly data from sentinel 2, with the cloud cover less than or equal to 1%.

```javascript

// Creating bi-weekly image// Creating bi-weekly image


function getBiweeklySentinelComposite(date) {
        
        var sentinel2 = ee.ImageCollection('COPERNICUS/S2_SR')
                            .filterBounds(region)
                            .filterDate(date, date.advance(2, 'week'))
                            .filterMetadata('CLOUD_COVERAGE_ASSESSMENT', 'not_greater_than', 1);
        
        var composite = sentinel2.median()
                            .set('system:time_start', date.millis(), 'dateYMD', date.format('YYYY-MM-dd'), 'numbImages', sentinel2.size());
        
        return composite;
      }

// Define the working region geometry
var region = ee.Geometry.Rectangle(27.248340, -29.632341, 27.416364, -29.750510);

// Define time range
var startDate = '2018-01-01'
var endDate = '2021-06-30'
var biweekDifference = ee.Date(startDate).advance(2, 'week').millis().subtract(ee.Date(startDate).millis());
var listMap = ee.List.sequence(ee.Date(startDate).millis(), ee.Date(endDate).millis(), biweekDifference);


// Get biweekly sentinel2 for the date between start and end date
var sentinel2 = ee.ImageCollection.fromImages(listMap.map(function(dateMillis){
  var date = ee.Date(dateMillis);
  return getBiweeklySentinelComposite(date);
}));

```

### Creating indices for each image composite in the stacked image collection sentinel2.
Each of the index function is independently generated. In this case, we are only going to use the SWI, other functions are copied below for records. The generated Sentinel2idxCollection is an image collection with all indices added to each image in the stacked image collection. 

```javascript

// Functions to add selected indices to the sentinel2 images
// -----------------------------------------------------------------------------
      
// Bands info: B2-Blue-10m; B3-Green-10m; B4-Red-10m; B5:RedEdge1; B6:RedEdge2; B7:RedEdge3;
// B8:NIR-10m; B9:Narrow NIR; B10:Water Vapor-60m; B10:SWIR-cirrus-60m; B111:SWIR1; B12:SWIR2

// VEGETATION INDICES (4)
//---------------------
      
function addNDVI(image) {
  // NDVI
  var ndvi = image.normalizedDifference(['B8', 'B4']).rename('NDVI')
                  .copyProperties(image,['system:time_start','system:time_end']);
  return image.addBands(ndvi).clip(region);
}

      
function addREdge1(image){
  // Red Edge1 NDVI: (B8-B5)/(B8+B5)
  var redge1 = image.normalizedDifference(['B8', 'B5']).rename('RedEdge1');
  return image.addBands(redge1).clip(region);
}
      
      
function addGNDVI(image){
  // GNDVI: green normalzied difference vegetation
  var gndvi = image.normalizedDifference(['B8', 'B3']).rename('GNDVI');
  return image.addBands(gndvi).clip(region);
}
      
      
function addSRRE(image) {
  // SRRE: Simple ratio red edge
  var srre = image.expression('B8/B5',{
    'B8': image.select('B8'),
    'B5': image.select('B5')
    }).rename('SRRE');
    return image.addBands(srre).clip(region);
}
      

// WATER INDEX (4)
//---------------------
      
function addNDWI(image) {
  // NDWI, sensitive the buil-ups
  var ndwi = image.normalizedDifference(['B3', 'B8']).rename('NDWI');
  return image.addBands(ndwi).clip(region);
}
      
      
function addSWI(image) {
  // SWI
  var swi = image.normalizedDifference(['B5', 'B11']).rename('SWI');
  return image.addBands(swi).clip(region);
}


function addNDDI(image) {
  // NDDI: normalized difference drought
  // (NDVI ??? NDWI)???(NDVI + NDWI)
  var nddi = image.expression('(((B8-B4)/(B8+B4))-((B3-B8)/(B3+B8)))/(((B8-B4)/(B8+B4))+((B3-B8)/(B3+B8)))',{
    'B8': image.select('B8'),
    'B4': image.select('B4'),
    'B3': image.select('B3')
    }).rename('NDDI');
        
    return image.addBands(nddi).clip(region);
}
      
function addNDPI(image){
    // NDPI: normalized difference pond
    // (SWIR-G)/(SWIR+G)
    var ndpi = image.normalizedDifference(['B11', 'B3']).rename('NDPI');
    return image.addBands(ndpi).clip(region);
}

function addSWM(image){
        // SWM: sentinel water mask
        // (B2+B3)/(B8+B11)
        var swm = image.expression('(B2+B3)/(B8+B11)',{
          'B2': image.select('B2'),
          'B3': image.select('B3'),
          'B8': image.select('B8'),
          'B11': image.select('B11')
        }).rename('SWM');
        return image.addBands(swm).clip(region);
      }
      
      
// SOIL INDEX (3)
//---------------------
function addBSI(image) {
  // Bare soil index: (B11+B4)-(B8+B2)/(B11+B4)+(B8+B2)
  var bsi = image.expression('((B11+B4)-(B8+B2))/((B11+B4)+(B8+B2))',{
    'B11': image.select('B11'),
    'B4': image.select('B4'),
    'B8': image.select('B8'),
    'B2': image.select('B2')
    }).rename('BSI');
    return image.addBands(bsi).clip(region);
}
      
      
function addBright(image){
    // BRIGHTNESS INDEX
    //sqrt(((Red * Red)/ (Green* Green))/2)
    var brightI = image.expression('sqrt(((B4*B4)/(B3*B3))/2)',{
      'B3': image.select('B3'),
      'B4': image.select('B4')
      }).rename('BRIGHTI');
    return image.addBands(brightI).clip(region);
}

// Filter out the image that have cloud > 1% cover
// Add the indices to each image in the collection
var Sentinel2idxCollection = sentinel2
    .map(function(image) {
      return image.set('count', image.bandNames().length())
    })
    .filter(ee.Filter.eq('count', 23))
    .map(addNDVI)
    .map(addREdge1)
    .map(addGNDVI)
    .map(addSRRE)
    .map(addNDWI)
    .map(addSWI)
    .map(addNDPI)
    .map(addSWM)
    .map(addNDDI)
    .map(addBSI)
    .map(addBright);

```

### Creating a binary water masks using the optimal SWI value. 

The optimal SWI value is analyzed outside of the GEE environment using python code xxxx and the alloints.csv file in the data folder. From the analysis, each time band image has the same optimal SWI for generating the best classification overall accuracy. The value is xxx, this value is used to create the binary masks. Any SWI value of the SWI band greater than this threshold value will be considered as water, the value below this value is non-water.

The output variable waterBinaries is an image collection of SWI images. Each SWI image has one band named "SWI". In order for better understanding and easy analysis outside of the GEE environment, the band is renamed by its system time.

```javascript

function selectSWI(image){
  return image.select('SWI').gte(-0.1919).copyProperties(image, ["system:time_start"])
}

var waterBinaries = Sentinel2idxCollection.map(selectSWI).map(function(image){
  var dateString = ee.Date(image.get('system:time_start')).format('yyyy-MM-dd');
  var swi = image.select('SWI').rename(dateString)
  .copyProperties(image,['system:time_start','system:time_end']);
  return swi;
});
```

### To export the binary time-series water masks

The below function helps you to output one image, with each band represent one time-stamp water mask.

```javascript
var waterImage = newCollectionToImage(waterBinaries);

Export.image.toDrive({image: waterImage,
                      description: 'WaterMasks_SWI_ThresholdsOut',
                      folder:'MCC_Lesotho',
                      scale: 10,
                      region: region,
                      fileFormat: 'GeoTiff',
                      crs: 'EPSG:3857',
                      maxPixels: 1808828538,
                      formatOptions: {cloudOptimized: true}
}); //1191858690
```


### Generating ROC

In this section, the scripts below are used to find the optimal SWI threshold value to distinguish water and non-water categories. The ROC curve is also created to evaluate the threshold value. 

First, import the water sample polygons and non-water sample polygons that are manually digitized.

```javascript

// Getting the data

var wtrain = ee.FeatureCollection(water_train);
var ftrain = ee.FeatureCollection(non_water_train);

```

Second, randomly generating 500 points from the current water samples, and 500 points from the non-water samples. Then, combine the two data layer. This data layer will be used to calculate true positive rater and false positive rate to generate the ROC. 

```javascript

// Create buffer distance around points
function bufferPoints(radius, bounds) {
  return function(pt) {
    pt = ee.Feature(pt);
    return bounds ? pt.buffer(radius).bounds() : pt.buffer(radius);
  };
}


// -----------------------------------------------------------------------------
// Finding the optimal threshold value and generating ROC for one image

// Create random points for water, the data is used the find the optimal threshod to
// distinguish water and non-water

var rd_points_water = ee.FeatureCollection.randomPoints(wtrain,500, 0, 10)
                                          .map(function(feat)
                                                  {return feat.set('ld_type','water')}
                                                );//.set('ld_type','water');
var ptsBuff_water = rd_points_water.map(bufferPoints(10, false));

print("rd_points_water", rd_points_water);
Map.addLayer(rd_points_water,{}, 'Points');



// Create random points for non water
var rd_points_nw = ee.FeatureCollection.randomPoints(ftrain,500, 0, 10)
                                        .map(function(feat)
                                                  {return feat.set('ld_type','nonwater')}
                                                );
var ptsBuff_nw = rd_points_nw.map(bufferPoints(10, false));
print("rd_points_nw", rd_points_nw);
Map.addLayer(rd_points_nw,{}, 'Points')



// Choosing the first SWI layer in the image collection
var SWIindex = Sentinel2idxCollection.select("SWI").first();


// Sample input points.
var waterd = SWIindex.reduceRegions(ptsBuff_water,ee.Reducer.max().setOutputs(['SWI']),10).map(function(x){return x.set('is_target',1);})
var nonwaterd = SWIindex.reduceRegions(ptsBuff_nw,ee.Reducer.max().setOutputs(['SWI']),10).map(function(x){return x.set('is_target',0);})
var combined = waterd.merge(nonwaterd);


```
Third, below functions are used to generate the ROC curve, and to calculate the best ROC value. 

```javascript

// Calculate the Receiver Operating Characteristic (ROC) curve
// -----------------------------------------------------------

// Define the ROC range and relevant values
var ROC_field = 'SWI', ROC_min = -1, ROC_max = 1, ROC_steps = 100, ROC_points = combined

var ROC = ee.FeatureCollection(ee.List.sequence(ROC_min, ROC_max, null, ROC_steps).map(function (cutoff) {
  var target_roc = ROC_points.filterMetadata('is_target','equals',1);
  // true-positive-rate, sensitivity  
  var TPR = ee.Number(target_roc.filterMetadata(ROC_field,'greater_than',cutoff).size()).divide(target_roc.size());
  var non_target_roc = ROC_points.filterMetadata('is_target','equals',0);
  // true-negative-rate, specificity  
  var TNR = ee.Number(non_target_roc.filterMetadata(ROC_field,'less_than',cutoff).size()).divide(non_target_roc.size());
  return ee.Feature(null,{cutoff: cutoff, TPR: TPR, TNR: TNR, FPR:TNR.subtract(1).multiply(-1),  dist:TPR.subtract(1).pow(2).add(TNR.subtract(1).pow(2)).sqrt()})
}))

print("ROC", ROC);


// Visualization of the ROC curve
// Use trapezoidal approximation for area under curve (AUC)
var X = ee.Array(ROC.aggregate_array('FPR')), 
    Y = ee.Array(ROC.aggregate_array('TPR')), 
    Xk_m_Xkm1 = X.slice(0,1).subtract(X.slice(0,0,-1)),
    Yk_p_Ykm1 = Y.slice(0,1).add(Y.slice(0,0,-1)),
    AUC = Xk_m_Xkm1.multiply(Yk_p_Ykm1).multiply(0.5).reduce('sum',[0]).abs().toList().get(0)
print(AUC,'Area under curve')
// Plot the ROC curve
print(ui.Chart.feature.byFeature(ROC, 'FPR', 'TPR').setOptions({
      title: 'ROC curve',
      legend: 'none',
      hAxis: { title: 'False-positive-rate'},
      vAxis: { title: 'True-positive-rate'},
      lineWidth: 1}))
// find the cutoff value whose ROC point is closest to (0,1) (= "perfect classification")      
var ROC_best = ROC.sort('dist').first().get('cutoff');//.aside(print,'best ROC point cutoff');

```

*Note: The chart is used for visualization purpose, to get the variable importance chart for any selected image, please select the image you used to create this ROC chart.
![The visualization of index trends](../images/ROC.png)


### Accuracy Assessment

Before we make use of the map we just created it's important to know just how accurate it is. For example, if the classified map shows that water occurred in a given area, how confident can we believe that the area is actually water?

A **confusion matrix** is the standard method for assessing the performance of a classification algorithm. It takes cases of known class (e.g. the training data or an independent validation data set) and compares them to their predicted class. The rows of the matrix are instances of the actual class, while the columns are instances of the predicted class. The diagonal of the matrix gives the number of correct classifications, while the off-diagonals give the number of incorrect classifications. For example, in this case we have two classes water and non-water, the matrix might look like:


![The visualization of index trends](../images/ConfusionMatrics.png)

[Chart Source](https://www.dataschool.io/simple-guide-to-confusion-matrix-terminology/)

In this example, 50 out 60 cases of class 1 were correctly classified, while 100 out of 105 cases of class 2 were correctly classified Looking at the off-diagonal components, in 10 cases class 1 was incorrectly assigned to class 2, and in 5 cases class 2 was incorrectly assigned to class 1. The overall accuracy is the total number of correct classifications as a proportion of the total number of cases, which in this case is 150 / 165 = 91%.

In this case, we randomly choose 20 sample points from the testing water layer, and 20 sample points from the testing non-water layer. We use these 40 samples as testing cases to create the confusion matrix. You can increase this number based on how you construct your testing data. To calculate the confusion matrix and overall accuracy for the binary water and non-water map add the following code to the end of your script:

```javascript

// Getting the testing data

var wtest = ee.FeatureCollection(water_test);
var ftest = ee.FeatureCollection(non_water_test);


// Accuracy Assessment
//----------------------------------------------------------------------------

// Sample the testing data from the testing layers.

var test_points_water = ee.FeatureCollection.randomPoints(wtest,20, 0, 10)
                                          .map(function(feat)
                                                  {return feat.set('ld_type','water')}
                                                );//.set('ld_type','water');
var testbuff_water = test_points_water.map(bufferPoints(10, false));


var test_points_nw = ee.FeatureCollection.randomPoints(ftest,20, 0, 10)
                                        .map(function(feat)
                                                  {return feat.set('ld_type','nonwater')}
                                                );
var testbuff_nw = test_points_nw.map(bufferPoints(10, false));


// Sample input points.
var watertest = SWIindex.reduceRegions(testbuff_water,ee.Reducer.max().setOutputs(['SWI']),10).map(function(x){return x.set('is_target',1);})
var nonwatertest = SWIindex.reduceRegions(testbuff_nw,ee.Reducer.max().setOutputs(['SWI']),10).map(function(x){return x.set('is_target',0);})
var validation = watertest.merge(nonwatertest);


var target = validation.filterMetadata('is_target','equals',1);
var TP = ee.Number(target.filterMetadata('SWI','greater_than',-0.1919).size());
var non_target = validation.filterMetadata('is_target','equals',0);
var TN = ee.Number(non_target.filterMetadata('SWI','less_than',-0.1919).size());

var FN = ee.Number(target.filterMetadata('SWI', 'less_than', -0.1919).size());
var FP = ee.Number(non_target.filterMetadata('SWI', 'greater_than', -0.1919).size());

var valerror = ee.List([[TP, FN], [FP, TN]]);

print("Validation error matrix", valerror);

var overallAccuracy = TP.add(TN).divide(TP.add(FN).add(FP).add(TN));

print("Validation overallAccuracy", overallAccuracy);


```

<!-- 


<center>
![](images/polygon-tool.png)
</center>

Now click on the gear icon next to this new layer and fill in the details as highlighter in the image below. This layer will be for the first class: forest unchanged between 2001 and 2011. You need to give it a name ("forest"), set the type as "Feature" rather than Geometry, and add a new "class"" attribute (this will be class 0).

<center>
![](images/define-feature.png)
</center>

Now use all three layers of satellite imagery to identify regions that remain forest throughout the study period and create some polygons delineating these areas. Keep your polygons small and remember to capture the diversity within this class. Once you're done with this class, move on to the to the other classes, making sure to create a new layer for each and fill out the correct information in the layer properties. Call your layers: forest, forestLoss, nonforest, and forestGain.

Once you're done, scroll up to the top of the code editor and you'll see a new section where these polygon layers are imported. Be sure to save your code at this point so you don't loose these polygons!

<center>
![](images/polygon-tool.png)
</center>

## Extract cell values

Finally, we need to combine these four training layers into one and extract the imagery cell values from within the polygons. This will produce a single table that associates pixels of each class with the spectral band values in those pixels. It's likely that when you selected polygons, some classes, such as unchanged forest, were easy to find examples of and therefore the training polygons for these classes cover a much larger area. Ideally we'd like the same number of training cells for each class. Furthermore, Earth Engine imposes usage limits and, if the training polygons contain too many cells, these limits will be exceeded and an error will be returned. To address this, we'll subsample within the polygons. Add the following code to the end of the script you already have.

```javascript
// subsample training polygons with random points
// this ensures all classes have same sample size
// also EE can't handle too many cells at once
var trainingLayers = [forest, forestLoss, nonforest, forestGain];
var n = 500;
// loop over training layers
for (var i = 0; i < trainingLayers.length; i++) { 
  // sample points within training polygons
  var pts = ee.FeatureCollection
    .randomPoints(trainingLayers[i].geometry(), n);
  // add class
  var thisClass = trainingLayers[i].get('class');
  pts = pts.map(function(f) {
    return f.set({class: thisClass});
  });
  // extract raster cell values
  var training = combined.sampleRegions(pts, ['class'], 30);
  // combine trainging regions together
  if (i === 0) {
    var trainingData = training;
  } else {
    trainingData = trainingData.merge(training);
  }
}
```

## Random forests

We now have our imagery and our training data and it's time to run the random forests classification. Add the following code to your script to fit a random forests model and plot the resulting forest change map.

```javascript
//// classify with random forests
// use bands 1-5 from each time period
var bands = ['B1_2001', 'B1_2011', 'B2_2001', 'B2_2011', 'B3_2001', 'B3_2011',
             'B4_2001', 'B4_2011', 'B5_2001', 'B5_2011'];
// fit a random forests model
var classifier = ee.Classifier.randomForest(30)
  .train(trainingData, 'class', bands);
// produce the forest change map
var classified = combined.classify(classifier);
var p = ['00ff00', 'ff0000', '000000', '0000ff'];
// display
Map.addLayer(classified, {palette: p, min: 0, max: 3}, 'classification');
```

Below is an example forest change map, yours may be slightly different since you likely chose different training areas. In this map forest is green, non-forest is black, forest loss is red, and forest gain is blue.

<center>
![](images/change-map.png)
</center>

### Accuracy assessement

Before we make use of the map we just created it's important to know just how accurate it is. For example, if the classified map shows that forest loss occurred in a given area, how confident can we be that that area actually experienced forest loss?

A **confusion matrix** is the standard method for assessing the performance of a classification algorithm. It takes cases of known class (e.g. the training data or an independent validation data set) and compares them to their predicted class. The rows of the matrix are instances of the actual class, while the columns are instances of the predicted class. The diagonal of the matrix gives the number of correct classifications, while the off-diagonals give the number of incorrect classifications. For example, if we only had two classes, the matrix might look like:

$$
\begin{bmatrix}
10 & 2\\ 
3 & 5
\end{bmatrix}
$$

In this example, 10 out 12 cases of class 1 were correctly classified, while 5 out of 8 cases of class 2 were correctly classified Looking at the off-diagonal components, in 2 cases class 1 was incorrectly assigned to class 2, and in 3 cases class 2 was incorrectly assigned to class 1. The overall accuracy is the total number of correct classifications as a proportion of the total number of cases, which in this case is $15 / 20 = 75\%$.

To calculate the confusion matrix and overall accuracy for our forest change map add the following code to the end of your script:

```javascript
// accuracy assessement
var confMat = classifier.confusionMatrix();
print('Confusion matrix: ', confMat);
print('Overall accuracy: ', confMat.accuracy());
```

You should now see the confusion matrix and overall accuracy to the console:

<center>
![](images/accuracy.png)
</center>

In this case, our accuracy was quite good across all the classes, however, note that we used the training data to perform our validation. In practice it's best to collect an independent validation data set, or partition the training data set into training and validation subsets, in order to avoid bias in the accuracy assessment. This is possible in Earth Engine, however it is out of the scope of this tutorial.

## Conclusion

In this tutorial we used supervised classification to build a forest change map for a single Landsat scene in Brazil. However, this only scratches the surface of what's possible with Earth Engine. We could have extended our analysis to include a much larger region or to study land change in a different geographic location or biome. And, the applications aren't limited to land-cover change in the context of conservation, Earth Engine is broadly applicable to any task requiring analysis of spatiotemporal trends on the Earth's surface.

The [full script](https://code.earthengine.google.com/b2032d825436fe7e8018c3b64610cd89) for this tutorial is online. To learn more about Earth Engine complete the [Introduction to Earth Engine tutorial](https://developers.google.com/earth-engine/tutorials) if you haven't already. Then consult the [Earth Engine Guides](https://developers.google.com/earth-engine/), which provides excellent tutorials on all the major funcationality of Earth Engine. Finally, if at any point you get stuck, try reaching out to the [Earth Engine Google Group](https://groups.google.com/forum/#!forum/google-earth-engine-developers) for help.


 -->
 
