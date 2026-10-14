// Cyclone Idai Sentinel-1 pre/post export for Google Earth Engine.
//
// Uses the agreed 18 February 2019 pre-event baseline and a
// 20 March 2019 post-event scene.

var beira = ee.Geometry.Rectangle([
  34.65, -19.95,
  35.10, -19.65
]);

var preImage = ee.Image(
  'COPERNICUS/S1_GRD/S1B_IW_GRDH_1SDV_20190218T160653_20190218T160722_015002_01C07E_D1A3'
);
var postImage = ee.Image(
  'COPERNICUS/S1_GRD/S1A_IW_GRDH_1SDV_20190320T160724_20190320T160753_026423_02F51E_2D7F'
);

var preEvent = ee.Image.cat([
  preImage.select('VV').rename('pre_vv'),
  preImage.select('VH').rename('pre_vh')
]);
var postEvent = ee.Image.cat([
  postImage.select('VV').rename('post_vv'),
  postImage.select('VH').rename('post_vh')
]);

var smoothedStack = preEvent.addBands(postEvent)
  .focal_mean({
    radius: 30,
    kernelType: 'circle',
    units: 'meters'
  })
  .rename(['pre_vv', 'pre_vh', 'post_vv', 'post_vh']);

var commonValid = preImage.select('VV').mask()
  .and(postImage.select('VV').mask())
  .selfMask();
var overlapRegion = commonValid.geometry(100)
  .intersection(beira, 100);
var overlapArea = overlapRegion.area(100);

print('Pre-event footprint area (m2)', preImage.geometry().area(100));
print('Post-event footprint area (m2)', postImage.geometry().area(100));
print('Common valid-mask area (m2)', commonValid.geometry(100).area(100));
print('Overlap export area (m2)', overlapArea);
print('Export region is valid', ee.Number(overlapArea).gt(0));

Map.centerObject(overlapRegion, 9);
Map.addLayer(
  overlapRegion,
  {color: 'yellow'},
  'Idai common valid SAR region'
);

Export.image.toDrive({
  image: smoothedStack,
  description: 'Idai_S1_PrePost_20190218_20190320_overlap',
  folder: 'GEE_Cyclone_Exports',
  fileNamePrefix: 'Idai_S1_PrePost_20190218_20190320_overlap',
  region: overlapRegion,
  scale: 10,
  crs: 'EPSG:3857',
  maxPixels: 1e13,
  fileFormat: 'GeoTIFF'
});
