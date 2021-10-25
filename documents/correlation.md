## Measuring indicators for monitoring water resources

The aim of this post is to create a step by step instruction on measuring the statistic relationship between the water indices. The correlation between the selected water indices will be used to keep/remove the water indices from further analysis.

From literature review, the NDWI, SWI, mNDWI, and SWM were selected for the water detection. To understand the process of adding the water indices as bands, see other posts in this folder.


```javascript

function getSentinelComposite(date) {
        
        var sentinel2 = ee.ImageCollection('COPERNICUS/S2_SR')
                            .filterBounds(region)
                            .filterDate(date, date.advance(1, 'year'))
                            .filterMetadata('CLOUD_COVERAGE_ASSESSMENT', 'not_greater_than', 1);
        
        var composite = sentinel2.median()
                            .set('system:time_start', date.millis(), 'dateYMD', date.format('YYYY-MM-dd'), 'numbImages', sentinel2.size());
        
        return composite;
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

function addmNDWI(image){
    // mNDWI: modified normalized difference water index
    // (G-SWIR)/(G+SWIR)
    var mndwi = image.normalizedDifference(['B3', 'B11']).rename('mNDWI');
    return image.addBands(mndwi).clip(region);
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
      
var region = study_area; //ee.Geometry.Rectangle(27.248340, -29.632341, 27.416364, -29.750510);

var startDate = '2018-01-01';
var endDate = '2021-06-01';
var timeDifference = ee.Date(startDate).advance(1, 'year').millis().subtract(ee.Date(startDate).millis());
var listMap = ee.List.sequence(ee.Date(startDate).millis(), ee.Date(endDate).millis(), timeDifference);


// Get biweekly sentinel2 data
var sentinel2 = ee.ImageCollection.fromImages(listMap.map(function(dateMillis){
  var date = ee.Date(dateMillis);
  return getSentinelComposite(date);
}));


// Filter out non-band images
var Sentinel2idxCollection = sentinel2
    .map(function(image) {
      return image.set('count', image.bandNames().length());
    })
    .filter(ee.Filter.eq('count', 23))
    .map(addSWI)
    .map(addSWM)
    .map(addNDWI)
    .map(addmNDWI);
    


```

We use NDWI as an example to measure the relationship with the other three indices. 

```javascript

// collinearity analysis

var image = Sentinel2idxCollection.first();

// Get a dictionary with band names as keys, pixel lists as values.
var result = image.reduceRegion(ee.Reducer.toList(), data, 50);

// Convert the band data to plot on the y-axis to arrays.
var y1 = ee.Array(result.get('SWI'));
var y2 = ee.Array(result.get('SWM'));
var y3 = ee.Array(result.get('mNDWI'));

// Concatenate the y-axis data by stacking the arrays on the 1-axis.
var yValues = ee.Array.cat([y1, y2, y3], 1);

// The band data to plot on the x-axis is a List.
var xValues = result.get('NDWI');

// Make a band correlation chart.
var chart = ui.Chart.array.values(yValues, 0, xValues)
    .setSeriesNames(['SWI', 'SWM', 'mNDWI'])
    .setOptions({
      title: 'Sentinel-2 NDWI vs. {SWI,SWM, mNDWI}',
      hAxis: {'title': 'NDWI'},
      vAxis: {'title': '{SWI,SWM,mNDWI}'},
      pointSize: 3,
      trendlines: { 0: {showR2: true, visibleInLegend: true}, 
                    1: {showR2: true, visibleInLegend: true},
                    2: {showR2: true, visibleInLegend: true}
      }
});

// Print the chart.
print(chart);

print('Linear fit output NDWI vs SWI',ee.Array.cat([xValues, y1], 1).reduce(ee.Reducer.linearFit(),[0],1));
print('Linear fit output NDWI vs SWM',ee.Array.cat([xValues, y2], 1).reduce(ee.Reducer.linearFit(),[0],1));
print('Linear fit output SWI vs SWM',ee.Array.cat([y1, y2], 1).reduce(ee.Reducer.linearFit(),[0],1));

```

![The visualization of index trends](../images/correlation.png)



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
 
