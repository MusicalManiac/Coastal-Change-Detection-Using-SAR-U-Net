// Cyclone Idai Sentinel-1 pre/post export for Google Earth Engine.
//
// Candidate closest event-relevant pair:
//   pre-event:  14 March 2019
//   post-event: 19 March 2019
//
// This is a separate experiment. It does not replace the project's
// 18 February 2019 / 20 March 2019 baseline export.

var beira = ee.Geometry.Rectangle([
  34.65, -19.95,
  35.10, -19.65
]);

var preImage = ee.Image(
  'COPERNICUS/S1_GRD/S1B_IW_GRDH_1SDV_20190314T160646_20190314T160711_015352_01CBEE_21E5'
);
var postImage = ee.Image(
  'COPERNICUS/S1_GRD/S1B_IW_GRDH_1SDV_20190319T161451_20190319T161520_015425_01CE3C_A401'
);

print('Pre-event image', preImage);
print('Pre-event date', ee.Date(preImage.get('system:time_start')));
print('Pre-event relative orbit', preImage.get('relativeOrbitNumber_start'));
print('Pre-event pass', preImage.get('orbitProperties_pass'));
print('Pre-event polarizations', preImage.get('transmitterReceiverPolarisation'));

print('Post-event image', postImage);
print('Post-event date', ee.Date(postImage.get('system:time_start')));
print('Post-event relative orbit', postImage.get('relativeOrbitNumber_start'));
print('Post-event pass', postImage.get('orbitProperties_pass'));
print('Post-event polarizations', postImage.get('transmitterReceiverPolarisation'));

var timeDifferenceHours = ee.Date(postImage.get('system:time_start'))
  .difference(ee.Date(preImage.get('system:time_start')), 'hour');
print('Pre/post time difference (hours)', timeDifferenceHours);

var preEvent = ee.Image.cat([
  preImage.select('VV').rename('pre_vv'),
  preImage.select('VH').rename('pre_vh')
]);
var postEvent = ee.Image.cat([
  postImage.select('VV').rename('post_vv'),
  postImage.select('VH').rename('post_vh')
]);

var rawStack = preEvent.addBands(postEvent);
var smoothedStack = rawStack
  .focal_mean({
    radius: 30,
    kernelType: 'circle',
    units: 'meters'
  })
  .rename(['pre_vv', 'pre_vh', 'post_vv', 'post_vh']);

// Sentinel-1 granule geometries can have a narrow geodesic gap even when
// the raster footprints have useful common coverage. Buffer before
// intersecting, then constrain the export to Beira.
var footprintBuffer = 10000;
var preBuffered = preImage.geometry().buffer(footprintBuffer, 100);
var postBuffered = postImage.geometry().buffer(footprintBuffer, 100);
var overlapRegion = preBuffered
  .intersection(postBuffered, 100)
  .intersection(beira, 100);

var overlapArea = overlapRegion.area(100);
print('Footprint buffer (m)', footprintBuffer);
print('Overlap export area (m2)', overlapArea);
print('Export region is valid', ee.Number(overlapArea).gt(0));

// Display the candidate scenes and export region before starting the task.
Map.centerObject(overlapRegion, 9);
Map.addLayer(
  preImage.select('VV'),
  {min: -25, max: 0},
  'Pre-event VV (14 March 2019)'
);
Map.addLayer(
  postImage.select('VV'),
  {min: -25, max: 0},
  'Post-event VV (19 March 2019)'
);
Map.addLayer(
  overlapRegion,
  {color: 'yellow'},
  'Sentinel-1 overlap export region'
);

Export.image.toDrive({
  image: smoothedStack,
  description: 'Idai_S1_PrePost_20190314_20190319_overlap',
  folder: 'GEE_Cyclone_Exports',
  fileNamePrefix: 'Idai_S1_PrePost_20190314_20190319_overlap',
  region: overlapRegion,
  scale: 10,
  crs: 'EPSG:3857',
  maxPixels: 1e13,
  fileFormat: 'GeoTIFF'
});
