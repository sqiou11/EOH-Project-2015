var poly;
var map;

function initialize() {
  var mapOptions = {
    zoom: 7,
    // Center the map on Chicago, USA.
    center: new google.maps.LatLng(41.879535, -87.624333)
  };

  map = new google.maps.Map(document.getElementById('map-canvas'), mapOptions);

  var polyOptions = {
    strokeColor: '#0066FF',
    strokeOpacity: 1.0,
    strokeWeight: 5
  };
  poly = new google.maps.Polyline(polyOptions);
  poly.setMap(map);

  // Add a listener for the click event
  google.maps.event.addListener(map, 'click', addLatLng);
}

/**
 * Handles click events on a map, and adds a new point to the Polyline.
 * @param {google.maps.MouseEvent} event
 */
function addLatLng(event) {

  var path = poly.getPath();

  // Because path is an MVCArray, we can simply append a new coordinate
  // and it will automatically appear.
  path.push(event.latLng);

  // Add a new marker at the new plotted point on the polyline.
  /*var marker = new google.maps.Marker({
    position: event.latLng,
    title: '#' + path.getLength(),
    map: map
  });*/
}

$(document).ready(function() {
  google.maps.event.addDomListener(window, 'load', initialize);
});


