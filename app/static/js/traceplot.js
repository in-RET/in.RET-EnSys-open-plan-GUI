var config = {
    showLink: false,
    responsive: true,
    scrollZoom: true,
    modeBarButtonsToRemove: [
        'select2d',
        'lasso2d',
        'toImage',
        'lassoSelect',
        'boxSelect',
        'hoverClosestCartesian',
        'hoverCompareCartesian',
        'toggleSpikelines']
}; //displayModeBar: true
var layout = {
    height: 140,
    margin:{
        b:30,
        l:20,
        r:0,
        t:10,
    }
};


function makePlotly( x, y ){
    console.log("plot ID", PLOT_ID);
    console.log( 'X',x, 'Y',y );
  var plotDiv = document.getElementById(PLOT_ID);

  var traces = [{
    x: x,
    y: y
  }];

  Plotly.newPlot(plotDiv, traces, layout, config);
};


var PLOT_ID = "";



function plot_file_trace(obj, plot_id="") {
    // Check for the various File API support.
    if (window.FileReader) {
        PLOT_ID = plot_id;

        var trace_plots = document.getElementById(plot_id);

        var flist = obj;

        var myfile = flist[0];
        if (myfile) {
        if(myfile.name.includes(".csv")){getAsText(myfile);}
          else if (myfile.name.includes(".xls")){
          alert("xls files not yet supported for quick vizualisation (but the data will be saved into the database)")
          }
        }

    } else {
      alert('FileReader are not supported in this browser.');
    }
}

// taken from https://github.com/MounirMesselmeni/html-fileapi
 function getAsText(fileToRead) {
      var reader = new FileReader();
      // Read file into memory as UTF-8
      reader.readAsText(fileToRead);
      // Handle errors load
      reader.onload = loadHandler;
      reader.onerror = errorHandler;
    }

    function loadHandler(event) {
      var csv = event.target.result;
      d3array = d3.csvParseRows(csv);
      processData(d3array);
    }

    function processData(array_2D) {
        const ncols = d3array[0].length;
        var dateFormat = d3.timeParse("%Y-%m-%d %H:%M:%S")
        var x = [], y = [];
        // there are only the timeseries values
        if (ncols == 1){
            for (var i=0; i<array_2D.length; i++) {
                var line = array_2D[i];
                    x.push(String(i));
                    y.push(line[0]);
                    }
        }
        // it is assumed here that first column is timestamp and second column is timeseries values
        else if (ncols == 2){
            for (var i=0; i<array_2D.length; i++) {
                var line = array_2D[i];
                    x.push(line[0]);
                    y.push(line[1]);
                    }
        }
        else{
            alert("File has more than 3 columns!!!");
        }
        // provide x and y to plotly maker
        makePlotly(x,y);
    }

    function errorHandler(evt) {
      if(evt.target.error.name == "NotReadableError") {
          alert("Canno't read file !");
      }
    }
