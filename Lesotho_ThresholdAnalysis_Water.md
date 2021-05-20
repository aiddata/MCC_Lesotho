---
title: "Extracting a time-series water masks using the optimal SWI values - Lesotho"
output:
  html_document:
    keep_md: true
---
This tutorial assumes people have basic knowledge about Google Earth Engine code editor.

## Load imagery

In this tutorial, we will produce/output a bi-weekly time-series (2018-2020) of water masks with each band representing a binary water mask. The goal for generating this time-series water masks is to monitoring the water changes bi-weekly from 2018 to 2020. The satellite imageries are from sentinel 2. The study area is in the western region of Lesotho. To do so, we need satellite imagery of the study region for the bi-weekly image composite from 2018 to 2020. 

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
var startDate = '2019-01-01'
var endDate = '2020-01-01'
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
