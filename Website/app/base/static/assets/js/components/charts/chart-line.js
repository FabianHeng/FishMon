'use strict';

//
// Sales chart
//

var TempChart = (function() {

  // Variables

    var $chart = $('#chart-temperature');


  // Methods

  function init($chart) {

    var tempChart = new Chart($chart, {
      type: 'line',
      options: {
          responsive: true,
          maintain-aspect-ratio: false,
        scales: {
          yAxes: [{
            gridLines: {
              lineWidth: 1,
              color: Charts.colors.gray[900],
              zeroLineColor: Charts.colors.gray[900]
            },
            ticks: {
              callback: function(value) {
                if (!(value % 5)) {
                  return value + '* C';
                }
              }
            }
          }]
        },
        tooltips: {
          callbacks: {
            label: function(item, data) {
              var label = data.datasets[item.datasetIndex].label || '';
              var yLabel = item.yLabel;
              var content = '';

              if (data.datasets.length > 1) {
                content += '<span class="popover-body-label mr-auto">' + label + '</span>';
              }

              content += '<span class="popover-body-value">$' + yLabel + 'k</span>';
              return content;
            }
          }
        }
      },
      data: {
        labels: [0, 5, 10, 15, 20, 25, 30, 35, 40],
        datasets: [{
          label: 'Temperature (*C)',
          data: []
        }]
      }
    });

    // Save to jQuery object

      $chart.data('chart', tempChart);

  };


  // Events

  if ($chart.length) {
    init($chart);
  }

})();
