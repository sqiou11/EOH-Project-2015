var poly;
var map;

function initialize() {
  var mapOptions = {
    zoom: 10,
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

  // Try HTML5 geolocation
  if(navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(function(position) {
      var pos = new google.maps.LatLng(position.coords.latitude,
                                       position.coords.longitude);

      var infowindow = new google.maps.InfoWindow({
        map: map,
        position: pos,
        content: 'Location found using HTML5.'
      });

      map.setCenter(pos);
    }, function() {
      handleNoGeolocation(true);
    });
  } else {
    // Browser doesn't support Geolocation
    handleNoGeolocation(false);
  }

  // Add a listener for the click event
  google.maps.event.addListener(map, 'click', addLatLng);
}

function handleNoGeolocation(errorFlag) {
  if (errorFlag) {
    var content = 'Error: The Geolocation service failed.';
  } else {
    var content = 'Error: Your browser doesn\'t support geolocation.';
  }

  var options = {
    map: map,
    position: new google.maps.LatLng(60, 105),
    content: content
  };

  var infowindow = new google.maps.InfoWindow(options);
  map.setCenter(options.position);
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


