## Extracting a time-series water masks using Random Forest - Lesotho

This tutorial assumes people have basic knowledge about Google Earth Engine code editor.

### Load imagery

In this tutorial, we will produce/output a bi-weekly time-series (2018-2019) of water masks with each band representing a binary water mask. The goal for generating this time-series water masks is to monitoring the water changes bi-weekly from 2018 to 2019. The satellite imageries are from sentinel 2. The study area is in the western region of Lesotho. To do so, we need satellite imagery of the study region for the bi-weekly image composite from 2018 to 2019. 

To understand the detail of this dataset we are using in this write-up, find the description [here](https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S2_SR#description).

This block of code is to load the bi-weekly data from sentinel 2, with the cloud cover less than or equal to 1%.

```javascript

// Creating bi-weekly image

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
var endDate = '2019-01-01'

var biweekDifference = ee.Date(startDate).advance(2, 'week').millis().subtract(ee.Date(startDate).millis());
var listMap = ee.List.sequence(ee.Date(startDate).millis(), ee.Date(endDate).millis(), biweekDifference);


// Get biweekly sentinel2 for the date between start and end date
var sentinel2 = ee.ImageCollection.fromImages(listMap.map(function(dateMillis){
  var date = ee.Date(dateMillis);
  return getBiweeklySentinelComposite(date);
}));

```

### Creating indices for each image composite in the stacked image collection sentinel2.

Each of the index function is independently generated. In this case, we are going to use the SWI, NDWI, NDDI, together with all the other bands to create a random forest classification model. There are four water indices created in the script, however, after analyzing the collinearity between the four water indices, SWI, NDWI, NDDI, and NDPI in script xxxx, we found the high correlation value between the SWI and NDPI. Thus, we only include SWI to create the random forest model. The functions that are used to generate other indices also included in the script snippet for records. The generated Sentinel2idxCollection is an image collection with all indices added to each image in the stacked image collection. 

For water body detection, the NDWI uses green band and NIR band, while the NDPI uses green band and SWIR. According to the water [spectral reflectance signature] (https://www.sciencedirect.com/topics/earth-and-planetary-sciences/spectral-reflectance) and the sentinel 2 spectral bands, the central wavelength of NIR is 832 nm with bandwidth 106 nm, and the central wavelength for SWIR is 1613 with bandwidth 91 nm. From the water spectral signature (the dotted line on the bottom in the figure), water has a higher reflectance on the band with wavelength 400-600 and gradually decreases from 600-1000, until later close to 0. The author who first combined SWIR and green band to calculate NDWI was to estimate the water content of vegetation canopy rather than detecting water bodies. This explains the ~0.45 correlation between NDWI and NDPI.

This might also explain why NDPI and SWI are highly correlated, since the difference between SWI and NDPI is that the SWI uses Red Edge 1 with SWIR and the NDPI uses green band with SWIR. The central wavelength of Red Edge 1 is 704nm with bandwidth 15nm, while the central wavelength of green band is 559 nm with bandwidth 36nm.

For the reason that NDPI and SWI are highly correlated (~0.99), the NDPI will be ignored in the random forest construction.

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
  // (NDVI − NDWI)∕(NDVI + NDWI)
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

### Training sample collection for random forest
In this section, we are going to create a list of random points from the digitized water and non-water polygons, these random points will be used as training data for training the random forest algorithm.

First, define the bands that will be used in the model prediction.

```javascript

// Bands info: B2-Blue-10m; B3-Green-10m; B4-Red-10m; B5:RedEdge1; B6:RedEdge2; B7:RedEdge3;
// B8:NIR-10m; B9:Narrow NIR; B10:Water Vapor-60m; B10:SWIR-cirrus-60m; B111:SWIR1; B12:SWIR2

var bandlist = ['SWI','NDWI','NDDI','B2','B3','B4','B5','B6','B7','B8','B8A','B9','B11','B12'];
```
Second, randomly generating 500 points from water samples, and 500 points from non-water samples. These 1000 random points will be used as our training data for model generalization. The output combinedPointCollection is a feature collection with 1000 sample points.

```javascript

var wpoly = ee.FeatureCollection(water);
var fpoly = ee.FeatureCollection(farmland);

// Create random points for water, training samples
var rd_points_water = ee.FeatureCollection.randomPoints(wpoly,500, 0, 10)
                                          .map(function(feat)
                                                  {return feat.set('ld_type',1)}
                                                );//.set('ld_type','water');
var ptsBuff_water = rd_points_water.map(bufferPoints(10, false));

print("rd_points_water", rd_points_water);


// Create random points for farmland extraction
var rd_points_fl = ee.FeatureCollection.randomPoints(fpoly,500, 0, 10)
                                        .map(function(feat)
                                                  {return feat.set('ld_type',0)}
                                                );
var ptsBuff_fl = rd_points_fl.map(bufferPoints(10, false));
print("rd_points_fl", rd_points_fl);


var combinedPointCollection = ptsBuff_water.merge(ptsBuff_fl);
print("combinedPointCollection", combinedPointCollection);

Map.addLayer(combinedPointCollection);

```

### Building a random forest classification

We use the first image in the image collection Sentinel2idxCollection as an example to illustrate the process to construct a random forest model for an image classification. We now have our imagery and our training data and it's time to run the random forests classification.

The code below generates the random forest classifier to predict the probability of the occurency of water. The classified layer is a probability map, which you can visualize the result by adding the layer to the map.

```javascript

// Start working on Random Forest
// ---------------------------------------------------------------------------

// Random forest for one image
var time1=Sentinel2idxCollection.first();

// Sample the input imagery to get a FeatureCollection of training data.
var training = time1.select(bandlist).sampleRegions({
  collection: combinedPointCollection, 
  properties: ['ld_type'],
  scale: 10
});


// Make a Random Forest classifier and train it with sample data.
var classifier = ee.Classifier.smileRandomForest(5)
    .setOutputMode('PROBABILITY')
    .train({
      features: training,
      classProperty: 'ld_type',
      inputProperties: bandlist
    });

// Classify the input imagery.
//var classified = input.classify(classifier);

print(classifier);

// Classify the input imagery.
var classified = time1.select(bandlist).classify(classifier);

// Define a palette for the Land Use classification.
var palette = [
  'D3D3D3', // water (0)  // grey
  '0000FF', // non-water (1)  // blue
];

// Display the classification result and the input image.
print("classification output", classified);
Map.addLayer(classified.clip(region), {min: 0, max: 2, palette: palette}, 'Land Use Classification');

```

### Finding the optimal probability threshold for random forest classification (ROC).
In this section, the scripts below are used to find the optimal SWI threshold value to distinguish water and non-water categories. The ROC curve is also created to evaluate the threshold value. 

First, use the water samples and non-water samples you generated earlier to create a combined feature collection, this feature collection indicates the classification "probability" value of each sample data you used for training. You can check the feature properties by print the data out.

```javascript
// Finding the optimal probability value to classify water and non-water cases.
// Sample input points.
var waterd = classified.reduceRegions(rd_points_water,ee.Reducer.max().setOutputs(['classification']),10).map(function(x){return x.set('is_target',1);})
var nonwaterd = classified.reduceRegions(rd_points_fl,ee.Reducer.max().setOutputs(['classification']),10).map(function(x){return x.set('is_target',0);})
var combined = waterd.merge(nonwaterd);


// Show random forest probability of points
print(waterd.aggregate_array('classification'),'Water probability');
print(nonwaterd.aggregate_array('classification'),'Non-Water probability');

print("combined", combined);
```

Second, similar to the index value threshold analysis, below functions are used to generate the ROC curve, and to calculate the best ROC value (different from the threshold analysis, the "threshold" here is the probability value rather than the index value. The index of SWI ranges from -1 to 1. Here, the probability value ranges from 0-1). 

```javascript

// Calculate the Receiver Operating Characteristic (ROC) curve
// -----------------------------------------------------------

// Chance these as needed
var ROC_field = 'classification', ROC_min = 0, ROC_max = 1, ROC_steps = 500, ROC_points = combined


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
      vAxis: { title: 'True-negative-rate'},
      lineWidth: 1}))

// find the cutoff value whose ROC point is closest to (0,1) (= "perfect classification")      
var ROC_best = ROC.sort('dist').first().get('cutoff').aside(print,'best ROC point cutoff');
```

### Using the optimal probability as threshold value in determing the classification result.

The ROC_best is the optimal probability value that uses to distinguish water and non-water cases. You will use this value to create a binary water mask as the output. The optimal probability value is about 0.488 for the selected image, so we use this probability value as the cutting point to produce a binary water mask. You can add the generated layer to your map.

```javascript
// Generating a binary classification map
var binaryClass = classified.select("classification").gte(0.488);
Map.addLayer(binaryClass);

```

### Variable importance

Below script is used to generate the variable importance map for your random forest classifier. You can see how much each band contributes to your random forest classifier.

```javascript
// Generating the variable importance chart
// ------------------------------------------------------------------------
var dict = classifier.explain();
print('Explain:',dict);

var variable_importance = ee.Feature(null, ee.Dictionary(dict).get('importance'));
 
var chart =
ui.Chart.feature.byProperty(variable_importance)
.setChartType('ColumnChart')
.setOptions({
title: 'Random Forest Variable Importance',
legend: {position: 'none'},
hAxis: {title: 'Bands'},
vAxis: {title: 'Importance'}
});

print(chart);

```

### Accuracy Assessment using testing data.

```javascript

```


### Export the binary classification result, and probability result.

The following code is used to export the binary classification map and probability layer you produced.

```javascript

// Exporting the probability and the binary classification result

Export.image.toDrive({image: classified,
                      description: 'Water_probability_RF',
                      folder:'MCC_Lesotho',
                      scale: 10,
                      region: region,
                      fileFormat: 'GeoTiff',
                      crs: 'EPSG:3857',
                      maxPixels: 1808828538,
                      formatOptions: {cloudOptimized: true}
}); //1191858690


Export.image.toDrive({image: binaryClass,
                      description: 'Water_binary_RF',
                      folder:'MCC_Lesotho',
                      scale: 10,
                      region: region,
                      fileFormat: 'GeoTiff',
                      crs: 'EPSG:3857',
                      maxPixels: 1808828538,
                      formatOptions: {cloudOptimized: true}
}); //1191858690


```





<!-- 

<!-- 
<center>
![](images/polygon-tool.png)
</center>


<center>
![](images/define-feature.png)
</center>

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
 
