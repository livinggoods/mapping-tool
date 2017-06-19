// this loads the dashboaord data
//$(document).ready(function() {
var plotData=[];
$(document).ready(function(){
    // get data
    $.ajax({
        'url': '/api/v1/recruitments.json',
        dataType:'json',
        type:'GET',
        success: function(data){
            $.each(data.recruitments, function(index, rec){
              // create the data point
              var seriesData = [rec.client_time, rec.data.count];
              plotData.push(seriesData);
            });
            console.log(plotData);
            createChart();
        }
    });
});
var seriesOptions = [],
    seriesCounter = 0,
    names = ['MSFT', 'AAPL', 'GOOG'];

function createChart() {
    Highcharts.stockChart('placeholder33x', {
        chart: {
            height: 400,
        },
        rangeSelector: {
            selected: 1
        },


        title:{text: 'Recruitments to Date'},

        plotOptions: {
            series: {
                compare: 'percent',
                showInNavigator: true
            }
        },
        credits:{href:"mailto:dkimaru@livingggoods.org", text:"David Kimaru"},

        series: [{
            name:'Recruitments',
            data:plotData,
            tooltip:{valueDecimals:0}
        }]
    });
}