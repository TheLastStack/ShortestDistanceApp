var white = false, black = false;
var marker_size;
var button_size;
function sizeAdjust() {
  const width  = window.innerWidth || document.documentElement.clientWidth || document.body.clientWidth;
  const height = window.innerHeight|| document.documentElement.clientHeight|| document.body.clientHeight;
  var largest_side;
  if (width < height) {
    largest_side = height;
  }
  else {
    largest_side = width;
  }
  marker_size = parseInt(Math.log2(largest_side/10));
  marker_size = 2 ** (marker_size > 8 ? 8 : marker_size - 1);
  button_size = marker_size * 3;
  document.getElementById('find').style.width=button_size.toString() + "px";
  document.getElementById('find').style.height=button_size.toString() + "px";
}
sizeAdjust();
window.addEventListener('resize', sizeAdjust);
var select = new ol.interaction.Select({
  style: selectStyle
});
var translate = new ol.interaction.Translate({
  features: select.getFeatures(),
});
var map = new ol.Map({
  interactions: ol.interaction.defaults().extend([select, translate]),
  target: 'map',
  layers: [
    new ol.layer.Tile({
      source: new ol.source.OSM()
    })
  ],
  view: new ol.View({
    center: ol.proj.fromLonLat([0, 0]),
    zoom: 4
  })
});
function selectStyle(feature, resolution)
{
  var color = feature.get("color");
  var style =  new ol.style.Style({
      image: new ol.style.Icon({
        anchor: [0.5, 1],
        anchorXUnits: "fraction",
        anchorYUnits: "fraction",
        src: "../static/" + color + "_"+ marker_size.toString() + ".png"
      })
  });
  return [style];
}
var vectorLayer = new ol.source.Vector({});
var white_marker = new ol.Feature({
  name: "White Marker",
  geometry: new ol.geom.Point(ol.proj.transform([0.0, 0.0], 'EPSG:4326', 'EPSG:3857')),
  color: "white"
});
var black_marker = new ol.Feature({
  name: "Black Marker",
  geometry: new ol.geom.Point(ol.proj.transform([15.0, 0.0], 'EPSG:4326', 'EPSG:3857')),
  color: "black"
});
vectorLayer.addFeature(white_marker);
vectorLayer.addFeature(black_marker);
map.addLayer(new ol.layer.Vector({
  source:vectorLayer,
  style: selectStyle
}));
function sendCoords() {
  const XHR = new XMLHttpRequest(),
        FD  = new FormData();
  FD.append("white_x", white_marker.getGeometry().getCoordinates()[0]);
  FD.append("white_y", white_marker.getGeometry().getCoordinates()[1]);
  FD.append("black_x", black_marker.getGeometry().getCoordinates()[0]);
  FD.append("black_y", black_marker.getGeometry().getCoordinates()[1]);
  XHR.open('POST', '/navigate');
  XHR.send(FD);
}
