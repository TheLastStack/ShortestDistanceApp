var marker_size, button_size;
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
  marker_size = Math.pow(2, (marker_size > 8 ? 8 : marker_size - 1));
  button_size = marker_size * 3;
  document.getElementById('find').style.width=button_size.toString() + "px";
  document.getElementById('find').style.height=button_size.toString() + "px";
}
sizeAdjust();
window.addEventListener('resize', sizeAdjust);
var map = new ol.Map({
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
var pre_vectorLayer = new ol.source.Vector({});
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
pre_vectorLayer.addFeature(white_marker);
pre_vectorLayer.addFeature(black_marker);
vectorLayer = new ol.layer.Vector({
  name:"Marker_layer",
  source: pre_vectorLayer,
  style: selectStyle
});
map.addLayer(vectorLayer);
var select = new ol.interaction.Select({
  style: selectStyle,
  layers:[vectorLayer]
});
var translate = new ol.interaction.Translate({
  features: select.getFeatures(),
});
map.addInteraction(select);
map.addInteraction(translate);
function drawCoords(status, response) {
  if(status == 4)
  {
    const Parser = new DOMParser();
    const xmlDoc = Parser.parseFromString(response, "application/xml");
    map.getLayers().forEach(layer => {
    if (layer.get('name') && layer.get('name') == 'route_layer'){
        map.removeLayer(layer);
      }
    });
    var nodes = xmlDoc.getElementsByTagName("node");
    var route_trace = new ol.geom.LineString([]);
    for(var i = 0; i < nodes.length; i++)
    {
      route_trace.appendCoordinate([parseFloat(nodes[i].getElementsByTagName("x")[0].textContent), parseFloat(nodes[i].getElementsByTagName("y")[0].textContent)]);
    }
    route_trace.transform('EPSG:4326', 'EPSG:3857');
    var pre_lineLayer = new ol.source.Vector({});
    pre_lineLayer.addFeature(
      new ol.Feature({
        geometry: route_trace,
        name: "Line_trace"
      })
    );
    var vectortracer = new ol.layer.Vector({
      source: pre_lineLayer,
      name: "route_layer",
      style: new ol.style.Style({
        stroke : new ol.style.Stroke({
         color: '#0000ff',
         width: 5
       })
     })
    });
    vectortracer.setZIndex(0);
    map.addLayer(vectortracer);
    map.getLayers().forEach(layer => {
    if (layer.get('name') && layer.get('name') == 'Marker_layer'){
        layer.setZIndex(1);
      }
    });
  }
}
function sendCoords() {
  var XHR = new XMLHttpRequest(),
        FD  = new FormData();
  XHR.onreadystatechange = function () {
    drawCoords(XHR.readyState, XHR.responseText);
  };
  FD.append("white_x", ol.proj.transform(white_marker.getGeometry().getCoordinates(), 'EPSG:3857', 'EPSG:4326')[0]);
  FD.append("white_y", ol.proj.transform(white_marker.getGeometry().getCoordinates(), 'EPSG:3857', 'EPSG:4326')[1]);
  FD.append("black_x", ol.proj.transform(black_marker.getGeometry().getCoordinates(), 'EPSG:3857', 'EPSG:4326')[0]);
  FD.append("black_y", ol.proj.transform(black_marker.getGeometry().getCoordinates(), 'EPSG:3857', 'EPSG:4326')[1]);
  XHR.open('POST', '/navigate');
  XHR.send(FD);
}
