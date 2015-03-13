var map;
var geojson;
var currFeatureID = -1;

function initMap() {
    // set up the map
    //convert the passed in file into a json object to add to the map, loading the file directly won't work with zoom for some reason
    $.getJSON(geojson_file, function(response) { 
        geojson = response;
    
        map = new google.maps.Map(document.getElementById('map-canvas'), {
            center: new google.maps.LatLng(0, 0),
            zoom: 2
        });
        map.data.addGeoJson(geojson);

        map.data.setStyle(function(feature) {
            return {
                icon: {
                    scaledSize: new google.maps.Size(75, 75),
                    url: '/images/' + feature.getProperty('image')
                },
                strokeColor: '#0066FF',
                strokeWeight: 10
            };
        });

        zoom(map);

        map.data.addListener('mouseover', function(event) {
            map.data.revertStyle();
            map.data.overrideStyle(event.feature, {
                icon: {scaledSize: new google.maps.Size(150, 150), url: '/images/' + event.feature.getProperty('image')} 
            });
        });

        map.data.addListener('mouseout', function(event) {
            map.data.revertStyle();
        });

        map.data.addListener('click', function(event) {
            displayModal(event.feature);
        });
    });
}

function displayModal(feature) {
    $('#image-modal').modal('show');
    $('#image-modal').find('.modal-title').text(feature.getProperty('image'));
    $('#image-modal').find('#clickedImage').attr('src', '/images/' + feature.getProperty('image'));

    $('#image-modal').find('#dateTime').text("Date and time: " + feature.getProperty('timestamp'));
    $('#image-modal').find('#GPS').text("GPS Coordinates: " + feature.getProperty('gps')[0] + ', ' + feature.getProperty('gps')[1]);
    $('#image-modal').find('#EDA').text("EDA Peaks per Second: " + feature.getProperty('peaksPerSecond'));
    currFeatureID = feature.getId();

    if(map.data.getFeatureById(currFeatureID+1) == undefined) {
        $('#image-modal').find('#nextImageBtn').addClass('disabled');
    } else {
        $('#image-modal').find('#nextImageBtn').removeClass('disabled');
    }
    if(map.data.getFeatureById(currFeatureID-1) == undefined) {
        $('#image-modal').find('#prevImageBtn').addClass('disabled');
    } else {
        $('#image-modal').find('#prevImageBtn').removeClass('disabled');
    }
}
/**
 * Update a map's viewport to fit each geometry in a dataset
 * @param {google.maps.Map} map The map to adjust
 */
function zoom(map) {
    var bounds = new google.maps.LatLngBounds();
    map.data.forEach(function(feature) {
        processPoints(feature.getGeometry(), bounds.extend, bounds);
    });
    map.fitBounds(bounds);
}

/**
 * Process each point in a Geometry, regardless of how deep the points may lie.
 * @param {google.maps.Data.Geometry} geometry The structure to process
 * @param {function(google.maps.LatLng)} callback A function to call on each
 *     LatLng point encountered (e.g. Array.push)
 * @param {Object} thisArg The value of 'this' as provided to 'callback' (e.g.
 *     myArray)
 */
function processPoints(geometry, callback, thisArg) {
    if (geometry instanceof google.maps.LatLng) {
        callback.call(thisArg, geometry);
    } else if (geometry instanceof google.maps.Data.Point) {
        callback.call(thisArg, geometry.get());
    } else {
        geometry.getArray().forEach(function(g) {
            processPoints(g, callback, thisArg);
        });
    }
}

$(document).ready(function() {
    google.maps.event.addDomListener(window, 'load', initMap);
    $('#nextImageBtn').click(function() {
        currFeatureID++;
        displayModal(map.data.getFeatureById(currFeatureID));
    });
    $('#prevImageBtn').click(function() {
        currFeatureID--;
        displayModal(map.data.getFeatureById(currFeatureID));
    });
    
});


