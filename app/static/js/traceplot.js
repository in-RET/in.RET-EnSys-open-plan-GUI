const config = {
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
const layout = {
    height: 220,
    margin: {
        b: 45,
        l: 60,
        r: 60,
        t: 15,
    },
    xaxis: {
        type: "date"
    }
};

var kindOfComponentSource = '';
var kindOfComponentTrafo = '';
var kindOfComponentStorage = '';


// handling expert trafo
function get_trafo_variation(value) {
	alert(value);
	render_form_expert_trafo(value);
}

function render_form_expert_trafo(value) {
    //alert('Called');
    var server_data = [
        { "trafo_input_output_variation": value }
    ];

    $.ajax({
        type: "POST",
        url: "/en/asset/adjust_form_expert_trafo/",
        data: JSON.stringify(server_data),
        contentType: "application/json",
        dataType: 'json',
        success: function (response) {
            Swal.fire('', "Got response from server ...", 'info');
            //alert(response['form_html']);
            $('#act_form_div').html(response['form_html']);
        }
    });
}

// handling predefined sources
function loadPredefindedDataKindofSource(value) {
    kindOfComponentSource = value;
    if (kindOfComponentSource != '' && choosenYear != '') {
        fill_out_form_source();
    }
}


// handling predefined transformers
function loadPredefindedDataKindofTrafo(value) {
    kindOfComponentTrafo = value;
    if (kindOfComponentTrafo != '' && choosenYear != '') {
        fill_out_form_trafo();
    }
}


// handling predefined storages
function loadPredefindedDataKindofStorage(value) {
    kindOfComponentStorage = value;
    if (kindOfComponentStorage != '' && choosenYear != '') {
        fill_out_form_storage();
    }
}


$.ajaxSetup({
    beforeSend: function (xhr, settings) {
        function getCookie(name) {
            var cookieValue = null;
            if (document.cookie && document.cookie != '') {
                var cookies = document.cookie.split(';');
                for (var i = 0; i < cookies.length; i++) {
                    var cookie = jQuery.trim(cookies[i]);
                    // Does this cookie string begin with the name we want?
                    if (cookie.substring(0, name.length + 1) == (name + '=')) {
                        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                        break;
                    }
                }
            }
            return cookieValue;
        }
        if (!(/^http:.*/.test(settings.url) || /^https:.*/.test(settings.url))) {
            // Only send the token to relative URLs i.e. locally.
            xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
        }
    }
});


function fill_out_form_source() {
    //alert('Called');
    var server_data = [
        { "kindOfComponentSource": kindOfComponentSource },
        { "choosenTimestampSource": choosenYear },
    ];

    $.ajax({
        type: "POST",
        url: "/en/asset/get_param_suggestion_source/",
        data: JSON.stringify(server_data),
        contentType: "application/json",
        dataType: 'json',
        success: function (response) {
            Swal.fire('', "Got response from server ...", 'info');
            //alert(response['form_html']);
            $('#act_form_div').html(response['form_html']);
        }
    });
}

function fill_out_form_trafo() {
    //alert('Called');
    var server_data = [
        { "kindOfComponentTrafo": kindOfComponentTrafo },
        { "choosenTimestampTrafo": choosenYear },
    ];

    $.ajax({
        type: "POST",
        url: "/en/asset/get_param_suggestion_trafo/",
        data: JSON.stringify(server_data),
        contentType: "application/json",
        dataType: 'json',
        success: function (response) {
            Swal.fire('', "Got response from server ...", 'info');
            //alert(response['form_html']);
            $('#act_form_div').html(response['form_html']);
        }
    });
}

function fill_out_form_storage() {
    //alert('Called');
    var server_data = [
        { "kindOfComponentStorage": kindOfComponentStorage },
        { "choosenTimestampStorage": choosenYear },
    ];

    $.ajax({
        type: "POST",
        url: "/en/asset/get_param_suggestion_storage/",
        data: JSON.stringify(server_data),
        contentType: "application/json",
        dataType: 'json',
        success: function (response) {
            Swal.fire('', "Got response from server ...", 'info');
            //alert(response['form_html']);
            $('#act_form_div').html(response['form_html']);
        }
    });
}

function makePlotlyLoadProfile(value) {
    var data;
    var trace1 = {
        x: [...Array(8760).keys()],
        y: Array(8760).fill(5),
        type: 'scatter'
    };

    var trace2 = {
        x: [...Array(8760).keys()],
        y: Array(8760).fill(6),
        type: 'scatter'
    };

    var trace3 = {
        x: [...Array(8760).keys()],
        y: Array(8760).fill(7),
        type: 'scatter'
    };

    if (value == "load_profile_1") {
        data = [trace1];
    }
    else if (value == "load_profile_2") {
        data = [trace2];
    }
    else if (value == "load_profile_3") {
        data = [trace3];
    }

    Plotly.newPlot('load_profile_trace', data);

}

function makePlotly(x, y, plot_id = "", userLayout = null) {

    // get the handle of the plotly plot
    if (plot_id == "") {
        plot_id = PLOT_ID;
    }
    var plotDiv = document.getElementById(plot_id);

    // if the timestamps from the scenario are available, loads them
    var ts_timestamps_div = document.getElementById("input_timeseries_timestamps");
    console.log(ts_timestamps_div);


    if (ts_timestamps_div) {
        var ts_timestamps = JSON.parse(ts_timestamps_div.querySelector("textarea").value);
       
        //console.log(ts_timestamps);
        // only replace the x values with timestamps if they match the y values, otherwise the error
        // will be confusing to the enduser
        if (ts_timestamps.length == y.length) {
            x = ts_timestamps;
        }
        else if (y.length == 0) {
            Swal.fire({
                title: "You have not uploaded a time series for this component! But you don't have to.",
                icon: "info",
                toast: true,
                //position: 'bottom-end',
                timer: 1200,
                showCancelButton: false,
                showConfirmButton: true,
            })
        } else {
            Swal.fire({
                title: "The number of values in your uploaded timeseries (" + y.length + ") does not match the scenario timestamps (" + ts_timestamps.length + ").\nPlease change the scenario settings or upload a new timeseries",
                icon: "info",
                toast: true,
                //position: 'bottom-end',
                timer: 1200,
                showCancelButton: false,
                showConfirmButton: true,
        })};
    }

    var plotLayout = { ...layout };
    // guess whether x is a number or a date and adjust the axis type accordingly
    if (isNaN(x[0]) == false) {
        plotLayout.xaxis.type = "linear";
    }
    else {
        plotLayout.xaxis.type = "date";
    }
    plotLayout.xaxis.autorange = "true";
    plotLayout["yaxis"] = { autorange: "true" };
    plotLayout = { ...plotLayout, ...userLayout };
    var traces = [{ type: "scatter", x: x, y: y }];

    Plotly.newPlot(plotDiv, traces, plotLayout, config);
    // simulate a click on autoscale
    plotDiv.querySelector('[data-title="Autoscale"]').click();


    var PLOT_ID = "";
};

/* Plot update of textinput field of DualInput field */
function plotDualInputTrace(obj, param_name = "") {

    // TODO get the timeseries timestamps (if exists) from a hidden safejs div with the django tag method
    jsObj = JSON.parse(obj);

    // this refers to div id in the html template asset/dual_input.html
    PLOT_ID = param_name + "_trace";

    var graphDOM = document.getElementById(PLOT_ID);
    if (Array.isArray(jsObj)) {
        myarray = []
        jsObj.forEach(el => myarray.push([el]))



        processData(myarray);
        graphDOM.style.display = "block";
    }
    else {
        graphDOM.style.display = "none";
        // reset file in memory if the user inputs a scalar after uploading a file
        var fileID = "id_" + param_name + "_1";
        var file_input = document.getElementById(fileID);
        file_input.value = "";
    };

}


function uploadDualInputTrace(obj, param_name = "") {

    // Check for the various File API support.
    if (window.FileReader) {
        var array = [];
        var flist = obj;

        var myfile = flist[0];
        if (myfile) {
            if (myfile.name.includes(".csv") || myfile.name.includes(".txt")) {
                Promise.resolve(getAsText(myfile, plot = false)).then(async (array) => { updateScalarInput(array); });
            }
            else if (myfile.name.includes(".xls")) {
                Promise.resolve(getAsExcel(myfile, plot = false)).then(async (array) => { updateScalarInput(array); });
            }
        }
        function updateScalarInput(array) {
            // write the array as json inside the scalar input field and trigger the change event
            var scalarID = "id_" + param_name + "_0";
            var scalar_input = document.getElementById(scalarID);
            scalar_input.value = JSON.stringify(array.map(el => Number(el[0])));
            scalar_input.dispatchEvent(new Event("change"));
        }

    } else {
        alert('FileReader are not supported in this browser.');
    }


}

function plot_file_trace(obj, plot_id = "") {
    // Check for the various File API support.
    if (window.FileReader) {
        PLOT_ID = plot_id;

        var trace_plots = document.getElementById(plot_id);

        var flist = obj;

        var myfile = flist[0];
        if (myfile) {
            if (myfile.name.includes(".csv")) { getAsText(myfile); }
            else if (myfile.name.includes(".txt")) { getAsText(myfile); }
            else if (myfile.name.includes(".xls")) { getAsExcel(myfile); }
        }

    } else {
        alert('FileReader are not supported in this browser.');
    }
}
function getAsExcel(fileToRead, plot = true) {
    var reader = new FileReader();

    if (plot == false) {
        // return a Promise of the file parsed as a d3 csv array
        return new Promise((resolve, reject) => {
            reader.onloadend = () => {
                resolve(parseExcelData(reader.result));
            };
            // Read file into memory as UTF-8
            reader.readAsBinaryString(fileToRead);
        });
    }
    else {
        reader.onload = function (e) {
            processData(parseExcelData(e.target.result));
        };
        reader.readAsBinaryString(fileToRead);
    }

    reader.onerror = function (ex) {
        console.log(ex);
    };



};

/* given the output of FileReader.result parse the data */
function parseExcelData(data) {
    var wb = XLSX.read(data, {
        type: 'binary'
    });
    var ws = wb.Sheets[wb.SheetNames[0]];
    const nsheets = wb.SheetNames.length;
    if (nsheets > 1) {
        alert("Your file has more than one sheet, only the sheet " + wb.SheetNames[0] + " will be parsed.");
    }
    var XL_row_object = XLSX.utils.sheet_to_row_object_array(ws);
    // TODO support column names (now it is ignored, info is in Object.keys)

    return XL_row_object.map(row => Object.values(row))
}



// taken from https://github.com/MounirMesselmeni/html-fileapi
function getAsText(fileToRead, plot = true) {
    var reader = new FileReader();

    // Handle errors load
    reader.onerror = errorHandler;

    if (plot == false) {
        // return a Promise of the file parsed as a d3 csv array
        return new Promise((resolve, reject) => {
            reader.onloadend = () => {
                resolve(d3.csvParseRows(reader.result));
            };
            // Read file into memory as UTF-8
            reader.readAsText(fileToRead);
        });
    }
    else {

        reader.onload = loadHandler;
        // Read file into memory as UTF-8
        reader.readAsText(fileToRead);
    }


    function loadHandler(event) {
        var csv = event.target.result;
        d3array = d3.csvParseRows(csv);
        processData(d3array);
    }


    function errorHandler(evt) {
        if (evt.target.error.name == "NotReadableError") {
            alert("Cannot read file !");
        }
    }
}


function processData(array_2D) {
    const ncols = array_2D[0].length;
    var dateFormat = d3.timeParse("%Y-%m-%d %H:%M:%S")
    var x = [], y = [];
    // there are only the timeseries values
    if (ncols == 1) {
        for (var i = 0; i < array_2D.length; i++) {
            var line = array_2D[i];
            x.push(String(i));
            y.push(line[0]);
        }
    }
    // it is assumed here that first column is timestamp and second column is timeseries values
    else if (ncols == 2) {
        for (var i = 0; i < array_2D.length; i++) {
            var line = array_2D[i];
            x.push(line[0]);
            y.push(line[1]);
        }
    }
    else {
        alert("File has more than 2 columns.\nIt is expected one column: the timeseries values\nOr two columns: the first one with timestamps and the second one with the timeseries values");
    }
    // provide x and y to plotly maker
    makePlotly(x, y);
}
