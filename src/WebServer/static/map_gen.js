var marker_size, button_size;
var saved_layers = [];
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
  button_size = Math.round(marker_size * 2.5);
  keeping_size = button_size / 2;
  document.getElementById('find').style.width=button_size.toString() + "px";
  document.getElementById('find').style.height=button_size.toString() + "px";
  const ids = ['plus', 'minus'];
  for (var i = 0; i < ids.length; i++)
  {
    document.getElementById(ids[i]).style.width=keeping_size.toString() + "px";
    document.getElementById(ids[i]).style.height=keeping_size.toString() + "px";
    document.getElementById(ids[i]).style.bottom=Math.round(1.1 * button_size).toString() + "px";
    document.getElementById(ids[i]).style['font-size']=Math.round(0.8 * keeping_size).toString() + "px";
  }
  document.getElementById('minus').style.right=Math.round(1.5 * keeping_size).toString() + "px";
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
    var layer_length = 0;
    map.getLayers().forEach(layer => {
      if (layer.get('name') && layer.get('name') == 'route_layer') {
          map.removeLayer(layer);
        }
      layer_length++;
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
    map.addLayer(vectortracer);
    vectortracer.setZIndex(layer_length);
    map.getLayers().forEach(layer => {
    if (layer.get('name') && layer.get('name') == 'Marker_layer'){
        layer.setZIndex(layer_length + 1);
      }
    });
  }
}
function addRoute() {
  map.getLayers().forEach(layer => {
  if (layer.get('name') && layer.get('name') == 'route_layer') {
      var copy, copy2, new_vectorLayer;
      if (saved_layers.length == 0)
      {
        saved_layers.push('route_layer$0');
        copy = layer.getSource();
        copy2 = layer.getStyle();
        new_vectorLayer = new ol.layer.Vector({
          source: copy,
          name: 'route_layer$0',
          style: copy2
        });
        const zindex = layer.getZIndex();
        map.removeLayer(layer);
        map.addLayer(new_vectorLayer);
        new_vectorLayer.setZIndex(zindex);
      }
      else
      {
        const idx = parseInt(saved_layers[saved_layers.length - 1].substring(saved_layers[0].indexOf('$') + 1)) + 1;
        saved_layers.push('route_layer$' + idx.toString());
        copy = layer.getSource();
        copy2 = layer.getStyle();
        new_vectorLayer = new ol.layer.Vector({
          source: copy,
          name: 'route_layer$' + idx.toString(),
          style: copy2
        });
        const zindex = layer.getZIndex();
        map.removeLayer(layer);
        map.addLayer(new_vectorLayer);
        new_vectorLayer.setZIndex(zindex);
      }
    }
  });
}
function removeRoute() {
  if (saved_layers.length != 0) {
    var pulled = 0;
    map.getLayers().forEach(layer => {
    if (layer.get('name') && layer.get('name') == 'route_layer') {
        map.removeLayer(layer);
        pulled = 1;
      }
    });
    if (pulled == 0) {
      const elementToRemove = saved_layers.pop();
      map.getLayers().forEach(layer => {
      if (layer.get('name') && layer.get('name') == elementToRemove) {
          map.removeLayer(layer);
        }
      });

    }
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
