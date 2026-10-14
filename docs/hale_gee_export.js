// Ex-Tropical Cyclone Hale Sentinel-1 pre/post export for Google Earth Engine.

var hawkesBay = ee.Geometry.Rectangle([
  176.55, -40.05,
  177.55, -38.85
]);

var s1 = ee.ImageCollection('COPERNICUS/S1_GRD')
  .filterBounds(hawkesBay)
  .filter(ee.Filter.eq('instrumentMode', 'IW'))
  .filter(ee.Filter.eq('resolution_meters', 10))
  .filter(ee.Filter.listContains(
    'transmitterReceiverPolarisation', 'VV'))
  .filter(ee.Filter.listContains(
    'transmitterReceiverPolarisation', 'VH'));

var preCandidates = s1
  .filterDate('2022-12-20', '2023-01-09')
  .filter(ee.Filter.eq('orbitProperties_pass', 'DESCENDING'))
  .sort('system:time_start', false);

var initialPre = ee.Image(preCandidates.first());
var selectedOrbit = initialPre.get('relativeOrbitNumber_start');
var postCandidates = s1
  .filterDate('2023-01-13', '2023-01-26')
  .filter(ee.Filter.eq('orbitProperties_pass', 'DESCENDING'))
  .filter(ee.Filter.eq('relativeOrbitNumber_start', selectedOrbit))
  .sort('system:time_start', true);

var preImage = initialPre;
var postImage = ee.Image(postCandidates.first());
print('Pre-event candidate count', preCandidates.size());
print('Post-event matching-orbit count', postCandidates.size());
print('Selected pre-event ID', preImage.get('system:index'));
print('Selected post-event ID', postImage.get('system:index'));
print('Selected relative orbit', selectedOrbit);

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
  .intersection(hawkesBay, 100);
var overlapArea = overlapRegion.area(100);
print('Common valid-mask area (m2)', commonValid.geometry(100).area(100));
print('Overlap export area (m2)', overlapArea);
print('Export region is valid', ee.Number(overlapArea).gt(0));

Map.centerObject(overlapRegion, 9);
Map.addLayer(overlapRegion, {color: 'yellow'}, 'Hale common valid SAR region');

Export.image.toDrive({
  image: smoothedStack,
  description: 'Hale_S1_PrePost_202301_overlap',
  folder: 'GEE_Cyclone_Exports',
  fileNamePrefix: 'Hale_S1_PrePost_202301_overlap',
  region: overlapRegion,
  scale: 10,
  crs: 'EPSG:2193',
  maxPixels: 1e13,
  fileFormat: 'GeoTIFF'
});
