chartWidth = $('.panel-heading').width();
mapsObj = JSON.parse(maps);

$(document).ready(function() {
    $.each(mapsObj, function(index, element) {

        $.get('/edagraph/' + username + '/' + mapsObj[index].mapName, function(data) {
            coords = JSON.parse(data);
            for (var i = 0; i < coords.length; i++) {
                coords[i]['x'] = new Date(coords[i]['x']);
                coords[i]['y'] = parseFloat(coords[i]['y']);
            }
            $.get('/edapeakvalley/' + username + '/' + mapsObj[index].mapName, function(data) {
                
                peakValleyObj = JSON.parse(data);
                //convert all peak and valley strings to Date objects
                for(var i = 0; i < peakValleyObj['valleys'].length; i++) {
                    peakValleyObj['valleys'][i] = new Date(peakValleyObj['valleys'][i]);
                    peakValleyObj['peaks'][i] = new Date(peakValleyObj['peaks'][i]);
                }
                var peakIndex = 0;
                var valleyIndex = 0;

                for (var i = 0; i < coords.length; i++) {
                    if(valleyIndex < peakValleyObj['valleys'].length && coords[i]['x'].valueOf() == peakValleyObj['valleys'][valleyIndex].valueOf()) {
                        coords[i]['indexLabel'] = 'valley';
                        coords[i]['markerType'] = 'cross';
                        coords[i]['markerColor'] = '#FF0000';
                        coords[i]['markerSize'] = 12;
                        valleyIndex++;
                        console.log('valley added!');
                    }
                    else if(peakIndex < peakValleyObj['peaks'].length && coords[i]['x'].valueOf() == peakValleyObj['peaks'][peakIndex].valueOf()) {
                        coords[i]['indexLabel'] = 'peak';
                        coords[i]['markerType'] = 'triangle';
                        coords[i]['markerColor'] = '#0000FF';
                        coords[i]['markerSize'] = 12;
                        peakIndex++;
                        console.log('peak added!');
                    }
                }
                console.log(coords);
                $("#chartContainer-" + mapsObj[index].mapName).CanvasJSChart(
                {
                    zoomEnabled: true,
                    title:{
                        text: "Electrodermal Activity",
                    },
                    animationEnabled: true,
                    height: 300,
                    width: chartWidth,
                    axisX: {
                        title: "time"
                    },
                    axisY:{
                        includeZero: false,
                        title: "EDA (u_S)"
                    },
                    data: [
                    {
                        type: "line",

                        dataPoints: coords
                    }
                    ]
                });
            });
            
        });/*
        */
        //console.log(coords);
        
        
    });
});
