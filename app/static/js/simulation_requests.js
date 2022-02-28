
const myInterval = setInterval(check_if_simulation_is_done, 3000);

function check_if_simulation_is_done(url=checkSimulationUrl){

     $.ajax({
        type: "GET",
        url: url,
        success: function (resp) {
            console.log(resp);
            if(resp.areResultReady == true){
                clearInterval(myInterval);
                location.reload();
            }
        },
        error: function (XMLHttpRequest, textStatus, errorThrown) {
            clearInterval(myInterval);
        }
     });
};
