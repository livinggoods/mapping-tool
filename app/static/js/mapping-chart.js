var plotData=[];
var colors = Highcharts.getOptions().colors;
var data = data = [];


var categories = [],
    browserData = [],
    versionsData = [],
    i,
    j,
    dataLen,
    drillDataLen,
    brightness;



$(document).ready(function(){
    $.ajax({
        'url': '/api/v1/get/mapping-details/'+mappingId,
        dataType:'json',
        type:'GET',
        success: function(apiData){
            var i = 0;
            $.each(apiData.mappings.parishes, function(index, parish){
              // create the apiData point
              categories.push(parish.name);
              var villages = [];
              var villageDrillData=[];
              var parishHouseHoldsCount=0;
              $.each(parish.village_data.villages, function(index, village){
                villages.push(village.village_name);
                parishHouseHoldsCount= parishHouseHoldsCount+village.noofhouseholds;
                villageDrillData.push(village.noofhouseholds);
              });
              data.push({
                y: parishHouseHoldsCount,
                color: colors[i],
                drilldown: {
                    name: parish.name+' villages',
                    categories: villages,
                    data: villageDrillData,
                    color: colors[i]
                }
              });

              i++;
            });
            processData();
        }
    });
});

function processData(){
    dataLen = data.length;
    // Build the data arrays
    for (i = 0; i < dataLen; i += 1) {
        // add browser data
        browserData.push({
            name: categories[i],
            y: data[i].y,
            color: data[i].color
        });

        // add version data
        drillDataLen = data[i].drilldown.data.length;
        for (j = 0; j < drillDataLen; j += 1) {
            brightness = 0.2 - (j / drillDataLen) / 5;
            versionsData.push({
                name: data[i].drilldown.categories[j],
                y: data[i].drilldown.data[j],
                color: Highcharts.Color(data[i].color).brighten(brightness).get()
            });
        }
    }
    createChart();
}


////

// Create the chart
function createChart() {
    //console.log(data);
    Highcharts.chart('map-chart', {
        chart: {
            type: 'pie'
        },
        title: {
            text: 'Village and Parish Summary '
        },
        credits:{href:"mailto:kimarudg@gmail.com", text:"David Kimaru"},
        subtitle: {
            text: mappingName
        },
        yAxis: {
            title: {
                text: 'Total Households'
            }
        },
        plotOptions: {
            pie: {
                shadow: false,
                center: ['50%', '50%']
            }
        },
        tooltip: {
            valueSuffix: ''
        },
        series: [{
            name: 'Villages ',
            data: browserData,
            size: '60%',
            dataLabels: {
                formatter: function () {
                    return this.y > 5 ? this.point.name : null;
                },
                color: '#ffffff',
                distance: -30
            }
        }, {
            name: 'Households',
            data: versionsData,
            size: '80%',
            innerSize: '60%',
            dataLabels: {
                formatter: function () {
                    // display only if larger than 1
                    return this.y > 1 ? '<b>' + this.point.name + ':</b> ' +
                        this.y : null;
                }
            },
            id: 'versions'
        }],
        responsive: {
            rules: [{
                condition: {
                    maxWidth: 400
                },
                chartOptions: {
                    series: [{
                        id: 'versions',
                        dataLabels: {
                            enabled: false
                        }
                    }]
                }
            }]
        }
    });
}